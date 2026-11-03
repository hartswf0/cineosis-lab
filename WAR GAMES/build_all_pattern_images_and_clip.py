#!/usr/bin/env python3
"""
Generates real pixel-level Spatiotemporal Pattern Images for ALL 173 WarGames clips
(105 Master Scene Beats + 68 Pure WOPR Computer Screens) directly from the .mp4 files,
fixes all 8-frame strips so 100% match the playing .mp4 videos, and runs LAION CLIP ViT-B/32
embeddings across the rendered images to classify and cluster shots by Geometry, Color, and Motion.

Rendered image directories (all 16:9, 384x216):
  - lab/patterns/burn/<id>.jpg  : Pixel Motion & Phosphor Burn-In Heatmap (Afterlight M2)
  - lab/patterns/stone/<id>.jpg : Oxblood & Gold Two-Block Temporal Registration (Afterlight 03)
  - lab/patterns/slit/<id>.jpg  : True X-T Slit-Scan Tomography + Optical Flow Field
  - lab/patterns/dew/<id>.jpg   : Chronophotographic Dew Trail + Color Palette + Rabatment Grid
"""
import concurrent.futures
import json
import math
import os
import sys
import time
import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAB = os.path.join(ROOT, "lab")

for sub in ["burn", "stone", "slit", "dew"]:
    os.makedirs(os.path.join(LAB, "patterns", sub), exist_ok=True)

sys.path.insert(0, HERE)
from parse_watch_wargames import load_laion_clip

# Load OpenCV Haar cascades as an auxiliary signal alongside dense optical flow
CASCADE_DIR = cv2.data.haarcascades
FACE_FRONT = cv2.CascadeClassifier(os.path.join(CASCADE_DIR, "haarcascade_frontalface_default.xml"))
FACE_ALT = cv2.CascadeClassifier(os.path.join(CASCADE_DIR, "haarcascade_frontalface_alt2.xml"))
FACE_PROF = cv2.CascadeClassifier(os.path.join(CASCADE_DIR, "haarcascade_profileface.xml"))


def decode_video_frames(mp4_path, target_n=24, W=384, H=216):
    """Decode up to target_n evenly-spaced RGB frames (384x216, strict 16:9) from an .mp4 clip."""
    cap = cv2.VideoCapture(mp4_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    dur = total / fps if total > 0 else 0.0
    if total <= 0:
        cap.release()
        return [], 0.0

    indices = np.linspace(0, max(0, total - 1), target_n).astype(int)
    frames_bgr = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, fr = cap.read()
        if ret and fr is not None:
            fr_16_9 = cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)
            frames_bgr.append(fr_16_9)
    cap.release()
    while len(frames_bgr) < target_n and len(frames_bgr) > 0:
        frames_bgr.append(frames_bgr[-1].copy())
    return frames_bgr, round(dur, 2)


def extract_dominant_colors_bgr(frames_bgr, k=5):
    """Extract 5 dominant colors (hex + RGB) and overall color metrics from the clip."""
    sample = np.concatenate([f[::4, ::4].reshape(-1, 3) for f in frames_bgr[::3]], axis=0).astype(np.float32)
    # Filter out pure black pixels if possible
    non_black = sample[sample.sum(axis=1) > 35]
    if len(non_black) > 100:
        sample = non_black
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
    _, labels, centers = cv2.kmeans(sample, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=k)
    order = np.argsort(-counts)
    centers = centers[order]
    hex_cols = []
    for c in centers:
        b, g, r = int(np.clip(c[0], 0, 255)), int(np.clip(c[1], 0, 255)), int(np.clip(c[2], 0, 255))
        hex_cols.append(f"#{r:02x}{g:02x}{b:02x}")
    return hex_cols, centers


def process_single_clip(item):
    """
    Given a clip item (scene beat or pure screen):
    1. Decodes 24 evenly spaced 16:9 frames from the exact .mp4 file.
    2. Saves the 8-frame strip (lab/strips/...) from frames [0, 3, 6, 10, 13, 17, 20, 23] so strip == video 100%.
    3. Computes dense optical flow (Farneback) + pixel deltas + trajectory (u, v, r) + true species topology.
    4. Renders 4 high-signal 16:9 pattern images (burn, stone, slit, dew) to lab/patterns/<mode>/<id>.jpg.
    """
    cid = item["cid"]
    mp4_path = item["mp4_path"]
    strip_path = item["strip_path"]
    thumb_path = item.get("thumb_path")
    is_screen = item["is_screen"]

    W, H = 384, 216
    frames_bgr, actual_dur = decode_video_frames(mp4_path, target_n=24, W=W, H=H)
    if not frames_bgr:
        return None

    N = len(frames_bgr)
    idx8 = np.linspace(0, N - 1, 8).astype(int)
    frames8_bgr = [frames_bgr[i] for i in idx8]

    # 1. Write 100% synchronized 8-frame strip (192x108 per tile -> 1536x108)
    tw, th = 192, 108
    strip_tiles = [cv2.resize(f, (tw, th), interpolation=cv2.INTER_AREA) for f in frames8_bgr]
    strip_img = np.concatenate(strip_tiles, axis=1)
    os.makedirs(os.path.dirname(strip_path), exist_ok=True)
    cv2.imwrite(strip_path, strip_img, [int(cv2.IMWRITE_JPEG_QUALITY), 88])

    # Also ensure thumb matches mid-frame if scene beat
    if thumb_path and not is_screen:
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        cv2.imwrite(thumb_path, frames8_bgr[3], [int(cv2.IMWRITE_JPEG_QUALITY), 88])

    # 2. Compute Dense Optical Flow (Farneback) and Pixel Frame Differences across the 24 frames
    grays = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames_bgr]
    flow_mags = []
    flow_vx = []
    flow_vy = []
    pixel_diffs = []
    cut_flags = [False] * N

    for i in range(N - 1):
        # Small downscale for fast Farneback optical flow (192x108)
        g0 = cv2.resize(grays[i], (192, 108))
        g1 = cv2.resize(grays[i + 1], (192, 108))
        diff = cv2.absdiff(grays[i + 1], grays[i]).astype(np.float32) / 255.0
        mean_diff = float(diff.mean())
        if mean_diff > 0.22:
            # Camera cut inside clip: suppress fake cross-cut optical flow spike
            cut_flags[i + 1] = True
            flow_mags.append(np.zeros((H, W), dtype=np.float32))
            flow_vx.append(np.zeros((H, W), dtype=np.float32))
            flow_vy.append(np.zeros((H, W), dtype=np.float32))
            pixel_diffs.append(np.zeros((H, W), dtype=np.float32))
        else:
            fl = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 2, 13, 2, 5, 1.1, 0)
            vx = cv2.resize(fl[:, :, 0], (W, H))
            vy = cv2.resize(fl[:, :, 1], (W, H))
            mag = np.sqrt(vx ** 2 + vy ** 2)
            flow_mags.append(mag)
            flow_vx.append(vx)
            flow_vy.append(vy)
            pixel_diffs.append(diff)

    # Pad last frame
    flow_mags.append(flow_mags[-1] if flow_mags else np.zeros((H, W), dtype=np.float32))
    flow_vx.append(flow_vx[-1] if flow_vx else np.zeros((H, W), dtype=np.float32))
    flow_vy.append(flow_vy[-1] if flow_vy else np.zeros((H, W), dtype=np.float32))
    pixel_diffs.append(pixel_diffs[-1] if pixel_diffs else np.zeros((H, W), dtype=np.float32))

    # 3. Measure accurate (u, v, r) for the 8 keyframes using Optical Flow + Saliency/Phosphor/Face
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xx_norm = xx / W
    yy_norm = yy / H
    center_prior = np.exp(-((xx_norm - 0.5) ** 2 / (2 * 0.32 ** 2) + (yy_norm - 0.48) ** 2 / (2 * 0.30 ** 2)))

    raw_uvr = []
    for k, fi in enumerate(idx8):
        fr = frames_bgr[fi]
        gr = grays[fi]
        mag = flow_mags[fi]
        pdiff = pixel_diffs[fi]

        # Laplacian edge energy
        lap = np.abs(cv2.Laplacian(gr, cv2.CV_32F))
        lap = lap / (lap.max() + 1e-6)

        if is_screen:
            # Pure screen: active phosphor characters/vectors + changing screen region
            b, g, r_ch = fr[:, :, 0].astype(np.float32), fr[:, :, 1].astype(np.float32), fr[:, :, 2].astype(np.float32)
            phosphor = np.maximum(g, np.maximum(b, r_ch)) / 255.0
            energy = (0.45 * pdiff + 0.30 * (mag / (mag.max() + 1.5)) + 0.25 * phosphor * lap) * center_prior
        else:
            # Scene beat: check Haar face first, then combine optical flow + skin/subject energy
            eq = cv2.equalizeHist(gr)
            faces = []
            for cas in (FACE_FRONT, FACE_ALT, FACE_PROF):
                det = cas.detectMultiScale(eq, scaleFactor=1.12, minNeighbors=4, minSize=(24, 24))
                if len(det) > 0:
                    for (x, y, fw, fh) in det:
                        faces.append((x, y, fw, fh))
            if faces:
                # Pick strongest/largest face near frame center or motion
                best = max(faces, key=lambda b: (b[2] * b[3]) * (1.0 - 0.5 * abs((b[0] + b[2]/2)/W - 0.5)))
                u = float(np.clip((best[0] + best[2] * 0.5) / W, 0.12, 0.88))
                v = float(np.clip((best[1] + best[3] * 0.5) / H, 0.14, 0.86))
                rad = float(np.clip(math.sqrt((best[2]/W) * (best[3]/H)) * 0.65, 0.11, 0.22))
                raw_uvr.append([u, v, rad, True])
                continue

            # Otherwise use dense optical flow + contrast energy
            ycrcb = cv2.cvtColor(fr, cv2.COLOR_BGR2YCrCb)
            cr, cb = ycrcb[:, :, 1].astype(np.float32), ycrcb[:, :, 2].astype(np.float32)
            skin = np.exp(-((cr - 150) ** 2 / (2 * 18 ** 2) + (cb - 112) ** 2 / (2 * 18 ** 2)))
            skin[gr < 30] = 0.0
            norm_mag = mag / (np.percentile(mag, 98) + 0.8)
            norm_mag = np.clip(norm_mag, 0, 1.5)
            energy = (0.50 * norm_mag + 0.25 * pdiff * 3.0 + 0.15 * skin + 0.10 * lap) * center_prior

        # Smooth energy map with a Gaussian window to locate primary subject blob
        energy_blur = cv2.GaussianBlur(energy.astype(np.float32), (31, 31), 9.0)
        min_v, max_v, min_loc, max_loc = cv2.minMaxLoc(energy_blur)
        if max_v > 0.02:
            pk_u = max_loc[0] / W
            pk_v = max_loc[1] / H
            # Compute local spread around peak for radius r
            thresh = energy_blur > (max_v * 0.55)
            area_frac = float(thresh.mean())
            rad = float(np.clip(math.sqrt(area_frac) * 0.55, 0.10, 0.22))
            u = float(np.clip(pk_u, 0.12, 0.88))
            v = float(np.clip(pk_v, 0.14, 0.86))
        else:
            u, v, rad = 0.50, 0.48, 0.14
        raw_uvr.append([u, v, rad, False])

    # Segment-aware temporal smoothing (do not smooth across camera cuts)
    uvr = [x[:3] for x in raw_uvr]
    for p in range(2):
        new_uvr = [list(x) for x in uvr]
        for k in range(8):
            fi = idx8[k]
            prev_cut = (k > 0) and any(cut_flags[idx8[k-1]+1 : fi+1])
            next_cut = (k < 7) and any(cut_flags[fi+1 : idx8[k+1]+1])
            w_self = 0.65 if raw_uvr[k][3] else 0.50
            u_acc, v_acc, r_acc, w_tot = w_self * uvr[k][0], w_self * uvr[k][1], w_self * uvr[k][2], w_self
            if k > 0 and not prev_cut:
                w_n = (1.0 - w_self) * 0.5
                u_acc += w_n * uvr[k-1][0]; v_acc += w_n * uvr[k-1][1]; r_acc += w_n * uvr[k-1][2]; w_tot += w_n
            if k < 7 and not next_cut:
                w_n = (1.0 - w_self) * 0.5
                u_acc += w_n * uvr[k+1][0]; v_acc += w_n * uvr[k+1][1]; r_acc += w_n * uvr[k+1][2]; w_tot += w_n
            new_uvr[k] = [round(u_acc / w_tot, 4), round(v_acc / w_tot, 4), round(r_acc / w_tot, 4)]
        uvr = new_uvr

    # 4. Compute TRUE Geometric Worm Species (topology) directly from the measured motion & trajectory
    us = np.array([p[0] for p in uvr])
    vs = np.array([p[1] for p in uvr])
    rs = np.array([p[2] for p in uvr])
    du_net = float(us[-1] - us[0])
    dv_net = float(vs[-1] - vs[0])
    dr_net = float(rs[-1] - rs[0])
    u_span = float(us.max() - us.min())
    v_span = float(vs.max() - vs.min())
    r_span = float(rs.max() - rs.min())
    step_du = np.diff(us)
    sign_flips = int(np.sum(np.diff(np.sign(step_du[np.abs(step_du) > 0.02])) != 0))
    path_len = float(np.sum(np.sqrt(np.diff(us)**2 + np.diff(vs)**2)))
    chord_len = float(math.sqrt(du_net**2 + dv_net**2))
    tortuosity = path_len / (chord_len + 0.03)

    # Global optical flow camera pan / zoom check
    mean_vx = float(np.mean([vx.mean() for vx in flow_vx]))
    mean_mag = float(np.mean([m.mean() for m in flow_mags]))

    if u_span < 0.09 and v_span < 0.09 and r_span < 0.035:
        topology = "VERTICAL_PILLAR"
    elif r_span >= 0.045 or abs(dr_net) >= 0.038:
        topology = "EXPANDING_CONE_FUNNEL"
    elif sign_flips >= 2 and u_span >= 0.14:
        topology = "DOUBLE_HELIX_BRAID"
    elif (abs(du_net) >= 0.13 and tortuosity < 1.65) or abs(mean_vx) > 0.85:
        topology = "SHEARED_DIAGONAL_RIBBON"
    elif tortuosity >= 1.45 or (u_span >= 0.10 and v_span >= 0.09):
        topology = "HELICAL_CORKSCREW"
    else:
        # Fallback based on strongest geometric feature
        if u_span < 0.12 and v_span < 0.12:
            topology = "VERTICAL_PILLAR"
        elif abs(du_net) >= abs(dv_net):
            topology = "SHEARED_DIAGONAL_RIBBON"
        else:
            topology = "HELICAL_CORKSCREW"

    pan_shear_deg = round(float(math.degrees(math.atan2(du_net, 1.0))), 1)
    cone_flare_dr = round(dr_net, 4)

    # Extract dominant color palette
    hex_cols, bgr_centers = extract_dominant_colors_bgr(frames_bgr, k=5)

    # =========================================================================
    # RENDER 1: BURN-IN HEATMAP (lab/patterns/burn/<cid>.jpg)
    # Real pixel-level accumulated optical flow + temporal delta on dark exposure
    # =========================================================================
    mean_frame = np.mean([f.astype(np.float32) for f in frames_bgr], axis=0)
    burn_base = (mean_frame * 0.36).astype(np.uint8)

    acc_heat = np.zeros((H, W), dtype=np.float32)
    for i in range(N):
        m = flow_mags[i]
        d = pixel_diffs[i]
        acc_heat += 0.65 * np.clip(m / 4.0, 0, 1.5) + 0.35 * np.clip(d * 3.5, 0, 1.5)
    # Also add soft Gaussian footprint along the tracked trajectory so stationary glowing screens register
    for (u, v, r) in uvr:
        g_blob = np.exp(-((xx_norm - u)**2 + (yy_norm - v)**2) / (2 * (r * 0.85)**2))
        acc_heat += 0.35 * g_blob

    acc_heat = cv2.GaussianBlur(acc_heat, (25, 25), 7.0)
    if acc_heat.max() > 1e-5:
        acc_norm = np.clip(acc_heat / np.percentile(acc_heat, 99.2), 0, 1.0)
    else:
        acc_norm = acc_heat

    heat_u8 = (acc_norm * 255).astype(np.uint8)
    heat_color = cv2.applyColorMap(heat_u8, cv2.COLORMAP_INFERNO)
    # Blend where heat > 0.08
    alpha = np.clip((acc_norm - 0.05) * 0.88, 0, 0.85)[:, :, None]
    burn_img = (burn_base.astype(np.float32) * (1.0 - alpha) + heat_color.astype(np.float32) * alpha).astype(np.uint8)

    # Draw isothermal contour rings at 0.45 and 0.75
    for thresh_val, col_bgr in [(115, (255, 220, 0)), (195, (255, 255, 255))]:
        _, bin_m = cv2.threshold(heat_u8, thresh_val, 255, cv2.THRESH_BINARY)
        cnts, _ = cv2.findContours(bin_m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(burn_img, cnts, -1, col_bgr, 1, cv2.LINE_AA)

    # Draw subtle 16:9 Rabatment & Thirds grid + tracked spine
    for frac in (1/3, 2/3):
        cv2.line(burn_img, (int(frac*W), 0), (int(frac*W), H), (90, 110, 90), 1)
        cv2.line(burn_img, (0, int(frac*H)), (W, int(frac*H)), (90, 110, 90), 1)
    pts_px = [(int(p[0]*W), int(p[1]*H)) for p in uvr]
    for i in range(len(pts_px) - 1):
        cv2.line(burn_img, pts_px[i], pts_px[i+1], (255, 240, 150), 2, cv2.LINE_AA)
    cv2.circle(burn_img, pts_px[0], 4, (255, 229, 0), -1, cv2.LINE_AA)
    cv2.circle(burn_img, pts_px[-1], 5, (180, 68, 255), -1, cv2.LINE_AA)

    burn_rel = f"patterns/burn/{cid}.jpg"
    cv2.imwrite(os.path.join(LAB, burn_rel), burn_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    # =========================================================================
    # RENDER 2: OXBLOOD & GOLD TEMPORAL REGISTRATION (lab/patterns/stone/<cid>.jpg)
    # Afterlight 03: Early-phase edges/motion in Burnished Gold, Late-phase in Crimson/Cyan
    # =========================================================================
    early_bgr = np.mean([f.astype(np.float32) for f in frames_bgr[1:7]], axis=0).astype(np.uint8)
    late_bgr = np.mean([f.astype(np.float32) for f in frames_bgr[N-7:N-1]], axis=0).astype(np.uint8)
    early_g = cv2.cvtColor(early_bgr, cv2.COLOR_BGR2GRAY)
    late_g = cv2.cvtColor(late_bgr, cv2.COLOR_BGR2GRAY)

    # High-contrast charcoal print ground from mid frame
    mid_g = grays[N // 2].astype(np.float32) / 255.0
    stone_img = (frames_bgr[N // 2].astype(np.float32) * 0.28).astype(np.float32)

    # Compute what vanished (Early > Late) vs what arrived (Late > Early) + edge structure
    diff_early = np.clip((early_g.astype(np.float32) - late_g.astype(np.float32)) / 255.0, 0, 1.0)
    diff_late = np.clip((late_g.astype(np.float32) - early_g.astype(np.float32)) / 255.0, 0, 1.0)
    edge_early = cv2.Canny(early_g, 45, 130).astype(np.float32) / 255.0
    edge_late = cv2.Canny(late_g, 45, 130).astype(np.float32) / 255.0

    gold_mask = np.clip(diff_early * 2.4 + edge_early * 0.55, 0, 1.0)[:, :, None]
    crimson_mask = np.clip(diff_late * 2.4 + edge_late * 0.65, 0, 1.0)[:, :, None]

    # BGR colors: Burnished Gold = (50, 176, 240), Oxblood Crimson/Cyan = (90, 55, 255)
    gold_bgr = np.array([45, 175, 245], dtype=np.float32)
    crim_bgr = np.array([110, 50, 255], dtype=np.float32) if not is_screen else np.array([255, 225, 0], dtype=np.float32)

    stone_img = stone_img * (1.0 - 0.65 * gold_mask) + gold_bgr * (0.75 * gold_mask)
    stone_img = stone_img * (1.0 - 0.70 * crimson_mask) + crim_bgr * (0.85 * crimson_mask)
    stone_img = np.clip(stone_img, 0, 255).astype(np.uint8)

    # Draw displacement vector from Early (t=0.2) to Late (t=0.8)
    p_early = pts_px[1]
    p_late = pts_px[6]
    cv2.circle(stone_img, p_early, int(uvr[1][2]*W*0.65), (45, 175, 245), 1, cv2.LINE_AA)
    cv2.circle(stone_img, p_late, int(uvr[6][2]*W*0.65), (255, 229, 0), 2, cv2.LINE_AA)
    cv2.arrowedLine(stone_img, p_early, p_late, (255, 255, 255), 2, cv2.LINE_AA, tipLength=0.18)

    stone_rel = f"patterns/stone/{cid}.jpg"
    cv2.imwrite(os.path.join(LAB, stone_rel), stone_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    # =========================================================================
    # RENDER 3: TRUE PIXEL X-T SLIT-SCAN TOMOGRAPHY + FLOW ROSE (lab/patterns/slit/<cid>.jpg)
    # Left 62%: True X-T Horizontal Slit-Scan stacked across all frames at the active Y band
    # Right 38%: True Y-T Vertical Slit-Scan + Optical Flow Vector Field + 5-Color Bar
    # =========================================================================
    slit_img = np.zeros((H, W, 3), dtype=np.uint8)
    w_left = int(W * 0.62)
    w_right = W - w_left

    # Mean vertical focus band v_mid
    v_mid = int(np.clip(np.median(vs) * H, 24, H - 24))
    u_mid = int(np.clip(np.median(us) * W, 24, W - 24))

    # Build X-T slit scan (time goes top -> bottom from t=0 to t=1, X goes left -> right)
    xt_rows = []
    for i, fr in enumerate(frames_bgr):
        # Average a 16-pixel band around v_mid so faces/text are crisp in the X-T slice
        y0, y1 = max(0, v_mid - 8), min(H, v_mid + 8)
        row_bgr = fr[y0:y1, :, :].mean(axis=0, keepdims=True).astype(np.uint8)
        xt_rows.append(row_bgr)
    xt_full = np.concatenate(xt_rows, axis=0)  # shape (N, W, 3)
    xt_resized = cv2.resize(xt_full, (w_left, H - 22), interpolation=cv2.INTER_CUBIC)
    slit_img[:H-22, :w_left] = xt_resized

    # Overlay the tracked u(t) spine on the X-T slit-scan (X = u * w_left, Y = t * (H-22))
    xt_pts = [(int(uvr[k][0] * w_left), int((k / 7.0) * (H - 26) + 2)) for k in range(8)]
    for k in range(7):
        cv2.line(slit_img, xt_pts[k], xt_pts[k+1], (255, 229, 0), 2, cv2.LINE_AA)
        cv2.circle(slit_img, xt_pts[k], 3, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(slit_img, xt_pts[7], 4, (204, 68, 255), -1, cv2.LINE_AA)

    # Right side top: mid-frame with dense optical flow vector arrows on a 6x4 grid
    flow_panel = (frames_bgr[N // 2].astype(np.float32) * 0.55).astype(np.uint8)
    avg_vx = np.mean(flow_vx, axis=0)
    avg_vy = np.mean(flow_vy, axis=0)
    for gy in range(24, H - 20, 36):
        for gx in range(32, W - 24, 48):
            vx_val = float(avg_vx[gy, gx]) * 8.0
            vy_val = float(avg_vy[gy, gx]) * 8.0
            p0 = (gx, gy)
            p1 = (int(np.clip(gx + vx_val, 0, W-1)), int(np.clip(gy + vy_val, 0, H-1)))
            cv2.arrowedLine(flow_panel, p0, p1, (255, 229, 0), 2, cv2.LINE_AA, tipLength=0.3)
    slit_img[:H-22, w_left:] = cv2.resize(flow_panel, (w_right, H - 22))
    cv2.line(slit_img, (w_left, 0), (w_left, H - 22), (180, 180, 180), 1)

    # Bottom 22px bar: 5-color dominant k-means palette strip across full width
    bw = W // 5
    for ci, c_bgr in enumerate(bgr_centers):
        x0 = ci * bw
        x1 = W if ci == 4 else (ci + 1) * bw
        col_tuple = (int(c_bgr[0]), int(c_bgr[1]), int(c_bgr[2]))
        cv2.rectangle(slit_img, (x0, H - 22), (x1, H), col_tuple, -1)

    slit_rel = f"patterns/slit/{cid}.jpg"
    cv2.imwrite(os.path.join(LAB, slit_rel), slit_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    # =========================================================================
    # RENDER 4: CHRONOPHOTOGRAPHIC DEW TRAIL + GEOMETRY CARD (lab/patterns/dew/<cid>.jpg)
    # Afterlight 02d: Darkened 16:9 Rabatment room + 8 sharp lens droplets from f1..f8
    # =========================================================================
    dew_img = (frames_bgr[N // 2].astype(np.float32) * 0.30).astype(np.uint8)
    # Draw 16:9 Rabatment verticals (x = H/W = 9/16 = 0.5625 and 1 - 9/16 = 0.4375) & diagonals
    for rx in (int(0.4375 * W), int(0.5625 * W)):
        cv2.line(dew_img, (rx, 0), (rx, H - 16), (70, 110, 90), 1)
    cv2.line(dew_img, (0, 0), (W, H - 16), (55, 75, 65), 1)
    cv2.line(dew_img, (W, 0), (0, H - 16), (55, 75, 65), 1)

    # Stamp circular lens droplets from f1..f8 along the trajectory (u, v, r)
    for k in range(8):
        fr_k = frames8_bgr[k]
        u, v, r = uvr[k]
        cx, cy = int(u * W), int(v * (H - 16))
        rad_px = int(max(18, r * W * 0.58))
        mask = np.zeros((H, W), dtype=np.uint8)
        cv2.circle(mask, (cx, cy), rad_px, 255, -1, cv2.LINE_AA)
        mask_blur = cv2.GaussianBlur(mask, (9, 9), 3.0).astype(np.float32) / 255.0
        m3 = mask_blur[:, :, None] * (0.45 + 0.55 * (k / 7.0))
        dew_img = (dew_img.astype(np.float32) * (1.0 - m3) + fr_k.astype(np.float32) * m3).astype(np.uint8)
        # Ring colored by temporal progression: Cyan (k=0) -> Gold (k=4) -> Magenta (k=7)
        ring_col = (255, 229, 0) if k < 3 else ((0, 180, 255) if k < 6 else (204, 68, 255))
        cv2.circle(dew_img, (cx, cy), rad_px, ring_col, 1 if k < 7 else 2, cv2.LINE_AA)

    for k in range(7):
        p0 = (int(uvr[k][0]*W), int(uvr[k][1]*(H-16)))
        p1 = (int(uvr[k+1][0]*W), int(uvr[k+1][1]*(H-16)))
        cv2.line(dew_img, p0, p1, (255, 255, 255), 1, cv2.LINE_AA)

    # Bottom 16px color palette bar
    for ci, c_bgr in enumerate(bgr_centers):
        x0 = ci * bw
        x1 = W if ci == 4 else (ci + 1) * bw
        col_tuple = (int(c_bgr[0]), int(c_bgr[1]), int(c_bgr[2]))
        cv2.rectangle(dew_img, (x0, H - 16), (x1, H), col_tuple, -1)

    dew_rel = f"patterns/dew/{cid}.jpg"
    cv2.imwrite(os.path.join(LAB, dew_rel), dew_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    return {
        "cid": cid,
        "is_screen": is_screen,
        "actual_dur": actual_dur,
        "uvr": uvr,
        "topology": topology,
        "pan_shear_deg": pan_shear_deg,
        "cone_flare_dr": cone_flare_dr,
        "mean_flow_mag": round(mean_mag, 3),
        "palette": hex_cols,
        "patterns": {
            "burn": burn_rel,
            "stone": stone_rel,
            "slit": slit_rel,
            "dew": dew_rel,
        },
        "mid_pil": Image.fromarray(cv2.cvtColor(frames8_bgr[3], cv2.COLOR_BGR2RGB)),
        "burn_pil": Image.fromarray(cv2.cvtColor(burn_img, cv2.COLOR_BGR2RGB)),
        "slit_pil": Image.fromarray(cv2.cvtColor(slit_img, cv2.COLOR_BGR2RGB)),
        "dew_pil": Image.fromarray(cv2.cvtColor(dew_img, cv2.COLOR_BGR2RGB)),
    }


# CLIP Zero-Shot Prompts for Geometry, Motion, and Color Classification
GEOM_PROMPTS = [
    ("CLOSEUP_PORTRAIT", "close-up portrait of a single person's face centered in the frame"),
    ("TWO_SHOT_DIALOGUE", "two people facing each other or talking in a balanced two-shot composition"),
    ("WIDE_ARCHITECTURE", "wide architectural command room or landscape with deep perspective lines"),
    ("CRT_TEXT_GRID", "close-up of a glowing computer monitor screen with rows of text or numbers"),
    ("VECTOR_MAP_BOARD", "glowing vector world map display board with trajectory arcs and grid lines"),
]

COLOR_PROMPTS = [
    ("PHOSPHOR_CYAN_GREEN", "dark screen with glowing cyan blue or green phosphor monochrome light"),
    ("WARM_TUNGSTEN_SKIN", "warm amber tungsten indoor lighting with skin tones and wood or brass"),
    ("CRIMSON_DEFCON_ALERT", "high-contrast red crimson and orange warning lights in a dark room"),
    ("COLD_DAYLIGHT_EXT", "cool overcast daylight exterior with grey blue sky water or trees"),
    ("HIGH_CONTRAST_NOIR", "deep black shadows with stark high-contrast white and silver highlights"),
]

MOTION_PROMPTS = [
    ("LOCKED_STATIC_PILLAR", "stationary locked camera with vertical lines and central static focus"),
    ("LATERAL_PAN_RIBBON", "horizontal diagonal motion streak or sweeping lateral camera pan across the frame"),
    ("RADIAL_ZOOM_CONE", "expanding radial rings or funnel cone zooming toward the viewer"),
    ("ALTERNATING_BRAID", "two separate focal hotspots on the left and right sides of the frame"),
    ("SPIRAL_CURVE_HELIX", "curved swirling S-shaped trajectory moving across both horizontal and vertical axes"),
]


def main():
    t0 = time.time()
    worm_path = os.path.join(LAB, "wargames-worm-volume.json")
    scr_path = os.path.join(LAB, "wargames-screens-program.json")
    stgl_path = os.path.join(LAB, "wargames-stgl-ir.json")

    with open(worm_path) as f:
        d_worm = json.load(f)
    with open(scr_path) as f:
        d_scr = json.load(f)
    with open(stgl_path) as f:
        d_stgl = json.load(f)

    tasks = []
    for b in d_worm["beats"]:
        tasks.append({
            "cid": b["id"],
            "is_screen": False,
            "mp4_path": os.path.join(LAB, b["video"]),
            "strip_path": os.path.join(LAB, b["strip"]),
            "thumb_path": os.path.join(LAB, b["thumb"]),
        })

    for st in d_scr["screen_states"]:
        vid_rel = st.get("clip") or st.get("video")
        cid = f"SCR_{st['state_index']:02d}_{st['shot_id']}"
        tasks.append({
            "cid": cid,
            "is_screen": True,
            "state_index": st["state_index"],
            "mp4_path": os.path.join(LAB, vid_rel),
            "strip_path": os.path.join(LAB, st["strip"]),
            "thumb_path": None,
        })

    print(f"1. Processing all {len(tasks)} video clips (105 scenes + 68 screens) into 4 Spatiotemporal Pattern Images each ({len(tasks)*4} images)...", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(process_single_clip, tasks):
            if res is not None:
                results.append(res)
    print(f"   Rendered {len(results)*4} pattern images and synchronized {len(results)} 8-frame strips in {time.time()-t0:.1f}s.", flush=True)

    # 2. Run LAION CLIP ViT-B/32 across Keyframes + Burn-In Heatmaps + Slit-Scan Tomography + Dew Composites
    print("2. Loading LAION CLIP ViT-B/32 and encoding all rendered pattern images...", flush=True)
    encode_images, encode_texts = load_laion_clip()

    def batch_encode(pil_list, bs=32):
        out = []
        for i in range(0, len(pil_list), bs):
            out.append(encode_images(pil_list[i:i+bs]))
        return np.concatenate(out, axis=0)

    E_mid = batch_encode([r["mid_pil"] for r in results])
    E_burn = batch_encode([r["burn_pil"] for r in results])
    E_slit = batch_encode([r["slit_pil"] for r in results])
    E_dew = batch_encode([r["dew_pil"] for r in results])

    # Joint Spatiotemporal CLIP Embedding combining Keyframe + Burn-In Heatmap + Slit-Scan + Dew Trail
    E_joint = 0.35 * E_mid + 0.25 * E_burn + 0.20 * E_slit + 0.20 * E_dew
    E_joint = E_joint / (np.linalg.norm(E_joint, axis=1, keepdims=True) + 1e-9)

    # Encode zero-shot text prompts
    T_geom = encode_texts([p[1] for p in GEOM_PROMPTS])
    T_color = encode_texts([p[1] for p in COLOR_PROMPTS])
    T_motion = encode_texts([p[1] for p in MOTION_PROMPTS])

    S_geom = E_mid @ T_geom.T
    S_color = E_dew @ T_color.T
    S_motion = (0.5 * E_burn + 0.5 * E_slit) @ T_motion.T

    # Compute 2D PCA layout of the Joint Spatiotemporal CLIP Embeddings
    X = E_joint - E_joint.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    xy = U[:, :2] * S[:2]
    xy = (xy - xy.min(0)) / (xy.max(0) - xy.min(0) + 1e-9)

    # Cosine similarity matrix for Top-3 Visual/Spatiotemporal Twins
    sim_mat = E_joint @ E_joint.T

    by_cid = {}
    for idx, r in enumerate(results):
        g_idx = int(np.argmax(S_geom[idx]))
        c_idx = int(np.argmax(S_color[idx]))
        m_idx = int(np.argmax(S_motion[idx]))

        sims = sim_mat[idx].copy()
        sims[idx] = -1.0
        nn_indices = np.argsort(-sims)[:3]
        twins = [{"cid": results[j]["cid"], "sim": round(float(sims[j]), 3)} for j in nn_indices]

        clip_info = {
            "geom_class": GEOM_PROMPTS[g_idx][0],
            "geom_score": round(float(S_geom[idx, g_idx]), 3),
            "color_class": COLOR_PROMPTS[c_idx][0],
            "color_score": round(float(S_color[idx, c_idx]), 3),
            "motion_class": MOTION_PROMPTS[m_idx][0],
            "motion_score": round(float(S_motion[idx, m_idx]), 3),
            "clip_x": round(float(xy[idx, 0]), 4),
            "clip_y": round(float(xy[idx, 1]), 4),
            "twins": twins,
        }
        r["clip"] = clip_info
        # Remove PIL objects before JSON serialization
        del r["mid_pil"], r["burn_pil"], r["slit_pil"], r["dew_pil"]
        by_cid[r["cid"]] = r

    # 3. Update wargames-worm-volume.json, wargames-stgl-ir.json, and wargames-screens-program.json
    stgl_by_id = {s["id"]: s for s in d_stgl.get("shots", [])}

    for b in d_worm["beats"]:
        r = by_cid.get(b["id"])
        if not r:
            continue
        b["dur_sec"] = r["actual_dur"]
        b["topology"] = r["topology"]
        b["pan_shear_angle_deg"] = r["pan_shear_deg"]
        b["cone_flare_dr"] = r["cone_flare_dr"]
        b["patterns"] = r["patterns"]
        b["palette"] = r["palette"]
        b["clip_signature"] = r["clip"]
        for k, wf in enumerate(b.get("worm_frames", [])):
            if k < len(r["uvr"]):
                wf["u"], wf["v"], wf["r"] = r["uvr"][k]

        # Sync wargames-stgl-ir.json
        st_shot = stgl_by_id.get(b["id"])
        if st_shot:
            st_shot["patterns"] = r["patterns"]
            st_shot["palette"] = r["palette"]
            st_shot["clip_signature"] = r["clip"]
            for k, f8 in enumerate(st_shot.get("frames_8", [])):
                if k < len(r["uvr"]):
                    f8["u"], f8["v"], f8["r"] = r["uvr"][k]

    for st in d_scr["screen_states"]:
        cid = f"SCR_{st['state_index']:02d}_{st['shot_id']}"
        r = by_cid.get(cid)
        if not r:
            continue
        st["dur"] = r["actual_dur"]
        st["patterns"] = r["patterns"]
        st["palette"] = r["palette"]
        st["clip_signature"] = r["clip"]
        if "worm_3d" in st and st["worm_3d"]:
            st["worm_3d"]["topology"] = r["topology"]
            for k, wf in enumerate(st["worm_3d"].get("worm_frames", [])):
                if k < len(r["uvr"]):
                    wf["u"], wf["v"], wf["r"] = r["uvr"][k]

    with open(worm_path, "w") as f:
        json.dump(d_worm, f, separators=(",", ":"))
    with open(scr_path, "w") as f:
        json.dump(d_scr, f, separators=(",", ":"))
    with open(stgl_path, "w") as f:
        json.dump(d_stgl, f, separators=(",", ":"))

    atlas_path = os.path.join(LAB, "wargames-clip-patterns.json")
    with open(atlas_path, "w") as f:
        json.dump({
            "total_clips": len(results),
            "total_pattern_images": len(results) * 4,
            "geom_prompts": GEOM_PROMPTS,
            "color_prompts": COLOR_PROMPTS,
            "motion_prompts": MOTION_PROMPTS,
            "items": results,
        }, f, indent=2)

    print(f"3. Done in {time.time()-t0:.1f}s! Saved {len(results)*4} pattern images + CLIP embeddings to {atlas_path}.", flush=True)


if __name__ == "__main__":
    main()

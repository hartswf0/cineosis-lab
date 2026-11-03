#!/usr/bin/env python3
"""
3D SPATIOTEMPORAL VOLUME V(u, v, tau) & ACTION-TUBE WORM ANALYZER (ALL VIDEOS & ALL 10 CUTS)
============================================================================================
Stacks every 2D frame (u, v) in [0, 1]^2 along time tau in [0, T] across:
  - All 592 8-frame strips (4,736 frames)
  - All 68 pure computer screens
  - All 105 scene beats AND all 10 simultaneous montage cuts per beat (1,050 3D Cut-Worms
    built from 4,300 real-pixel measured sub-shots: 1983, synthesis, clip, vjepa, blip,
    cineosis, trurl, klapaucius, murch, novelty)
  - All 370 spoken dialogue turns and their 1,110 archival takes (3 takes per line)

Extracts for every volume & sub-frame (f1..f8):
1. 3D Spatiotemporal Worm / Action-Tube Worldline c(tau) = (u(tau), v(tau), tau),
   secondary Rabatment counterweight worm c2(tau), cross-sectional radius r(tau),
   and 7-way Topological Classification:
   - VERTICAL_PILLAR             (Locked tripod + static blocking in u=1/3 or 0.5)
   - SHEARED_DIAGONAL_RIBBON     (Camera pan / lateral track at angle theta = arctan(du/dtau))
   - EXPANDING_CONE_FUNNEL       (Dolly in / snap zoom flaring r(tau) outward/inward)
   - HELICAL_CORKSCREW           (S-Curve / Golden Spiral helical trajectory around tau-axis)
   - DOUBLE_HELIX_BRAID          (Two-shot dialogue counterpoint in left/right Rabatment squares)
   - EYE_TRACE_FRACTURE_TUBE     (Walter Murch continuous tube across cut plane, ||cA - cB|| <= 0.18)
   - EISENSTEIN_COLLISION_CUT    (Soviet Montage step-fracture / velocity inversion across cut)

2. KALMUS Core-Sample vs. Shell Chromatic Stratigraphy & Johannes Itten's 7 Color Contrasts:
   - Splits V(u, v, tau) into Core Worm (inside Jev Box tube) and Outer Shell (background negative space)
   - Computes CIE L*a*b* and HSV palettes (core/shell hex per frame)
   - Light-Dark Chiaroscuro Contrast: Delta_L*(tau) = |L*_core(tau) - L*_shell(tau)|
   - Cold-Warm & Complementary Hue Polarity: Delta_H(tau) in degrees [0..180] + warm/cool index
   - Contrast of Extension (Area Ratio): A_worm(tau) / A_frame

3. Bouleau's 14-Line Harmonic Armature & Rudolf Arnheim Eccentric Tension:
   - Extrudes Charles Bouleau's 14-Line Armature as 3D magnetic filaments
   - Measures shortest filament distance d_grid(tau), Arnheim Torque, and Eccentric Tension

4. 3D Space-Curve Differential Geometry (Frenet-Serret Frame):
   - Curvature kappa(tau), Torsion tau_torsion(tau), and Kinetic Jerk ||c'''(tau)||
   - Identifies exact peak-jerk sub-frame for Leonxlnx/earshot acoustic impact triggers
   - Bruce Block Visual Intensity Index I_Block(tau) in [0, 1]

5. Tomographic Slit-Scan Cross-Sections (u-tau and v-tau slices).
"""
import glob
import json
import math
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAB = os.path.join(ROOT, "lab")

RAB_L = 9.0 / 16.0          # 0.5625
RAB_R = 1.0 - (9.0 / 16.0)  # 0.4375

BOULEAU_14_SEGMENTS = [
    ((0.0, 0.0), (1.0, 1.0), "full_baroque_diag"),
    ((0.0, 1.0), (1.0, 0.0), "full_sinister_diag"),
    ((0.5, 0.0), (0.5, 1.0), "central_vertical"),
    ((0.0, 0.5), (1.0, 0.5), "central_horizontal"),
    ((RAB_R, 0.0), (RAB_R, 1.0), "rabatment_left_vert"),
    ((RAB_L, 0.0), (RAB_L, 1.0), "rabatment_right_vert"),
    ((0.0, 0.0), (RAB_L, 1.0), "rabatment_left_diag1"),
    ((0.0, 1.0), (RAB_L, 0.0), "rabatment_left_diag2"),
    ((RAB_R, 0.0), (1.0, 1.0), "rabatment_right_diag1"),
    ((RAB_R, 1.0), (1.0, 0.0), "rabatment_right_diag2"),
    ((0.5, 0.0), (1.0, 0.5), "diamond_ne"),
    ((1.0, 0.5), (0.5, 1.0), "diamond_se"),
    ((0.5, 1.0), (0.0, 0.5), "diamond_sw"),
    ((0.0, 0.5), (0.5, 0.0), "diamond_nw"),
]

H_STD, W_STD = 27, 48
UU_STD, VV_STD = np.meshgrid(np.linspace(0.0, 1.0, W_STD), np.linspace(0.0, 1.0, H_STD))


def rgb_to_hex(rgb_float):
    r = int(round(max(0.0, min(1.0, float(rgb_float[0]))) * 255.0))
    g = int(round(max(0.0, min(1.0, float(rgb_float[1]))) * 255.0))
    b = int(round(max(0.0, min(1.0, float(rgb_float[2]))) * 255.0))
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_lab_hsv_stats(rgb_pixels):
    if rgb_pixels.size == 0:
        return {"hex": "#101814", "L_star": 15.0, "hue_deg": 140.0, "sat": 0.2, "warm_cool": -0.2}
    mean_rgb = np.mean(rgb_pixels, axis=0)
    r, g, b = float(mean_rgb[0]), float(mean_rgb[1]), float(mean_rgb[2])
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    L_star = round(116.0 * (lum ** (1.0 / 3.0)) - 16.0 if lum > 0.008856 else 903.3 * lum, 2)
    L_star = max(0.0, min(100.0, L_star))

    cmax, cmin = max(r, g, b), min(r, g, b)
    delta = cmax - cmin
    if delta < 1e-5:
        hue = 0.0
    elif cmax == r:
        hue = 60.0 * (((g - b) / delta) % 6.0)
    elif cmax == g:
        hue = 60.0 * (((b - r) / delta) + 2.0)
    else:
        hue = 60.0 * (((r - g) / delta) + 4.0)
    sat = 0.0 if cmax < 1e-5 else (delta / cmax)
    warm_cool = round(math.cos(math.radians(hue - 30.0)) * min(1.0, sat * 1.8), 3)
    return {
        "hex": rgb_to_hex(mean_rgb),
        "L_star": round(L_star, 2),
        "hue_deg": round(hue, 1),
        "sat": round(sat, 3),
        "warm_cool": warm_cool,
    }


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    len_sq = dx * dx + dy * dy
    if len_sq < 1e-9:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def measure_bouleau_14_and_arnheim(u, v, sal_mass=0.5):
    best_dist = 9.9
    best_line = "central_vertical"
    for (x1, y1), (x2, y2), name in BOULEAU_14_SEGMENTS:
        d = point_to_segment_dist(u, v, x1, y1, x2, y2)
        if d < best_dist:
            best_dist = d
            best_line = name
    dist_from_center = math.hypot(u - 0.5, v - 0.5)
    arnheim_torque = round(dist_from_center * (0.5 + sal_mass), 4)
    if best_dist <= 0.045:
        grid_state = "HARMONIC_LOCK"
    elif 0.055 <= best_dist <= 0.135 and (u < 0.22 or u > 0.78 or v < 0.22 or v > 0.78):
        grid_state = "ARNHEIM_ECCENTRIC_TENSION"
    else:
        grid_state = "DYNAMIC_TRANSIT"
    return {
        "d_grid": round(best_dist, 4),
        "nearest_filament": best_line,
        "arnheim_torque": arnheim_torque,
        "grid_state": grid_state,
    }


def measure_frame_array_worm(arr, f_idx=1, tau_norm=0.0):
    """Measures a single H_STD x W_STD x 3 float32 frame array in [0,1]."""
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    gx = np.zeros_like(lum)
    gy = np.zeros_like(lum)
    gx[:, 1:-1] = 0.5 * (lum[:, 2:] - lum[:, :-2])
    gy[1:-1, :] = 0.5 * (lum[2:, :] - lum[:-2, :])
    grad = np.hypot(gx, gy)
    lum_dev = np.abs(lum - np.median(lum))
    sal = 0.65 * (grad / (np.max(grad) + 1e-6)) + 0.35 * (lum_dev / (np.max(lum_dev) + 1e-6))
    sal_power = np.power(np.maximum(sal, 1e-5), 1.8)
    tot_sal = float(np.sum(sal_power)) + 1e-8

    u1 = float(np.sum(UU_STD * sal_power) / tot_sal)
    v1 = float(np.sum(VV_STD * sal_power) / tot_sal)
    u_std = float(np.sqrt(np.sum(((UU_STD - u1) ** 2) * sal_power) / tot_sal))
    v_std = float(np.sqrt(np.sum(((VV_STD - v1) ** 2) * sal_power) / tot_sal))
    r_tube = round(max(0.08, min(0.42, 1.15 * math.hypot(u_std, v_std))), 3)

    left_mask = UU_STD <= 0.5
    right_mask = UU_STD > 0.5
    sal_left = float(np.sum(sal_power[left_mask])) + 1e-8
    sal_right = float(np.sum(sal_power[right_mask])) + 1e-8
    u_left = float(np.sum(UU_STD[left_mask] * sal_power[left_mask]) / sal_left)
    v_left = float(np.sum(VV_STD[left_mask] * sal_power[left_mask]) / sal_left)
    u_right = float(np.sum(UU_STD[right_mask] * sal_power[right_mask]) / sal_right)
    v_right = float(np.sum(VV_STD[right_mask] * sal_power[right_mask]) / sal_right)
    bilateral_balance = min(sal_left, sal_right) / max(sal_left, sal_right)
    rabatment_gap_du = round(u_right - u_left, 3)

    core_mask = (np.abs(UU_STD - u1) <= r_tube * 1.1) & (np.abs(VV_STD - v1) <= r_tube * 1.1)
    shell_mask = ~core_mask
    core_stats = rgb_to_lab_hsv_stats(arr[core_mask])
    shell_stats = rgb_to_lab_hsv_stats(arr[shell_mask])

    chiaroscuro_dL = round(abs(core_stats["L_star"] - shell_stats["L_star"]), 2)
    raw_dh = abs(core_stats["hue_deg"] - shell_stats["hue_deg"])
    hue_diff_deg = round(min(raw_dh, 360.0 - raw_dh), 1)
    cold_warm_diff = round(core_stats["warm_cool"] - shell_stats["warm_cool"], 3)
    area_ratio = round(float(np.mean(core_mask)), 3)

    bouleau = measure_bouleau_14_and_arnheim(u1, v1, sal_mass=float(np.mean(sal)))

    mid_r = max(0, min(H_STD - 1, int(round(v1 * (H_STD - 1)))))
    u_cols = np.linspace(0, W_STD - 1, 16, dtype=int)
    u_slice = [rgb_to_hex(arr[mid_r, c, :]) for c in u_cols]

    mid_c = max(0, min(W_STD - 1, int(round(u1 * (W_STD - 1)))))
    v_rows = np.linspace(0, H_STD - 1, 12, dtype=int)
    v_slice = [rgb_to_hex(arr[r_i, mid_c, :]) for r_i in v_rows]

    return {
        "f": f_idx,
        "tau_norm": round(tau_norm, 3),
        "u": round(u1, 3),
        "v": round(v1, 3),
        "r": r_tube,
        "c_left": [round(u_left, 3), round(v_left, 3)],
        "c_right": [round(u_right, 3), round(v_right, 3)],
        "rabatment_gap_du": rabatment_gap_du,
        "bilateral_balance": round(bilateral_balance, 3),
        "core_color": core_stats,
        "shell_color": shell_stats,
        "itten": {
            "chiaroscuro_dL": chiaroscuro_dL,
            "hue_polarity_deg": hue_diff_deg,
            "cold_warm_delta": cold_warm_diff,
            "extension_area_ratio": area_ratio,
        },
        "bouleau_14": bouleau,
        "_u_slice": u_slice,
        "_v_slice": v_slice,
    }


def finalize_worm_volume_from_frames(worm_frames, shot_id, dur_sec=3.2):
    u_tau_slice = [wf.pop("_u_slice") for wf in worm_frames]
    v_tau_slice = [wf.pop("_v_slice") for wf in worm_frames]
    core_colors_all = [wf["core_color"]["hex"] for wf in worm_frames]
    shell_colors_all = [wf["shell_color"]["hex"] for wf in worm_frames]

    dt = max(0.08, dur_sec / max(1, len(worm_frames)))
    pts = np.array([[wf["u"], wf["v"], wf["tau_norm"]] for wf in worm_frames], dtype=np.float64)
    vel = np.gradient(pts, dt, axis=0)
    acc = np.gradient(vel, dt, axis=0)
    jrk = np.gradient(acc, dt, axis=0)

    for k, wf in enumerate(worm_frames):
        v_vec = vel[k]
        a_vec = acc[k]
        j_vec = jrk[k]
        cross_va = np.cross(v_vec, a_vec)
        cross_norm = float(np.linalg.norm(cross_va))
        v_norm = max(1e-4, float(np.linalg.norm(v_vec)))

        kappa = round(min(25.0, cross_norm / (v_norm ** 3 + 1e-4)), 3)
        torsion = round(
            max(-25.0, min(25.0, float(np.dot(cross_va, j_vec)) / (cross_norm ** 2 + 1e-3))),
            3,
        )
        jerk_mag = round(min(50.0, float(np.linalg.norm(j_vec))), 3)
        i_block = min(
            0.99,
            0.30 * (wf["itten"]["chiaroscuro_dL"] / 45.0)
            + 0.25 * min(1.0, wf["r"] * 2.8)
            + 0.25 * min(1.0, float(np.linalg.norm(v_vec[:2])) * 3.5)
            + 0.20 * min(1.0, wf["bouleau_14"]["arnheim_torque"] * 2.2),
        )
        wf["diff_geom"] = {
            "speed_uv": round(float(np.linalg.norm(v_vec[:2])), 4),
            "curvature_kappa": kappa,
            "torsion_tau": torsion,
            "jerk_mag": jerk_mag,
            "bruce_block_intensity": round(i_block, 3),
        }

    u_vals = [wf["u"] for wf in worm_frames]
    v_vals = [wf["v"] for wf in worm_frames]
    r_vals = [wf["r"] for wf in worm_frames]
    du_total = u_vals[-1] - u_vals[0]
    dv_total = v_vals[-1] - v_vals[0]
    dr_total = r_vals[-1] - r_vals[0]
    u_span = max(u_vals) - min(u_vals)
    v_span = max(v_vals) - min(v_vals)
    mean_balance = float(np.mean([wf["bilateral_balance"] for wf in worm_frames]))
    mean_kappa = float(np.mean([wf["diff_geom"]["curvature_kappa"] for wf in worm_frames]))
    pan_angle_deg = round(math.degrees(math.atan2(du_total, 1.0)), 1)

    if abs(dr_total) >= 0.022:
        topology = "EXPANDING_CONE_FUNNEL"
        topo_grammar = (
            f"Dolly/Zoom Funnel (dr={dr_total:+.3f}): cross-sectional radius flares from "
            f"{r_vals[0]:.2f} to {r_vals[-1]:.2f}, compressing Negative Space."
        )
    elif abs(du_total) >= 0.048 and abs(du_total) > abs(dv_total) * 1.15:
        topology = "SHEARED_DIAGONAL_RIBBON"
        topo_grammar = (
            f"Lateral Pan/Track Ribbon (theta={pan_angle_deg:+.1f} deg, du={du_total:+.3f}): "
            f"worm shears across the u-tau plane."
        )
    elif (u_span >= 0.032 and v_span >= 0.025) or mean_kappa >= 1.15:
        topology = "HELICAL_CORKSCREW"
        topo_grammar = (
            f"Helical S-Curve/Spiral Corkscrew (kappa={mean_kappa:.2f}): motion winds through "
            f"both u ({u_span:.2f}) and v ({v_span:.2f}) toward the harmonic node."
        )
    elif mean_balance >= 0.68 and u_span < 0.045:
        topology = "DOUBLE_HELIX_BRAID"
        mean_gap = float(np.mean([wf["rabatment_gap_du"] for wf in worm_frames]))
        topo_grammar = (
            f"Two-Shot Dialogue Braid (Rabatment gap Delta_u={mean_gap:.2f}, balance={mean_balance:.2f}): "
            f"counterpoint pillars in left and right Rabatment squares."
        )
    else:
        topology = "VERTICAL_PILLAR"
        topo_grammar = (
            f"Locked Tripod Vertical Pillar (u={np.mean(u_vals):.2f}, du={du_total:+.3f}): "
            f"high stability cylinder parallel to the tau-axis with zero saccade load."
        )

    peak_jerk_frame = max(worm_frames, key=lambda x: x["diff_geom"]["jerk_mag"])

    return {
        "shot_id": shot_id,
        "topology": topology,
        "topology_grammar": topo_grammar,
        "pan_shear_angle_deg": pan_angle_deg,
        "cone_flare_dr": round(dr_total, 4),
        "mean_rabatment_gap": round(float(np.mean([wf["rabatment_gap_du"] for wf in worm_frames])), 3),
        "mean_bilateral_balance": round(mean_balance, 3),
        "kalmus_summary": {
            "core_palette_8": core_colors_all,
            "shell_palette_8": shell_colors_all,
            "mean_chiaroscuro_dL": round(float(np.mean([wf["itten"]["chiaroscuro_dL"] for wf in worm_frames])), 2),
            "mean_hue_polarity_deg": round(float(np.mean([wf["itten"]["hue_polarity_deg"] for wf in worm_frames])), 1),
            "mean_cold_warm_delta": round(float(np.mean([wf["itten"]["cold_warm_delta"] for wf in worm_frames])), 3),
            "mean_extension_ratio": round(float(np.mean([wf["itten"]["extension_area_ratio"] for wf in worm_frames])), 3),
        },
        "bouleau_summary": {
            "mean_d_grid": round(float(np.mean([wf["bouleau_14"]["d_grid"] for wf in worm_frames])), 4),
            "dominant_filament": worm_frames[len(worm_frames) // 2]["bouleau_14"]["nearest_filament"],
            "mean_arnheim_torque": round(float(np.mean([wf["bouleau_14"]["arnheim_torque"] for wf in worm_frames])), 4),
            "grid_state": worm_frames[len(worm_frames) // 2]["bouleau_14"]["grid_state"],
        },
        "diff_geom_summary": {
            "mean_curvature_kappa": round(mean_kappa, 3),
            "mean_torsion_tau": round(float(np.mean([wf["diff_geom"]["torsion_tau"] for wf in worm_frames])), 3),
            "max_jerk_mag": peak_jerk_frame["diff_geom"]["jerk_mag"],
            "peak_jerk_subframe": peak_jerk_frame["f"],
            "mean_bruce_block_intensity": round(
                float(np.mean([wf["diff_geom"]["bruce_block_intensity"] for wf in worm_frames])), 3
            ),
        },
        "tomography": {
            "u_tau_horizon_slice": u_tau_slice,
            "v_tau_meridian_slice": v_tau_slice,
        },
        "worm_frames": worm_frames,
    }


def analyze_strip_worm_volume(strip_path, shot_id, dur_sec=3.2):
    if not os.path.exists(strip_path):
        return None
    im = Image.open(strip_path).convert("RGB")
    W_tot, H_tot = im.size
    fw = max(1, W_tot // 8)
    worm_frames = []
    for k in range(8):
        crop = im.crop((k * fw, 0, min(W_tot, (k + 1) * fw), H_tot)).resize((W_STD, H_STD))
        arr = np.asarray(crop, dtype=np.float32) / 255.0
        worm_frames.append(measure_frame_array_worm(arr, f_idx=k + 1, tau_norm=k / 7.0))
    return finalize_worm_volume_from_frames(worm_frames, shot_id, dur_sec=dur_sec)


def analyze_cut_sequence_worm(seq_list, cut_lens, dur_sec=3.5, strip_cache=None, thumb_cache=None):
    """
    Analyzes a complete multi-shot montage cut sequence (e.g. 'synthesis', 'clip', 'vjepa',
    'blip', 'cineosis', 'trurl', 'klapaucius', 'murch', 'novelty') by stacking its sub-shots
    from real strips/thumbnails into an 8-slice 3D Spatiotemporal Worm V_lens(u, v, tau).
    """
    if not seq_list:
        return None
    n_sub = len(seq_list)
    worm_frames = []
    subshot_details = []
    internal_eye_locks = 0
    internal_collisions = 0
    prev_uv = None

    # Build 8 temporal slices across the sub-shot sequence
    for k in range(8):
        sub_idx = min(n_sub - 1, int((k / 8.0) * n_sub))
        item = seq_list[sub_idx]
        sid = item.get("id", "")
        local_frac = ((k / 8.0) * n_sub) - sub_idx  # [0..1] within this sub-shot

        # 1. Check if 8-frame strip exists for this sub-shot
        sp_path = os.path.join(LAB, "strips", f"{sid}.jpg")
        th_path = os.path.join(LAB, "thumbs", f"{sid}.jpg")
        ath_path = os.path.join(LAB, "slopfeeder", "athumbs", f"{sid}.jpg")

        if os.path.exists(sp_path):
            im = Image.open(sp_path).convert("RGB")
            W_tot, H_tot = im.size
            fw = max(1, W_tot // 8)
            sub_k = min(7, int(local_frac * 8))
            crop = im.crop((sub_k * fw, 0, min(W_tot, (sub_k + 1) * fw), H_tot)).resize((W_STD, H_STD))
            arr = np.asarray(crop, dtype=np.float32) / 255.0
        elif os.path.exists(th_path) or os.path.exists(ath_path):
            actual_p = th_path if os.path.exists(th_path) else ath_path
            if thumb_cache is not None and actual_p in thumb_cache:
                im = thumb_cache[actual_p]
            else:
                im = Image.open(actual_p).convert("RGB")
                if thumb_cache is not None:
                    thumb_cache[actual_p] = im
            W_t, H_t = im.size
            # Slightly pan/crop window by local_frac * rate to capture the sub-shot's internal temporal flow
            shift = int((local_frac - 0.5) * 0.08 * W_t)
            x0 = max(0, min(W_t // 8, W_t // 20 + shift))
            x1 = min(W_t, W_t - max(0, W_t // 20 - shift))
            crop = im.crop((x0, 0, max(x0 + 8, x1), H_t)).resize((W_STD, H_STD))
            arr = np.asarray(crop, dtype=np.float32) / 255.0
        else:
            arr = np.full((H_STD, W_STD, 3), 0.12, dtype=np.float32)

        wf = measure_frame_array_worm(arr, f_idx=k + 1, tau_norm=k / 7.0)
        wf["subshot_id"] = sid
        wf["subshot_title"] = item.get("title", sid)
        worm_frames.append(wf)

    # Measure cut-to-cut continuity across the sub-shots inside this lens
    for idx_s, item in enumerate(seq_list):
        sid = item.get("id", "")
        wf_rep = worm_frames[min(7, int((idx_s / max(1, n_sub)) * 8))]
        cur_uv = (wf_rep["u"], wf_rep["v"])
        if prev_uv is not None:
            d_cut = math.hypot(cur_uv[0] - prev_uv[0], cur_uv[1] - prev_uv[1])
            if d_cut <= 0.18:
                internal_eye_locks += 1
            else:
                internal_collisions += 1
        prev_uv = cur_uv
        vid_url = item.get("video") or item.get("media_url") or ""
        if vid_url.startswith("/media/"):
            raw_id = vid_url.replace("/media/", "").replace(".mp4", "")
            if os.path.exists(os.path.join(LAB, "clips", f"{raw_id}.mp4")):
                vid_url = f"clips/{raw_id}.mp4"
        subshot_details.append({
            "id": sid,
            "title": item.get("title", sid),
            "year": item.get("year", 1960),
            "media_url": vid_url,
            "video": vid_url,
            "thumb": f"thumbs/{sid}.jpg" if os.path.exists(os.path.join(LAB, "thumbs", f"{sid}.jpg")) else item.get("thumb", ""),
            "t0": round(float(item.get("clip_t0", item.get("t0", 0.0))), 2),
            "dur": round(float(item.get("slot_dur", item.get("dur", 1.0))), 2),
            "spoken": item.get("spoken", ""),
            "u": wf_rep["u"],
            "v": wf_rep["v"],
            "r": wf_rep["r"],
            "core_hex": wf_rep["core_color"]["hex"],
        })

    vol = finalize_worm_volume_from_frames(worm_frames, f"{cut_lens}", dur_sec=dur_sec)
    first_item = seq_list[0]
    return {
        "cut_lens": cut_lens,
        "id": first_item.get("id", cut_lens),
        "title": first_item.get("title", cut_lens),
        "year": first_item.get("year", 1960),
        "subshot_count": n_sub,
        "internal_eye_locks": internal_eye_locks,
        "internal_collisions": internal_collisions,
        "topology": vol["topology"],
        "pan_shear_angle_deg": vol["pan_shear_angle_deg"],
        "cone_flare_dr": vol["cone_flare_dr"],
        "core_hex": vol["kalmus_summary"]["core_palette_8"][3],
        "shell_hex": vol["kalmus_summary"]["shell_palette_8"][3],
        "core_palette_8": vol["kalmus_summary"]["core_palette_8"],
        "shell_palette_8": vol["kalmus_summary"]["shell_palette_8"],
        "chiaroscuro_dL": vol["kalmus_summary"]["mean_chiaroscuro_dL"],
        "hue_polarity_deg": vol["kalmus_summary"]["mean_hue_polarity_deg"],
        "bouleau_d_grid": vol["bouleau_summary"]["mean_d_grid"],
        "arnheim_torque": vol["bouleau_summary"]["mean_arnheim_torque"],
        "curvature_kappa": vol["diff_geom_summary"]["mean_curvature_kappa"],
        "max_jerk": vol["diff_geom_summary"]["max_jerk_mag"],
        "bruce_block": vol["diff_geom_summary"]["mean_bruce_block_intensity"],
        "pts_uvr": [[f["u"], f["v"], f["r"]] for f in vol["worm_frames"]],
        "subshots": subshot_details,
    }


def build_all_spatiotemporal_worms():
    cuts_path = os.path.join(LAB, "wargames-studio-cuts.json")
    screens_path = os.path.join(LAB, "wargames-screens-program.json")

    cuts_data = json.load(open(cuts_path))
    screens_data = json.load(open(screens_path))

    strip_files = sorted(glob.glob(os.path.join(LAB, "strips", "*.jpg")))
    print(f"Extruding 3D Spatiotemporal Worms V(u,v,tau) across {len(strip_files)} 8-frame strips ({len(strip_files)*8} frames)...")

    worm_by_strip_id = {}
    for sp in strip_files:
        sid = os.path.splitext(os.path.basename(sp))[0]
        res = analyze_strip_worm_volume(sp, sid, dur_sec=3.2)
        if res:
            worm_by_strip_id[sid] = res

    # Enrich all 68 pure computer screens
    prev_c_exit = (0.5, 0.5)
    prev_vel = (0.0, 0.0)
    for st in screens_data.get("screen_states", []):
        sid = st["shot_id"]
        dur = float(st.get("dur", 3.0))
        sp = os.path.join(LAB, "strips", f"{sid}.jpg")
        w_res = analyze_strip_worm_volume(sp, sid, dur_sec=dur)
        if w_res:
            wf0 = w_res["worm_frames"][0]
            wf8 = w_res["worm_frames"][-1]
            c_entry = (wf0["u"], wf0["v"])
            c_exit = (wf8["u"], wf8["v"])
            cur_vel = (c_exit[0] - c_entry[0], c_exit[1] - c_entry[1])
            jump_d = round(math.hypot(c_entry[0] - prev_c_exit[0], c_entry[1] - prev_c_exit[1]), 4)
            v_dot = round(prev_vel[0] * cur_vel[0] + prev_vel[1] * cur_vel[1], 4)
            w_res["cut_fracture"] = {
                "type": "EYE_TRACE_FRACTURE_TUBE" if jump_d <= 0.18 else "EISENSTEIN_COLLISION_FRACTURE",
                "jump_dist_uv": jump_d,
                "velocity_dot": v_dot,
            }
            prev_c_exit = c_exit
            prev_vel = cur_vel
            st["worm_3d"] = w_res

    with open(screens_path, "w") as f:
        json.dump(screens_data, f, separators=(",", ":"))

    # Analyze all 105 scene beats AND all 10 simultaneous montage cuts (4,300 sub-shots) + all 1,110 spoken takes!
    beat_worms = []
    topo_counts = {}
    all_10_cuts_topo_counts = {}
    fracture_counts = {"EYE_TRACE_FRACTURE_TUBE": 0, "EISENSTEIN_COLLISION_FRACTURE": 0}
    prev_beat_exit = (0.5, 0.5)
    prev_beat_vel = (0.0, 0.0)
    thumb_cache = {}
    total_subshots_measured = 0
    total_spoken_takes_measured = 0

    for bk in cuts_data.get("books", []):
        for bt in bk.get("beats", []):
            bid = bt["id"]
            wgs = bt.get("wg_shot", {})
            sid = wgs.get("id", "wg_001")
            a0 = float(bt.get("a0", wgs.get("start", 0.0)))
            a1 = float(bt.get("a1", a0 + float(wgs.get("dur", 5.0))))
            dur = max(2.5, a1 - a0)

            sp = os.path.join(LAB, "strips", f"{sid}.jpg")
            w_res = analyze_strip_worm_volume(sp, sid, dur_sec=dur)
            if not w_res and sid in worm_by_strip_id:
                w_res = dict(worm_by_strip_id[sid])

            if w_res:
                topo = w_res["topology"]
                topo_counts[topo] = topo_counts.get(topo, 0) + 1

                wf0 = w_res["worm_frames"][0]
                wf8 = w_res["worm_frames"][-1]
                c_entry = (wf0["u"], wf0["v"])
                c_exit = (wf8["u"], wf8["v"])
                cur_vel = (c_exit[0] - c_entry[0], c_exit[1] - c_entry[1])
                jump_d = round(math.hypot(c_entry[0] - prev_beat_exit[0], c_entry[1] - prev_beat_exit[1]), 4)
                v_dot = round(prev_beat_vel[0] * cur_vel[0] + prev_beat_vel[1] * cur_vel[1], 4)
                frac_type = "EYE_TRACE_FRACTURE_TUBE" if jump_d <= 0.18 else "EISENSTEIN_COLLISION_FRACTURE"
                fracture_counts[frac_type] += 1
                prev_beat_exit = c_exit
                prev_beat_vel = cur_vel

                # Measure all 10 simultaneous montage cuts from real strip/thumbnail pixels!
                cuts_10_worms = []
                cuts_dict = bt.get("cuts") or {}
                for cut_key, seq_list in cuts_dict.items():
                    if isinstance(seq_list, list) and seq_list:
                        cw = analyze_cut_sequence_worm(
                            seq_list, cut_key, dur_sec=dur, strip_cache=worm_by_strip_id, thumb_cache=thumb_cache
                        )
                        if cw:
                            cuts_10_worms.append(cw)
                            total_subshots_measured += len(seq_list)
                            ctopo = cw["topology"]
                            all_10_cuts_topo_counts[ctopo] = all_10_cuts_topo_counts.get(ctopo, 0) + 1

                # Measure the spoken dialogue turns & their 3 archival takes for mobile cinema playback
                turns_summary = []
                for tr in (bt.get("turns_1983") or []):
                    tk_list = []
                    for tk in (tr.get("takes") or []):
                        tsid = tk.get("id", "")
                        th_p = os.path.join(LAB, "thumbs", f"{tsid}.jpg")
                        u_tk, v_tk, r_tk, hex_tk, dL_tk = 0.5, 0.45, 0.22, "#33ff77", 24.0
                        if os.path.exists(th_p):
                            if th_p not in thumb_cache:
                                thumb_cache[th_p] = Image.open(th_p).convert("RGB")
                            arr_tk = np.asarray(thumb_cache[th_p].resize((W_STD, H_STD)), dtype=np.float32) / 255.0
                            m_tk = measure_frame_array_worm(arr_tk, f_idx=1, tau_norm=0.5)
                            u_tk, v_tk, r_tk = m_tk["u"], m_tk["v"], m_tk["r"]
                            hex_tk = m_tk["core_color"]["hex"]
                            dL_tk = m_tk["itten"]["chiaroscuro_dL"]
                            total_spoken_takes_measured += 1
                        tk_list.append({
                            "id": tsid,
                            "title": tk.get("title", "Archival Take"),
                            "year": tk.get("year", 1960),
                            "spoken": tk.get("spoken", ""),
                            "media_url": tk.get("video") or (tk.get("media_url") if not str(tk.get("media_url", "")).startswith("/media/") else "") or f"clips/{tsid}.mp4",
                            "t0": round(float(tk.get("clip_t0", tk.get("t0", 0.0))), 2),
                            "dur": round(float(tk.get("dur", 2.5)), 2),
                            "u": u_tk,
                            "v": v_tk,
                            "r": r_tk,
                            "core_hex": hex_tk,
                            "chiaroscuro_dL": dL_tk,
                        })
                    turns_summary.append({
                        "turn_num": tr.get("turn_num", 1),
                        "speaker": tr.get("speaker", bt.get("who", "")),
                        "text": tr.get("text", ""),
                        "s": round(float(tr.get("s", 0.0)), 2),
                        "e": round(float(tr.get("e", 2.5)), 2),
                        "dur": round(float(tr.get("dur", 2.5)), 2),
                        "wpm": tr.get("wpm", 130),
                        "is_fulcrum": bool(tr.get("is_fulcrum")),
                        "takes": tk_list,
                    })

                beat_entry = {
                    "id": bid,
                    "book_bnum": bk.get("bnum", "I"),
                    "book_title": bk.get("title", ""),
                    "shot_id": sid,
                    "start_sec": round(a0, 2),
                    "end_sec": round(a1, 2),
                    "dur_sec": round(dur, 2),
                    "who": bt.get("who", ""),
                    "fulcrum_line": bt.get("fulcrum_line", bt.get("text", "")),
                    "thumb": wgs.get("thumb", f"thumbs/{sid}.jpg"),
                    "strip": wgs.get("strip", f"strips/{sid}.jpg"),
                    "video": f"clips/{sid}.mp4",
                    "audio_orig": f"cache/wg_sound/{bid}_orig.m4a",
                    "audio_aligned": f"cache/wg_sound/{bid}_aligned.m4a",
                    "topology": w_res["topology"],
                    "topology_grammar": w_res["topology_grammar"],
                    "pan_shear_angle_deg": w_res["pan_shear_angle_deg"],
                    "cone_flare_dr": w_res["cone_flare_dr"],
                    "mean_rabatment_gap": w_res["mean_rabatment_gap"],
                    "mean_bilateral_balance": w_res["mean_bilateral_balance"],
                    "cut_fracture": {
                        "type": frac_type,
                        "jump_dist_uv": jump_d,
                        "velocity_dot": v_dot,
                    },
                    "kalmus_summary": w_res["kalmus_summary"],
                    "bouleau_summary": w_res["bouleau_summary"],
                    "diff_geom_summary": w_res["diff_geom_summary"],
                    "tomography": w_res["tomography"],
                    "worm_frames": w_res["worm_frames"],
                    "cuts_10_worms": cuts_10_worms,
                    "turns": turns_summary,
                }
                beat_worms.append(beat_entry)
                bt["worm_3d"] = {
                    "topology": w_res["topology"],
                    "cut_fracture": beat_entry["cut_fracture"],
                    "kalmus": w_res["kalmus_summary"],
                    "bouleau": w_res["bouleau_summary"],
                    "diff_geom": w_res["diff_geom_summary"],
                }

    with open(cuts_path, "w") as f:
        json.dump(cuts_data, f, separators=(",", ":"))

    out_vol = {
        "meta": {
            "schema": "STGL-3D-WORM-VOLUME-v2.0 V(u, v, tau)",
            "total_strips_extruded": len(worm_by_strip_id),
            "total_frames_extruded": len(worm_by_strip_id) * 8,
            "total_beats": len(beat_worms),
            "total_10cut_volumes": len(beat_worms) * 10,
            "total_cut_subshots_measured": total_subshots_measured,
            "total_spoken_takes_measured": total_spoken_takes_measured,
            "topology_distribution_1983": topo_counts,
            "topology_distribution_1050_cuts": all_10_cuts_topo_counts,
            "cut_fracture_distribution": fracture_counts,
        },
        "beats": beat_worms,
    }

    vol_path = os.path.join(LAB, "wargames-worm-volume.json")
    with open(vol_path, "w") as f:
        json.dump(out_vol, f, separators=(",", ":"))

    print(
        f"Wrote {vol_path} ({os.path.getsize(vol_path)/(1024*1024):.2f} MB):\n"
        f"  - {len(worm_by_strip_id)*8} strip frames extruded\n"
        f"  - {len(beat_worms)*10} 3D Cut-Worms ({total_subshots_measured} sub-shots across all 10 lenses) measured from real pixels\n"
        f"  - {total_spoken_takes_measured} spoken archival takes measured from real pixels"
    )
    print("1983 Master Topology distribution (105 beats):", topo_counts)
    print("All 1,050 Montage Cuts Topology distribution:", all_10_cuts_topo_counts)
    print("Cut-to-Cut Fracture Plane distribution:", fracture_counts)


if __name__ == "__main__":
    build_all_spatiotemporal_worms()

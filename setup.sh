#!/bin/sh
# Re-create the Python pipeline environment: lab/.venv with SAM 2 (reuses system torch/open_clip/opencv if present)
# and the SAM 2.1 small checkpoint from Meta (~185 MB). The lab itself needs only python3 + a browser.
set -e
cd "$(dirname "$0")/lab"
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -q "git+https://github.com/facebookresearch/sam2.git" open_clip_torch opencv-python scikit-learn pillow numpy
mkdir -p models
[ -s models/sam2.1_hiera_small.pt ] || curl -fL -o models/sam2.1_hiera_small.pt \
  https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt
echo "ok — run e.g.: .venv/bin/python analyze.py   (see README for the pipeline order)"

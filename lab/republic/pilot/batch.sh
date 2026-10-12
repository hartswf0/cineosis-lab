#!/bin/sh
# each episode: voices, pictures and citizens, the score, then the film twice (scored, and voices only)
cd "$(dirname "$0")/../.."
for n in "$@"; do
  echo "== ep$n $(date +%T)"
  republic/.tts/bin/python republic/pilot/tts.py ep$n > /dev/null 2>&1 || { echo "ep$n tts failed"; continue; }
  .venv/bin/python republic/pilot/pick.py ep$n 2>&1 | grep "narr ·\|chorus ·\|Error\|Trace" 
  .venv/bin/python score/fit.py pilot ep$n 2>&1 | grep "@" | sed 's/^/   /'
  republic/.tts/bin/python republic/pilot/render.py ep$n --score 2>&1 | grep "mp4\|Error\|Trace"
  republic/.tts/bin/python republic/pilot/render.py ep$n 2>&1 | grep "mp4\|Error\|Trace"
done
echo "== lane done $(date +%T)"

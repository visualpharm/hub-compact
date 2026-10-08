#!/bin/sh
# Screenshots of every demo screen at phone, tablet and desktop widths: dev/shots.sh <port> <out-dir>
port=${1:-1100}; out=${2:-/tmp/compact-shots}; mkdir -p "$out"
for r in s/hub s/billing s/mobile-app s/web-shop sessions schedule settings; do
  n=$(echo "$r" | tr '/' '-')
  hub shot "http://127.0.0.1:$port/#/$r" --widths 390,820,1440 --wait 4000 --out "$out/$n.png" >/dev/null 2>&1
done
ls "$out" | wc -l

#!/usr/bin/env bash
# Record the demo and mux the narration onto it.
#
#   ./record_demo.sh record    # capture your screen for 3 minutes
#   ./record_demo.sh mux       # lay narration_full.mp3 over the capture
#   ./record_demo.sh check     # verify the final file
#
# Requires ffmpeg. Works on Linux (X11) and macOS. On Windows, use OBS to
# record screen.mkv, then run the mux step under WSL or Git Bash.

set -euo pipefail

DURATION=180
RAW="screen_raw.mkv"
NARRATION="narration_full.mp3"
FINAL="demo_final.mp4"

case "${1:-}" in

record)
  echo "Recording ${DURATION}s. Follow narration_cuesheet.md — the cue times"
  echo "are printed there. Press q to stop early."
  echo
  echo "CHECK BEFORE YOU START: no API key visible anywhere on screen."
  echo
  read -rp "Press Enter to begin in 5 seconds... "
  sleep 5

  case "$(uname -s)" in
    Linux)
      ffmpeg -y -f x11grab -framerate 30 -video_size 1920x1080 -i "${DISPLAY:-:0}" \
        -t "$DURATION" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$RAW"
      ;;
    Darwin)
      # List devices first with: ffmpeg -f avfoundation -list_devices true -i ""
      ffmpeg -y -f avfoundation -framerate 30 -i "1:none" \
        -t "$DURATION" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$RAW"
      ;;
    *)
      echo "Unsupported OS for automatic capture. Record with OBS to $RAW, then run: $0 mux"
      exit 1
      ;;
  esac
  echo "Captured $RAW"
  ;;

mux)
  [[ -f "$RAW" ]] || { echo "Missing $RAW. Record first, or drop your OBS capture here."; exit 1; }
  [[ -f "$NARRATION" ]] || { echo "Missing $NARRATION. Run: python build_narration.py"; exit 1; }

  # -shortest trims to whichever track ends first, so a slightly long capture
  # is cut to the narration rather than trailing into silence.
  ffmpeg -y -i "$RAW" -i "$NARRATION" \
    -c:v libx264 -preset medium -crf 21 -pix_fmt yuv420p \
    -c:a aac -b:a 192k \
    -map 0:v:0 -map 1:a:0 -shortest \
    "$FINAL"
  echo "Wrote $FINAL"
  ;;

check)
  [[ -f "$FINAL" ]] || { echo "No $FINAL yet."; exit 1; }
  echo "Duration: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL")s"
  ffprobe -v error -show_entries stream=codec_type,codec_name,width,height \
    -of default=noprint_wrappers=1 "$FINAL"
  SIZE=$(du -h "$FINAL" | cut -f1)
  echo "Size: $SIZE"
  echo
  echo "Confirm: under 3:00, both video and audio streams present, text legible."
  ;;

*)
  echo "Usage: $0 {record|mux|check}"
  exit 1
  ;;
esac

# DIY Veo (rugby match camera)

Goal: Veo-style auto-panning match footage of Dexter's rugby for ~£0-180, no £75/month subscription. Two cameras film the whole pitch, software stitches a panorama and an AI "camera" crops/pans to follow play.

## Software: reco video-stitcher
- Open source (AGPL), Rust rewrite: https://github.com/reco-project/video-stitcher (repo cloned at `/home/jarvis/projects/video-stitcher` for reference)
- Prebuilt GUI app, no build needed. Latest v0.5.4 (Aug 2026):
  - Mac (Apple Silicon): use the **ffmpeg9 build**: https://github.com/reco-project/video-stitcher/releases/download/v0.5.4/reco-gui-v0.5.4-macos-arm64-ffmpeg9.tar.gz, plus `brew install ffmpeg` (Homebrew ships FFmpeg 9.0.2 as of Oct 2026). The plain `macos-arm64` build links libavutil.60 (FFmpeg 8) and dyld-aborts on Rob's Mac (hit 05 Oct 2026).
  - AI tracking model (same page): `yolo26n.onnx`
- Workflow per QUICKSTART: load left+right video, Auto Calibrate (feature match + audio sync), fix lens via Gyroflow profile browser if warped, set ROI polygon per camera, export 1080p with AI tracking (Field mode, detection interval 15).
- Jarvis's box CANNOT be the render node: LXC has no GPU and the prebuilt Linux CLI needs FFmpeg 6 (libavutil58) vs Debian 13's FFmpeg 7. Processing lives on a Mac/desktop with a real GPU. (Verified 05 Oct 2026.)

## Hardware decision (as of 05 Oct 2026)
- Pilot: two iPhones (11+), ULTRA-WIDE lens (~120° each), 4K30, locked exposure (Blackmagic Camera app), case off, airplane mode, ~45GB free each. This is literally what Veo Go sells.
- If pilot convinces: 2x used GoPro Hero 7 Black (~£75-90 each, stabilisation OFF, 4:3 ratio). Hero 5 Black is the absolute floor; Hero 7 White/Silver NOT supported by Gyroflow.

## Test ladder (agreed 05 Oct 2026)
1. **Sofa test (free, ~30 min):** reco-gui on the Mac + two phones filming the garden simultaneously from one spot, ultra-wide, 30-60s, ~40% overlap between views. Auto Calibrate → stitched panorama proves the whole pipeline before any spend.
2. **Motion test:** kids + ball in the park, same setup, export with yolo26n AI tracking in Field mode. Proves the auto-pan.
3. **Mount build LAST:** the calibration from tests 1-2 gives the real design numbers (angle between phones for good overlap, so the crossbar geometry) before cutting anything. Likely form: two phone clamps on a short crossbar at a fixed toe-out angle, on a painter's pole / sturdy tripod, 2-3m up, plus shade for heat.
4. **Match day:** only after the club conversation (see safeguarding below).

## Safeguarding (kids' rugby)
Systematic filming needs: club permission, opposition consent per fixture, parental consent on file both teams (one no-photo flag = no filming). Sharing = private links only (GDPR). Route: pitch it to Dexter's club as their DIY Veo, club handles consents. Templates: Billericay RFC + Chelmsford RFC policies.

## Open items
- [ ] Rob: download reco-gui on the Mac, run sofa test
- [ ] Lens profile: try Gyroflow's iPhone ultra-wide profile first; only do manual checkerboard calibration if the stitch looks warped
- [ ] Pitch to Dexter's club before any match-day filming

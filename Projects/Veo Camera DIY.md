# Veo Camera DIY

Idea sparked 04 Oct 2026 watching Dexter's rugby match (a Veo-camera-equipped pitch had automated tracking/panning). Goal: build an open-source equivalent instead of paying for a Veo subscription.

## The plan
- Software: [reco-project/video-stitcher](https://github.com/reco-project/video-stitcher) (AGPL, Rust, GPU-accelerated) — stitches two overlapping camera feeds into one panorama, runs YOLO ball/player tracking with anticipatory lookahead to simulate the pan/zoom. Post-processing only, not live (live stitching needs cameras cabled into a GPU box via GStreamer).
- Hardware mirrors the original Veo design (two 4K cameras in a 3D-printed box on a 4m pole): two action cams angled to cover 180°, 3D-printed mount (Rob designs/prints it), telescopic pole.
- Sync is automatic (audio cross-correlation + IMU), no need to start cameras simultaneously.
- Workflow: record both cams through the match → feed mp4s to stitcher at home → stitched + tracked output video to share.

## Camera choice: action cams, not phones
iPhones overheat/throttle over an 80-min match and have no Gyroflow lens profile. Action cams are first-class in the stitcher's calibration (Gyroflow profile database is GoPro/DJI/Insta360-centric), run off a USB-C power bank, lock exposure, and are rain-proof.

**Tier decision (discussed 04 Oct):**
- £20 no-name (B&M/Amazon deal) cams: **rejected**. The Veo effect crops ~1/4 of the frame for the virtual pan, and these cams' "4K" is interpolated from a much cheaper sensor — cropped output would be unusably soft. No Gyroflow profile either, so manual checkerboard calibration needed.
- ~£50-60 each (Akaso Brave 4 / EK7000 tier): workable cheap trial to prove the pipeline, known brand with Gyroflow profiles, but still partly-interpolated 4K.
- ~£100-130 each, used GoPro Hero 9/10: the real floor for Veo-quality output — native 4K sensor, native lens profiles, exposure lock, rain-proof.

Rob's leaning: trial on Akasos if cost-sensitive, but go straight to used GoPros if this becomes a every-Sunday habit.

## Shopping list (not yet bought)
2x action cams (tier TBD), 2x 128GB SD cards, a USB-C power bank, a telescopic pole, one evening of Rob 3D-printing the mount. Rob said this one's fine to put on the public Shopping List (not Wishlist) when it's greenlit.

## Status
Idea stage, not yet actioned — no purchases made as of 04 Oct 2026.

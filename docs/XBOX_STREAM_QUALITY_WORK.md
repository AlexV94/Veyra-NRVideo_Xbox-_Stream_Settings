# Xbox stream-quality controls — development handoff

**Status:** incomplete prototype; do not distribute as a compiled build yet.

## What is implemented

- Xbox dialog requests 1080p (default) or 1440p (experimental), persisted locally and applied on reconnect.
- Settings travel from the QML model into the Xbox session descriptor.
- Xbox dialog displays live *measured* encoded video Mbps, video size, received/decoded FPS, WebRTC RTT, locally dropped frames, and decoder errors.
- Existing video path, H.264 codec, GPU decoding and frame generation are intentionally unchanged.

## Required final source edit before compiling

The new `WebRtcSession::setPreferredVideoSize` declaration and call require a definition.
Run `python scripts/xbox/apply_stream_dimensions.py` in the repository checkout.
The helper strictly matches Veyra 2.2.0's existing `src/xbox/WebRtcSession.cpp`, adds the method definition, and replaces the fixed dimension announcement with the chosen dimensions. Review `git diff` before building.

**Important:** The preference changes the dimensions sent in the existing client configuration message. It does **not** force Xbox encoding resolution, FPS, bitrate, codec, or a new WebRTC profile. The console can ignore it. There is currently no Xbox bitrate-request override.

## Local build and validation

1. Clone your fork and check out `feature/xbox-stream-quality-controls`.
2. Run the helper above and inspect source changes.
3. Follow the upstream Visual Studio 2022 / CMake and dependency setup; build with `VEYRA_ENABLE_XBOX=ON`.
4. Run `veyra_xbox_tests` if that target exists in your configuration, plus QML/UI checks.
5. Test the existing 1080p path first, with all enhancements disabled. Confirm stable received video, accurate measured Mbps, and controller paired directly to the console (gamepad passthrough off).
6. Test experimental 1440p only after 1080p is stable. Verify the *received* size and bitrate, not just the requested values.

## Future work

- Confirm whether modern Xbox `VideoPreference` and resolution-update messages are supported, then implement them behind capability checks.
- Add a requested-bitrate option **only** if console protocol support can be demonstrated; otherwise keep it as auto-negotiated.
- Add true RTP packet-loss measurements. Existing `dropped` and `decodeErrors` are local processing counters, **not network packet loss**.
- Windows compilation and testing with a real Series S and connected RTX 4070 Super are still outstanding.

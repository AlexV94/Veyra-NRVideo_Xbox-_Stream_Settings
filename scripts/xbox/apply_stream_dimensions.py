#!/usr/bin/env python3
"""Finish the Xbox WebRTC dimension-preference edit in a local Veyra checkout.

This small patch is intentionally strict: it refuses to change unfamiliar versions.
Run once from the repository root, then inspect the diff before building.

    python scripts/xbox/apply_stream_dimensions.py
"""
from pathlib import Path

path = Path("src/xbox/WebRtcSession.cpp")
text = path.read_text(encoding="utf-8")
anchor = "WebRtcSession::~WebRtcSession() { close(); }"
implementation = """WebRtcSession::~WebRtcSession() { close(); }

void WebRtcSession::setPreferredVideoSize(uint32_t width, uint32_t height) {
    if ((width == 1920 && height == 1080) || (width == 2560 && height == 1440)) {
        preferredVideoWidth_ = width;
        preferredVideoHeight_ = height;
    } else {
        preferredVideoWidth_ = 1920;
        preferredVideoHeight_ = 1080;
    }
}
"""
original = '''        {"horizontal", 1920}, {"vertical", 1080}, {"preferredWidth", 1920}, {"preferredHeight", 1080},
        {"safeAreaLeft", 0}, {"safeAreaTop", 0}, {"safeAreaRight", 1920}, {"safeAreaBottom", 1080}, {"supportsCustomResolution", true}}));'''
replacement = '''        {"horizontal", preferredVideoWidth_}, {"vertical", preferredVideoHeight_},
        {"preferredWidth", preferredVideoWidth_}, {"preferredHeight", preferredVideoHeight_},
        {"safeAreaLeft", 0}, {"safeAreaTop", 0},
        {"safeAreaRight", preferredVideoWidth_}, {"safeAreaBottom", preferredVideoHeight_},
        {"supportsCustomResolution", true}}));'''
if text.count(anchor) != 1 or text.count(original) != 1:
    raise SystemExit("Unrecognized WebRtcSession.cpp revision or patch already applied; no changes made.")
updated = text.replace(anchor, implementation).replace(original, replacement)
path.write_text(updated, encoding="utf-8")
print("Updated", path, "— review git diff, then compile and test.")

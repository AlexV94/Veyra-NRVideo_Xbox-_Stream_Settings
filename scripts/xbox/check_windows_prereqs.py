#!/usr/bin/env python3
"""Read-only Windows prerequisites report for the custom Veyra Xbox build.

Run from the repository root:
    py -3.11 scripts/xbox/check_windows_prereqs.py

The script never downloads, installs or alters anything.
It does not inspect game accounts or Xbox credentials.
"""
from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
import subprocess

repo = Path(__file__).resolve().parents[2]
checks: list[tuple[str, bool, str]] = []


def add(label: str, good: bool, detail: str = "") -> None:
    checks.append((label, good, detail))
    print(f"{'OK     ' if good else 'MISSING'} {label}" + (f": {detail}" if detail else ""))


def cmd(name: str) -> str:
    found = shutil.which(name)
    add(name, bool(found), found or "not on PATH")
    return found or ""


print("Veyra Xbox Windows build prerequisites (read-only)\n")
add("Windows 11 x64", platform.system() == "Windows" and platform.machine().lower() in ("amd64", "x86_64"),
    platform.platform())
cmd("git")
cmd("cmake")
cmd("ninja")
cmd("py")

pf86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
vswhere = pf86 / "Microsoft" / "Visual Studio" / "Installer" / "vswhere.exe"
vs = ""
if vswhere.is_file():
    try:
        vs = subprocess.check_output(
            [str(vswhere), "-latest", "-products", "*", "-requires",
             "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
            text=True, timeout=10
        ).strip()
    except (OSError, subprocess.SubprocessError):
        pass
vsroot = Path(vs) if vs else Path("X:/nonexistent-visual-studio")
add("Visual Studio 2022 MSVC x64", bool(vs) and "2022" in str(vsroot)
    and (vsroot / "VC/Auxiliary/Build/vcvars64.bat").is_file(), vs or "select Desktop development with C++")

qt = Path(os.environ.get("VEYRA_QT_ROOT", r"C:\Qt\6.8.3\msvc2022_64"))
add("Qt 6.8.3 MSVC2022 64-bit",
    (qt / "lib/cmake/Qt6/Qt6Config.cmake").is_file(), str(qt))

vcpkg = Path(os.environ.get("VCPKG_ROOT", r"C:\vcpkg"))
static = vcpkg / "installed/x64-windows-static"
add("vcpkg x64-windows-static prefix", static.is_dir(), str(static))
for label, relative in (
    ("libdatachannel", "share/libdatachannel"),
    ("Opus", "share/opus"),
    ("nlohmann-json", "share/nlohmann-json"),
    ("OpenSSL", "share/openssl"),
):
    folder = static / relative
    add("vcpkg " + label, folder.is_dir(), str(folder))

ffmpeg = Path(os.environ.get("VEYRA_FFMPEG_ROOT", r"C:\veyra-deps\installed\x64-windows"))
add("FFmpeg 9.x header prefix", (ffmpeg / "include/libavformat/avformat.h").is_file(), str(ffmpeg))
add("FFmpeg 9.x runtime", (ffmpeg / "bin/avcodec-63.dll").is_file(), str(ffmpeg / "bin"))
add("FFmpeg patched build provenance", False, "manually verify upstream pinned/patched FFmpeg build")

nvcodec = Path(os.environ.get("VEYRA_NVENC_HEADERS_ROOT",
    str(repo / "third_party_local/nvidia/nv-codec-headers-13.0")))
add("nv-codec-headers n13.0.19.0",
    (nvcodec / "include/ffnvcodec/nvEncodeAPI.h").is_file(), str(nvcodec))

dlss = Path(os.environ.get("VEYRA_DLSS_SDK_ROOT", str(repo / "third_party_local/nvidia/DLSS_SDK_310.7.0")))
nvof = Path(os.environ.get("VEYRA_NVOF_SDK_ROOT",
    str(repo / "third_party_local/nvidia/Optical_Flow_SDK_5.0.7")))
print("\nOptional, but required for Veyra's NVIDIA enhancement / frame-generation build:")
add("NVIDIA DLSS SDK", (dlss / "include/nvsdk_ngx.h").is_file(), str(dlss))
add("NVIDIA Optical Flow SDK",
    (nvof / "NvOFInterface/nvOpticalFlowCommon.h").is_file(), str(nvof))

print("\nSource patch status:")
source = repo / "src/xbox/WebRtcSession.cpp"
if source.is_file():
    body = source.read_text(encoding="utf-8")
    finished = (
        "void WebRtcSession::setPreferredVideoSize(" in body
        and '{"horizontal", preferredVideoWidth_}' in body
    )
    add("Handshake patch applied", finished,
        "run: py -3.11 scripts/xbox/apply_stream_dimensions.py" if not finished else "present")
else:
    add("Source checkout", False, str(source))

print("\nThis is a readiness checklist, not proof that dependencies are compatible or the build succeeds.")
print("Keep proprietary SDKs and console/account credentials out of Git.")

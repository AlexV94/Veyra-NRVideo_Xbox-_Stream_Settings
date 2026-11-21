# Windows 11 build walkthrough — Xbox Remote Play prototype

This documents a **development build**, not a supported release. Do not overwrite an installed Veyra. Start with 1080p and no extra effects. All changes live on branch `feature/xbox-stream-quality-controls`.

## 1. Install Windows tools

Install **Visual Studio 2022 Build Tools**, selecting Desktop development with C++ (MSVC v143, Windows SDK and CMake tools). This repository's build wrapper expects Visual Studio **2022**, not 2026.

Install Git, Python 3.11, CMake (>=3.24) and Ninja. In an interactive PowerShell terminal:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.11 -e
winget install --id Kitware.CMake -e
winget install --id Ninja-build.Ninja -e
```

Install **Qt 6.8.3 / MSVC 2022 64-bit** through Qt Online Installer, including Qt Quick/QML. The upstream release documents Qt 6.8.3 specifically; a more recent Qt may require changes.

## 2. Clone fork and finish the handshake edit

```powershell
New-Item -ItemType Directory -Force C:\dev | Out-Null
Set-Location C:\dev
git clone --branch feature/xbox-stream-quality-controls --single-branch https://github.com/AlexV94/Veyra-NRVideo_Xbox-_Stream_Settings.git Veyra-Xbox
Set-Location C:\dev\Veyra-Xbox
py -3.11 scripts/xbox/apply_stream_dimensions.py
git diff --check
git diff -- src/xbox/WebRtcSession.cpp
py -3.11 scripts/xbox/check_windows_prereqs.py
```

The patch helper fails rather than guessing if the file differs from the expected Veyra 2.2.0 revision. When applied, `WebRtcSession::setPreferredVideoSize()` accepts only 1080p and 1440p and uses those preferences in the existing dimensions-changed message.

**Not yet an Xbox bitrate override.** The console may ignore the requested video size. Never treat client preferences as proof of actual encoder output.

## 3. Source dependencies (not included in a normal Git clone)

Required for an Xbox + GUI build:

- **FFmpeg 9.0.1** compatible with Veyra's source: CMake expects a prefix with headers, import libraries, and the proper runtime DLLs. The mainline source documents a patched FFmpeg provenance. A retail/portable Veyra install does not include the developer headers and import libraries.
- **nv-codec-headers n13.0.19.0**: required by `veyra_sinks` when FFmpeg is enabled; see `VEYRA_NVENC_HEADERS_ROOT`.
- **vcpkg x64-windows-static dependencies:** `libdatachannel`, `nlohmann-json`, `opus`, and OpenSSL; note the project overlay at `scripts/xbox/vcpkg-overlay`. Match the upstream `scripts/xbox/dependency-lock.json` and source/versions where applicable.
- **Qt 6.8.3 MSVC 2022 64-bit** and Qt QML/Quick modules; CMake requires `VEYRA_BUILD_QML_UI=ON` for this UI.
- **For the production NVIDIA effects pipeline:** the matching NVIDIA DLSS SDK and NVIDIA Optical Flow SDK are staged outside Git. Proprietary assets must be obtained from their authorized publishers. An Xbox-only/reduced build can disable these effects for initial diagnostics.

Avoid copying assorted DLLs from unrelated program installations into the build directory. Some of the upstream dependency steps rely on pinned or patched versions and are not a one-command standard-vcpkg install.

## 4. Configure the first reduced Xbox build

After the prerequisite report identifies the actual prefixes, open **x64 Native Tools Command Prompt for VS 2022** and run the following in `C:\dev\Veyra-Xbox`, substituting real, verified paths for the FFmpeg, NVENC, Qt and vcpkg prefixes:

```bat
cmake -S . -B out\build\xbox-dev -G Ninja ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DVEYRA_ENABLE_XBOX=ON ^
  -DVEYRA_BUILD_QML_UI=ON ^
  -DVEYRA_ENABLE_REMOTEPLAY=OFF ^
  -DVEYRA_ENABLE_EXPERIMENTAL_DLSSNR=OFF ^
  -DVEYRA_ENABLE_LIBDOVI=OFF ^
  -DVEYRA_ENABLE_DEINTERLACE=OFF ^
  "-DVEYRA_FFMPEG_ROOT=C:/veyra-deps/installed/x64-windows" ^
  "-DVEYRA_NVENC_HEADERS_ROOT=C:/dev/nv-codec-headers-13.0" ^
  "-DCMAKE_PREFIX_PATH=C:/Qt/6.8.3/msvc2022_64;C:/vcpkg/installed/x64-windows-static"
```

This is an **initial diagnostic configuration**, not a command known to succeed on a fresh machine: the upstream CMake graph has many conditional targets. The FFmpeg prefix must be a matching development build, not merely a folder containing retail program DLLs. Disabling `VEYRA_ENABLE_EXPERIMENTAL_DLSSNR` means the NVIDIA FG/NR functionality in the distribution is not reproduced by this reduced build.

## 5. Compile protocol tests, then the UI

```bat
cmake --build out\build\xbox-dev --target veyra_xbox_tests --parallel 2
out\build\xbox-dev\veyra_xbox_tests.exe
cmake --build out\build\xbox-dev --target veyra_qml_ui --parallel 2
```

The test executable exercises offline Xbox protocol scenarios. It is not a live Xbox video-quality test. To run the UI, stage matching Qt/FFmpeg/OpenSSL runtime files and shaders in a separate folder according to upstream packaging; do not overwrite the installed Veyra executable or mix DLLs from mismatched releases.

## 6. Real Xbox acceptance

1. First verify the default 1080p request connects, receives picture and sound, and does not add encoder/block artifacts.
2. Reopen the Xbox settings dialog to inspect actual stream resolution, Mbps, received FPS, decoded FPS, RTT, local drops and decoder errors.
3. With the controller paired directly to Xbox, disable PC controller forwarding in Veyra.
4. Re-test at 1440p only if 1080p stays stable. Revert if blocky frames or stalls reappear.
5. Never interpret locally dropped frames and decode errors as WebRTC packet-loss statistics.
6. Restore NVIDIA SDK-backed effects in a separate validation stage after the baseline Xbox build; verify 30 unique game frames -> 60 display FPS without claiming lower input latency.

## Getting help with the first failure

Attach the text output of `check_windows_prereqs.py` and the **first CMake configure error**, if any. Do not share Microsoft sign-in tokens, console account files, or other credentials.

See `docs/BUILD_2.2.0.md`, `docs/DEVELOPMENT.md`, `cmake/VeyraXbox.cmake` and `docs/XBOX_STREAM_CORRUPTION_RECOVERY.md` for upstream build constraints.

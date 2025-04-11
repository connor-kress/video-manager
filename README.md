# Video Management Suite

This is a collection of scripts to manage video download and playback. I do not
condone piracy in any way. Never download videos without explicit permission
from the applicable copyright holders.

## System Dependencies

This project requires the following external programs to be installed on your
system:

1.  **FFmpeg:** Used for video processing tasks.
    - **Debian/Ubuntu:** `sudo apt update && sudo apt install ffmpeg`
    - **macOS (using Homebrew):** `brew install ffmpeg`
    - **Fedora:** `sudo dnf install ffmpeg`
    - **Windows:** Download from the official FFmpeg website and add it to your
      system's PATH.

2.  **mpv:** Used for video playback.
    - **Debian/Ubuntu:** `sudo apt update && sudo apt install mpv`
    - **macOS (using Homebrew):** `brew install mpv`
    - **Fedora:** `sudo dnf install mpv`
    - **Windows:** Download from the official mpv website or use a package
      manager like Chocolatey (`choco install mpv`).

3.  **notify-send/terminal-notifier:** Used for sending desktop notifications.
    - **Debian/Ubuntu:** `sudo apt update && sudo apt install libnotify-bin`
    - **macOS (using Homebrew):** `brew install terminal-notifier`
    - **Fedora:** `sudo dnf install libnotify`
    - **Windows:** TODO (PowerShell or `win10toast`)

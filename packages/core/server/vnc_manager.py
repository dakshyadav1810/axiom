"""
VNC Manager — manages Xvfb + x11vnc + websockify for browser streaming.

Launches a virtual display (Xvfb), a VNC server (x11vnc), and a
WebSocket-to-TCP bridge (websockify) so the React frontend can embed
a live noVNC viewer of the headless Playwright browser.

On macOS (development) the full Xvfb stack is unavailable.  In that
case the manager falls back to a CDP-based screencast that streams
JPEG frames over a plain WebSocket — no VNC required.

Usage:
    vnc = VNCManager()
    await vnc.start()                # Starts Xvfb + x11vnc + websockify
    display = vnc.get_display()      # ":99"
    ws_url  = vnc.get_ws_url()       # "ws://localhost:6080"
    ...
    await vnc.stop()
"""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
import signal
import subprocess
import sys
from typing import Optional


class VNCManager:
    """
    Lifecycle manager for the virtual-display + VNC + websockify stack.

    Linux:
        Xvfb  →  x11vnc  →  websockify  →  noVNC (frontend)

    macOS (fallback):
        CDP screencast streamed via the /ws/browser-stream WebSocket
        handled separately in main.py — VNCManager is skipped.
    """

    def __init__(
        self,
        display: int = 99,
        width: int = 1280,
        height: int = 720,
        depth: int = 24,
        vnc_port: int = 5900,
        ws_port: int = 6080,
    ):
        self.display = display
        self.width = width
        self.height = height
        self.depth = depth
        self.vnc_port = vnc_port
        self.ws_port = ws_port

        self._xvfb_proc: Optional[subprocess.Popen] = None
        self._x11vnc_proc: Optional[subprocess.Popen] = None
        self._websockify_proc: Optional[subprocess.Popen] = None

        self._running = False

    # ── public API ──────────────────────────────────────────────

    @staticmethod
    def is_linux() -> bool:
        return platform.system() == "Linux"

    @staticmethod
    def is_available() -> bool:
        """Check whether the VNC stack binaries are installed."""
        if not VNCManager.is_linux():
            return False
        return all(
            shutil.which(cmd) is not None
            for cmd in ("Xvfb", "x11vnc", "websockify")
        )

    def _probe_existing(self) -> bool:
        """Return True if a websockify process is already listening on ws_port.

        docker-entrypoint.sh starts Xvfb + x11vnc + websockify before the
        Python server is launched.  Rather than trying to re-spawn everything
        (which would fail with 'port already in use'), we just detect whether
        the stack is already up and mark ourselves as running.
        """
        import socket
        try:
            with socket.create_connection(("localhost", self.ws_port), timeout=1):
                return True
        except OSError:
            return False

    async def start(self) -> None:
        """Launch Xvfb → x11vnc → websockify (Linux only)."""
        if self._running:
            return

        if not self.is_linux():
            print("[vnc] Skipping VNC stack (macOS detected — using CDP fallback)")
            return

        # If docker-entrypoint.sh already started the stack, just adopt it.
        if self._probe_existing():
            self._running = True
            print(f"[vnc] Detected existing VNC stack on port {self.ws_port} — adopted")
            return

        if not self.is_available():
            missing = [
                cmd for cmd in ("Xvfb", "x11vnc", "websockify")
                if shutil.which(cmd) is None
            ]
            print(f"[vnc] Missing binaries: {', '.join(missing)}")
            print("[vnc] Install with: sudo apt-get install xvfb x11vnc && pip install websockify")
            return

        display_str = f":{self.display}"
        resolution = f"{self.width}x{self.height}x{self.depth}"

        # 1. Start Xvfb
        self._xvfb_proc = subprocess.Popen(
            ["Xvfb", display_str, "-screen", "0", resolution, "-ac", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Give Xvfb a moment to initialize
        await asyncio.sleep(0.5)
        if self._xvfb_proc.poll() is not None:
            print(f"[vnc] Xvfb failed to start (exit {self._xvfb_proc.returncode})")
            return
        print(f"[vnc] Xvfb started on {display_str} ({resolution})")

        # 2. Start x11vnc (no password, localhost only)
        self._x11vnc_proc = subprocess.Popen(
            [
                "x11vnc",
                "-display", display_str,
                "-rfbport", str(self.vnc_port),
                "-nopw",
                "-localhost",
                "-forever",       # Don't exit after first client disconnects
                "-shared",        # Allow multiple connections
                "-noxdamage",     # Compatibility
                "-cursor", "most",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await asyncio.sleep(0.5)
        if self._x11vnc_proc.poll() is not None:
            print(f"[vnc] x11vnc failed to start (exit {self._x11vnc_proc.returncode})")
            await self.stop()
            return
        print(f"[vnc] x11vnc started on port {self.vnc_port}")

        # 3. Start websockify (WebSocket bridge)
        self._websockify_proc = subprocess.Popen(
            [
                "websockify",
                "--web", "/usr/share/novnc",  # Serve noVNC web client (optional)
                str(self.ws_port),
                f"localhost:{self.vnc_port}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await asyncio.sleep(0.5)
        if self._websockify_proc.poll() is not None:
            print(f"[vnc] websockify failed to start (exit {self._websockify_proc.returncode})")
            await self.stop()
            return
        print(f"[vnc] websockify bridging ws://localhost:{self.ws_port} → localhost:{self.vnc_port}")

        self._running = True
        print(f"[vnc] VNC stack ready — connect noVNC to ws://localhost:{self.ws_port}")

    async def stop(self) -> None:
        """Terminate the VNC stack in reverse order."""
        for name, proc in [
            ("websockify", self._websockify_proc),
            ("x11vnc", self._x11vnc_proc),
            ("Xvfb", self._xvfb_proc),
        ]:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    print(f"[vnc] {name} stopped")
                except Exception as e:
                    print(f"[vnc] Error stopping {name}: {e}")

        self._xvfb_proc = None
        self._x11vnc_proc = None
        self._websockify_proc = None
        self._running = False

    def get_display(self) -> str:
        """Return the DISPLAY env var string (e.g. ':99')."""
        return f":{self.display}"

    def get_ws_url(self) -> str:
        """Return the websockify WebSocket URL."""
        return f"ws://localhost:{self.ws_port}"

    @property
    def running(self) -> bool:
        return self._running

"""
Spawn and manage the Node.js TUI process from Python CLI.

This module handles:
1. Checking if Node.js and TUI dependencies are available
2. Building the TUI if needed
3. Spawning the TUI process with proper environment variables
4. Handling process lifecycle and signals
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class TUISpawner:
    """Manages spawning and lifecycle of the Ink TUI process."""

    def __init__(self, api_url: str = "http://localhost:8000", user_id: str = "default"):
        """
        Initialize the TUI spawner.

        Args:
            api_url: URL of the FastAPI backend
            user_id: Current user ID
        """
        self.api_url = api_url
        self.user_id = user_id
        self.tui_dir = Path(__file__).parent.parent.parent.parent / "cli" / "tui"
        self.node_bin = self._find_node()
        self.process: subprocess.Popen | None = None

    @staticmethod
    def _find_node() -> str | None:
        """Find Node.js executable in system PATH."""
        return shutil.which("node")

    def is_available(self) -> bool:
        """Check if TUI can be launched (Node.js available, dependencies installed)."""
        if not self.node_bin:
            return False

        # Check if TUI directory exists
        if not self.tui_dir.exists():
            return False

        # Check if node_modules exists
        node_modules = self.tui_dir / "node_modules"
        if not node_modules.exists():
            logger.warning("TUI node_modules not found. Run 'npm install' in cli/tui/")
            return False

        return True

    def _ensure_built(self) -> None:
        """Ensure TUI is built."""
        if not self.node_bin:
            raise RuntimeError("Node.js not found in PATH")

        # Check if dist exists
        dist = self.tui_dir / "dist"
        if not dist.exists():
            logger.info("Building TUI...")
            # Find npm executable
            npm_bin = shutil.which("npm")
            if not npm_bin:
                raise RuntimeError("npm not found in PATH. Install Node.js 18+ to use TUI mode.")

            result = subprocess.run(  # nosec B603
                [npm_bin, "run", "build"],
                cwd=self.tui_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.error(f"TUI build failed: {result.stderr}")
                raise RuntimeError("Failed to build TUI")

    def spawn(self) -> subprocess.Popen:
        """
        Spawn the TUI process.

        Returns:
            subprocess.Popen: The spawned process

        Raises:
            RuntimeError: If Node.js is not available or TUI setup failed
        """
        if not self.node_bin:
            raise RuntimeError("Node.js not found. Install Node.js 18+ to use TUI mode.")

        if not self.is_available():
            raise RuntimeError(
                "TUI is not properly set up. Run: npm install && npm run build in cli/tui/"
            )

        # Ensure built
        self._ensure_built()

        # Prepare environment
        env = os.environ.copy()
        env["SKILL_FLEET_API_URL"] = self.api_url
        env["SKILL_FLEET_USER_ID"] = self.user_id

        # Start the TUI process
        try:
            self.process = subprocess.Popen(  # nosec B603
                [self.node_bin, str(self.tui_dir / "dist" / "index.js")],
                env=env,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                cwd=self.tui_dir,
            )
            logger.debug(f"TUI spawned with PID {self.process.pid}")
            return self.process
        except Exception as e:
            logger.error(f"Failed to spawn TUI: {e}")
            raise RuntimeError(f"Failed to spawn TUI: {e}") from e

    def wait(self) -> int:
        """
        Wait for the TUI process to exit and return exit code.

        Returns:
            int: Process exit code
        """
        if not self.process:
            return 1

        try:
            return self.process.wait()
        except KeyboardInterrupt:
            logger.debug("TUI interrupted by user")
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            return 130  # Standard exit code for Ctrl+C

    def run(self) -> int:
        """
        Spawn and wait for TUI to complete.

        Returns:
            int: Process exit code
        """
        try:
            self.spawn()
            return self.wait()
        except Exception as e:
            logger.error(f"TUI error: {e}")
            return 1

    def terminate(self) -> None:
        """Terminate the TUI process gracefully."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.error(f"Error terminating TUI: {e}")


def spawn_tui(
    api_url: str = "http://localhost:8000",
    user_id: str = "default",
    force_no_tui: bool = False,
) -> int:
    """
    Spawn the Ink TUI if available, otherwise return 0 to continue with fallback.

    Args:
        api_url: FastAPI backend URL
        user_id: Current user ID
        force_no_tui: If True, skip TUI and return 0

    Returns:
        int: Exit code (0 = no TUI, 1 = error, other = TUI exit code)
    """
    if force_no_tui:
        logger.debug("TUI disabled via --no-tui flag")
        return 0

    spawner = TUISpawner(api_url=api_url, user_id=user_id)

    if not spawner.is_available():
        logger.debug("TUI not available, falling back to simple chat")
        return 0

    try:
        return spawner.run()
    except Exception as e:
        logger.warning(f"TUI failed, falling back to simple chat: {e}")
        return 0

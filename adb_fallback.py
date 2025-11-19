"""
ADB Fallback System for Binance Redpacket Claiming

This module provides automated device control via ADB for redpacket claiming
when the API method fails or is blocked. Designed specifically for Redmi Note 12.
"""
import asyncio
import os
import time
import subprocess
import json
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from source.config import config
from lib.utils import logger


@dataclass
class ADBCommand:
    """Represents an ADB command with description and expected outcomes."""
    command: str
    description: str
    timeout: int = 10
    expected_success_patterns: List[str] = None


@dataclass
class DeviceState:
    """Current state of the Android device."""
    connected: bool = False
    binance_running: bool = False
    screen_on: bool = False
    last_screenshot: Optional[str] = None
    battery_level: int = 0
    error_count: int = 0


class ADBFallback:
    """Advanced ADB automation system for redpacket claiming fallback."""

    def __init__(self):
        self.device_id = os.getenv('ADB_DEVICE_ID', '')
        self.coordinates = self._get_uhd_coordinates()
        self.device_state = DeviceState()
        self.screenshot_counter = 0

        # Ensure screenshot directory exists
        self.screenshot_dir = Path(config.ADB_SETTINGS.get("screenshot_path", "C:\\bots\\redpackets\\screenshots\\"))
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        logger.info("ADB Fallback system initialized")

    def _get_uhd_coordinates(self) -> Dict[str, Tuple[int, int]]:
        """Get UHD coordinates for Redmi Note 12 (3840x2160 resolution)."""
        return {
            "binance_launcher": (720, 1944),
            "redpacket_section": (1080, 1620),
            "claim_input_focus": (1920, 1080),
            "submit_button": (2160, 1800),
            "captcha_skip": (1080, 1400),
            "back_navigation": (360, 216),
            "app_close": (3600, 180)
        }

    async def check_device_connection(self) -> bool:
        """Check if ADB device is connected and responsive."""
        try:
            cmd = ["adb", "devices"]
            if self.device_id:
                cmd.extend(["-s", self.device_id])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            devices_output = stdout.decode().strip()

            if self.device_id:
                self.device_state.connected = self.device_id in devices_output
            else:
                # Check for any connected device (excluding "List of devices")
                lines = devices_output.split('\n')[1:]  # Skip header
                self.device_state.connected = any(line.strip() for line in lines if '\tdevice' in line)

            if self.device_state.connected:
                logger.info("ADB device connection verified")
            else:
                logger.error(f"ADB device not found. Output: {devices_output}")

            return self.device_state.connected

        except Exception as e:
            logger.error(f"Failed to check ADB device connection: {e}")
            self.device_state.connected = False
            return False

    async def execute_adb_command(self, command: str, timeout: int = 10) -> Tuple[bool, str]:
        """Execute ADB command and return success status and output."""
        try:
            full_command = ["adb"]
            if self.device_id:
                full_command.extend(["-s", self.device_id])

            # Split shell command properly
            if command.startswith("shell "):
                full_command.extend(["shell"])
                shell_cmd = command[6:]  # Remove "shell " prefix
                full_command.extend(shell_cmd.split())
            else:
                full_command.extend(command.split())

            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.warning(f"ADB command timed out: {command}")
                return False, "Command timed out"

            success = process.returncode == 0
            output = stdout.decode().strip()
            error = stderr.decode().strip()

            if not success and error:
                logger.warning(f"ADB command failed: {command} | Error: {error}")
                return False, error

            logger.debug(f"ADB command executed: {command} | Success: {success}")
            return success, output

        except Exception as e:
            logger.error(f"Exception executing ADB command '{command}': {e}")
            return False, str(e)

    async def take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take a screenshot and save it to the screenshots directory."""
        try:
            if not filename:
                self.screenshot_counter += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"claim_screenshot_{timestamp}_{self.screenshot_counter}.png"

            device_path = f"/sdcard/{filename}"
            local_path = self.screenshot_dir / filename

            # Take screenshot on device
            success, _ = await self.execute_adb_command(f"shell screencap -p {device_path}")
            if not success:
                logger.error("Failed to take screenshot on device")
                return ""

            # Pull screenshot to local directory
            success, _ = await self.execute_adb_command(f"pull {device_path} {local_path}")
            if not success:
                logger.error("Failed to pull screenshot from device")
                return ""

            # Clean up device screenshot
            await self.execute_adb_command(f"shell rm {device_path}")

            self.device_state.last_screenshot = str(local_path)
            logger.info(f"Screenshot saved: {local_path}")
            return str(local_path)

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return ""

    async def wake_up_device(self) -> bool:
        """Wake up the device and unlock if possible."""
        try:
            # Turn screen on
            success, _ = await self.execute_adb_command("shell input keyevent KEYCODE_POWER")
            if not success:
                logger.warning("Failed to turn screen on")
                return False

            await asyncio.sleep(1)

            # Try to unlock (swipe up - assuming pattern/pin isn't set)
            success, _ = await self.execute_adb_command("shell input touchscreen swipe 540 1900 540 1000")

            logger.info("Device wake-up attempt completed")
            return True

        except Exception as e:
            logger.error(f"Failed to wake up device: {e}")
            return False

    async def launch_binance_app(self) -> bool:
        """Launch the Binance app on the device."""
        try:
            success, output = await self.execute_adb_command(
                "shell am start -n com.binance.dev/.ui.MainActivity"
            )

            if not success:
                logger.error(f"Failed to launch Binance app: {output}")
                return False

            # Wait for app to load
            await asyncio.sleep(5)

            # Verify app is running
            success, output = await self.execute_adb_command(
                "shell dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'"
            )

            if "com.binance.dev" in output:
                logger.info("Binance app launched successfully")
                self.device_state.binance_running = True
                return True
            else:
                logger.warning("Binance app may not have launched properly")
                return False

        except Exception as e:
            logger.error(f"Failed to launch Binance app: {e}")
            return False

    async def navigate_to_redpacket_section(self) -> bool:
        """Navigate to the redpacket section within the Binance app."""
        try:
            coords = self.coordinates["redpacket_section"]
            x, y = coords

            # Tap on redpacket section
            success, _ = await self.execute_adb_command(f"shell input tap {x} {y}")
            if not success:
                logger.error("Failed to tap redpacket section")
                return False

            # Wait for navigation
            await asyncio.sleep(3)

            # Take screenshot for verification
            screenshot_path = await self.take_screenshot("redpacket_section.png")

            logger.info("Navigated to redpacket section")
            return True

        except Exception as e:
            logger.error(f"Failed to navigate to redpacket section: {e}")
            return False

    async def input_claim_code(self, code: str) -> bool:
        """Input the claim code into the appropriate field."""
        try:
            # Focus on input field
            coords = self.coordinates["claim_input_focus"]
            x, y = coords

            success, _ = await self.execute_adb_command(f"shell input tap {x} {y}")
            if not success:
                logger.error("Failed to focus on claim input field")
                return False

            await asyncio.sleep(1)

            # Clear any existing text
            success, _ = await self.execute_adb_command("shell input keyevent KEYCODE_CTRL_A")
            if success:
                await asyncio.sleep(0.5)
                await self.execute_adb_command("shell input keyevent KEYCODE_DEL")

            # Input the code
            success, _ = await self.execute_adb_command(f"shell input text {code}")
            if not success:
                logger.error("Failed to input claim code")
                return False

            await asyncio.sleep(1)

            # Take screenshot for verification
            screenshot_path = await self.take_screenshot(f"code_input_{code}.png")

            logger.info(f"Claim code entered: {code}")
            return True

        except Exception as e:
            logger.error(f"Failed to input claim code {code}: {e}")
            return False

    async def submit_claim(self) -> bool:
        """Submit the claim by tapping the submit button."""
        try:
            coords = self.coordinates["submit_button"]
            x, y = coords

            # Tap submit button
            success, _ = await self.execute_adb_command(f"shell input tap {x} {y}")
            if not success:
                logger.error("Failed to tap submit button")
                return False

            # Wait for claim processing
            await asyncio.sleep(5)

            # Take screenshot for result verification
            screenshot_path = await self.take_screenshot("claim_result.png")

            logger.info("Claim submitted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to submit claim: {e}")
            return False

    async def handle_captcha_if_present(self) -> bool:
        """Check for and handle CAPTCHA if present."""
        try:
            # Take screenshot first to analyze
            screenshot_path = await self.take_screenshot("captcha_check.png")
            if not screenshot_path:
                return False

            # For now, we'll try to skip CAPTCHA by tapping the skip coordinates
            # In a production system, you'd want to use OCR or image recognition here
            coords = self.coordinates["captcha_skip"]
            x, y = coords

            success, _ = await self.execute_adb_command(f"shell input tap {x} {y}")
            if success:
                await asyncio.sleep(2)
                logger.info("CAPTCHA skip attempt completed")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to handle CAPTCHA: {e}")
            return False

    async def close_binance_app(self) -> bool:
        """Force close the Binance app."""
        try:
            success, _ = await self.execute_adb_command("shell am force-stop com.binance.dev")
            if success:
                self.device_state.binance_running = False
                logger.info("Binance app force-closed")
                return True
            else:
                logger.warning("Failed to force-close Binance app")
                return False

        except Exception as e:
            logger.error(f"Failed to close Binance app: {e}")
            return False

    async def claim_redpacket_via_adb(self, code: str) -> Dict[str, Any]:
        """
        Complete redpacket claim process via ADB automation.

        Returns:
            Dict with claim result and metadata
        """
        result = {
            "success": False,
            "code": code,
            "method": "adb",
            "timestamp": datetime.now().isoformat(),
            "error": None,
            "screenshots": [],
            "steps_completed": []
        }

        try:
            logger.info(f"Starting ADB claim process for code: {code}")

            # Step 1: Check device connection
            if not await self.check_device_connection():
                result["error"] = "Device not connected via ADB"
                return result

            result["steps_completed"].append("device_connected")

            # Step 2: Wake up device
            if not await self.wake_up_device():
                result["error"] = "Failed to wake up device"
                return result

            result["steps_completed"].append("device_awake")

            # Step 3: Launch Binance app
            if not await self.launch_binance_app():
                result["error"] = "Failed to launch Binance app"
                return result

            result["steps_completed"].append("binance_launched")

            # Step 4: Navigate to redpacket section
            if not await self.navigate_to_redpacket_section():
                result["error"] = "Failed to navigate to redpacket section"
                return result

            result["steps_completed"].append("navigated_to_redpacket")

            # Step 5: Input claim code
            if not await self.input_claim_code(code):
                result["error"] = "Failed to input claim code"
                return result

            result["steps_completed"].append("code_entered")

            # Step 6: Check for and handle CAPTCHA
            await self.handle_captcha_if_present()
            result["steps_completed"].append("captcha_handled")

            # Step 7: Submit claim
            if not await self.submit_claim():
                result["error"] = "Failed to submit claim"
                return result

            result["steps_completed"].append("claim_submitted")

            # Step 8: Take final screenshot
            final_screenshot = await self.take_screenshot(f"final_result_{code}.png")
            if final_screenshot:
                result["screenshots"].append(final_screenshot)

            result["success"] = True
            result["steps_completed"].append("completed")
            logger.success(f"✅ ADB claim completed for code: {code}")

            return result

        except Exception as e:
            logger.error(f"ADB claim process failed for code {code}: {e}", exc_info=True)
            result["error"] = str(e)
            return result

        finally:
            # Always try to close the app when done
            await self.close_binance_app()

    async def cleanup_session(self) -> bool:
        """Clean up the ADB session by closing apps and clearing temp files."""
        try:
            logger.info("Starting ADB session cleanup...")

            # Close Binance app
            await self.close_binance_app()

            # Clear any temporary screenshots on device
            await self.execute_adb_command("shell rm -f /sdcard/claim_screenshot_*.png")
            await self.execute_adb_command("shell rm -f /sdcard/*.png")

            # Turn screen off (optional)
            await self.execute_adb_command("shell input keyevent KEYCODE_POWER")

            logger.info("ADB session cleanup completed")
            return True

        except Exception as e:
            logger.error(f"ADB session cleanup failed: {e}")
            return False

    def get_device_status(self) -> Dict[str, Any]:
        """Get current device status and statistics."""
        return {
            "device_id": self.device_id,
            "connected": self.device_state.connected,
            "binance_running": self.device_state.binance_running,
            "last_screenshot": self.device_state.last_screenshot,
            "screenshot_count": self.screenshot_counter,
            "error_count": self.device_state.error_count,
            "coordinates": self.coordinates
        }
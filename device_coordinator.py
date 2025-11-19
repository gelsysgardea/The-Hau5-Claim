"""
Device Coordinator for ADB Fallback System

This module manages the device state, coordination, and decision making
for when to trigger ADB fallback vs API method.
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from adb_fallback import ADBFallback
from source.config import config
from lib.utils import logger


class FallbackTrigger(Enum):
    """Reasons for triggering ADB fallback."""
    API_FAILURES = "api_failures"
    BAN_DETECTED = "ban_detected"
    SESSION_EXPIRED = "session_expired"
    MANUAL_TRIGGER = "manual_trigger"
    RATE_LIMIT = "rate_limit"


class DeviceStatus(Enum):
    """Device operational status."""
    OFFLINE = "offline"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class FallbackMetrics:
    """Metrics for ADB fallback performance."""
    total_claims: int = 0
    successful_claims: int = 0
    failed_claims: int = 0
    avg_claim_time: float = 0.0
    last_claim_time: Optional[datetime] = None
    consecutive_failures: int = 0
    device_uptime: float = 0.0


@dataclass
class DeviceMetrics:
    """Device health and performance metrics."""
    battery_level: int = 100
    temperature: float = 0.0
    memory_usage: float = 0.0
    app_crashes: int = 0
    screenshot_count: int = 0
    last_heartbeat: Optional[datetime] = None


class DeviceCoordinator:
    """
    Advanced device coordinator that manages ADB fallback decisions,
    device health monitoring, and performance optimization.
    """

    def __init__(self):
        self.adb_fallback = ADBFallback()
        self.device_status = DeviceStatus.OFFLINE
        self.fallback_enabled = True
        self.auto_recovery_enabled = True

        # Metrics tracking
        self.fallback_metrics = FallbackMetrics()
        self.device_metrics = DeviceMetrics()
        self.trigger_history: List[Dict[str, Any]] = []

        # State management
        self.last_device_check = 0
        self.last_successful_claim = None
        self.maintenance_mode_until = 0
        self.rate_limit_until = 0

        # Configuration
        self.max_consecutive_failures = config.ADB_SETTINGS.get("max_consecutive_failures", 3)
        self.device_check_interval = config.ADB_SETTINGS.get("device_check_interval", 60)
        self.maintenance_cooldown = config.ADB_SETTINGS.get("maintenance_cooldown", 300)  # 5 minutes

        logger.info("Device Coordinator initialized")

    async def initialize_device(self) -> bool:
        """Initialize device connection and verify readiness."""
        try:
            logger.info("Initializing device for ADB fallback...")

            # Check device connection
            if not await self.adb_fallback.check_device_connection():
                logger.error("Device not connected - ADB fallback unavailable")
                self.device_status = DeviceStatus.OFFLINE
                return False

            # Wake up device and verify responsiveness
            if not await self.adb_fallback.wake_up_device():
                logger.error("Device not responding to wake-up commands")
                self.device_status = DeviceStatus.ERROR
                return False

            # Test screenshot capability
            test_screenshot = await self.adb_fallback.take_screenshot("device_test.png")
            if not test_screenshot:
                logger.warning("Screenshot test failed - may indicate permission issues")

            # Update device status
            self.device_status = DeviceStatus.READY
            self.last_device_check = time.time()
            self.device_metrics.last_heartbeat = datetime.now()

            logger.info("Device initialized and ready for ADB fallback")
            return True

        except Exception as e:
            logger.error(f"Device initialization failed: {e}", exc_info=True)
            self.device_status = DeviceStatus.ERROR
            return False

    async def should_trigger_fallback(self, trigger: FallbackTrigger, context: Dict[str, Any] = None) -> bool:
        """
        Determine if ADB fallback should be triggered based on trigger type and system state.

        Args:
            trigger: Reason for considering fallback
            context: Additional context for decision making

        Returns:
            True if fallback should be triggered
        """
        if not self.fallback_enabled:
            logger.debug("ADB fallback is disabled")
            return False

        # Check if device is ready
        if self.device_status != DeviceStatus.READY:
            # Try to initialize device if it's offline
            if self.device_status == DeviceStatus.OFFLINE:
                if not await self.initialize_device():
                    logger.warning("Cannot trigger fallback - device not available")
                    return False
            else:
                logger.warning(f"Cannot trigger fallback - device status: {self.device_status}")
                return False

        # Check if we're in maintenance mode
        if time.time() < self.maintenance_mode_until:
            logger.debug("Device in maintenance mode - skipping fallback")
            return False

        # Check if we're rate limited
        if time.time() < self.rate_limit_until:
            logger.debug("Rate limit active - skipping fallback")
            return False

        # Trigger-specific logic
        if trigger == FallbackTrigger.API_FAILURES:
            consecutive_failures = context.get("consecutive_failures", 0)
            if consecutive_failures >= self.max_consecutive_failures:
                logger.info(f"Triggering fallback due to {consecutive_failures} consecutive API failures")
                return True

        elif trigger == FallbackTrigger.BAN_DETECTED:
            risk_score = context.get("risk_score", 0)
            if risk_score >= config.ANTI_BAN_SETTINGS["ban_detection_signals"]["risk_score_threshold"]:
                logger.info(f"Triggering fallback due to high risk score: {risk_score}")
                return True

        elif trigger == FallbackTrigger.SESSION_EXPIRED:
            logger.info("Triggering fallback due to session expiration")
            return True

        elif trigger == FallbackTrigger.RATE_LIMIT:
            logger.info("Triggering fallback due to API rate limiting")
            return True

        elif trigger == FallbackTrigger.MANUAL_TRIGGER:
            logger.info("Manual fallback trigger received")
            return True

        return False

    async def execute_fallback_claim(self, code: str, trigger: FallbackTrigger, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute ADB fallback claim with full coordination and monitoring.

        Args:
            code: Redpacket code to claim
            trigger: Reason for fallback
            context: Additional context

        Returns:
            Dict with claim result and metrics
        """
        start_time = time.time()
        claim_result = {
            "success": False,
            "code": code,
            "trigger": trigger.value,
            "method": "adb_fallback",
            "timestamp": datetime.now().isoformat(),
            "device_status": self.device_status.value,
            "execution_time": 0,
            "error": None,
            "recovery_actions": []
        }

        try:
            # Update device status to busy
            self.device_status = DeviceStatus.BUSY
            logger.info(f"🔄 Executing ADB fallback claim for code: {code}")

            # Record trigger
            self._record_trigger(trigger, context)

            # Ensure device is ready
            if self.device_status != DeviceStatus.READY:
                if not await self.initialize_device():
                    claim_result["error"] = "Device initialization failed"
                    return claim_result
                claim_result["recovery_actions"].append("device_reinitialized")

            # Execute the claim via ADB
            adb_result = await self.adb_fallback.claim_redpacket_via_adb(code)

            # Update metrics
            self.fallback_metrics.total_claims += 1
            execution_time = time.time() - start_time
            claim_result["execution_time"] = execution_time

            if adb_result.get("success", False):
                # Successful claim
                self.fallback_metrics.successful_claims += 1
                self.fallback_metrics.consecutive_failures = 0
                self.last_successful_claim = datetime.now()
                claim_result["success"] = True
                claim_result["adb_result"] = adb_result

                logger.success(f"✅ ADB fallback claim successful: {code} (took {execution_time:.1f}s)")

                # Apply success delay
                await asyncio.sleep(2)  # Brief pause after successful claim

            else:
                # Failed claim
                self.fallback_metrics.failed_claims += 1
                self.fallback_metrics.consecutive_failures += 1
                claim_result["error"] = adb_result.get("error", "Unknown ADB error")
                claim_result["adb_result"] = adb_result

                logger.error(f"❌ ADB fallback claim failed: {code} - {claim_result['error']}")

                # Auto-recovery actions
                if self.auto_recovery_enabled:
                    await self._attempt_auto_recovery(claim_result)

            # Update average claim time
            self._update_average_claim_time(execution_time)

            # Update device status
            self.device_status = DeviceStatus.READY

            return claim_result

        except Exception as e:
            logger.error(f"ADB fallback execution failed for code {code}: {e}", exc_info=True)
            self.fallback_metrics.failed_claims += 1
            self.fallback_metrics.consecutive_failures += 1

            claim_result["error"] = str(e)
            claim_result["execution_time"] = time.time() - start_time
            self.device_status = DeviceStatus.ERROR

            # Emergency cleanup
            if self.auto_recovery_enabled:
                await self._emergency_cleanup()
                claim_result["recovery_actions"].append("emergency_cleanup")

            return claim_result

        finally:
            # Update metrics
            self.fallback_metrics.last_claim_time = datetime.now()
            self._update_device_metrics()

    async def _attempt_auto_recovery(self, claim_result: Dict[str, Any]) -> None:
        """Attempt automatic recovery after failed claim."""
        try:
            recovery_actions = claim_result["recovery_actions"]
            consecutive_failures = self.fallback_metrics.consecutive_failures

            logger.info(f"Attempting auto-recovery after {consecutive_failures} consecutive failures")

            # Recovery strategy based on failure count
            if consecutive_failures <= 2:
                # Light recovery: cleanup session
                await self.adb_fallback.cleanup_session()
                recovery_actions.append("session_cleanup")
                await asyncio.sleep(5)

            elif consecutive_failures <= 4:
                # Medium recovery: device restart
                logger.info("Performing medium recovery - device cleanup")
                await self.adb_fallback.cleanup_session()
                await asyncio.sleep(10)

                # Try to reinitialize device
                if await self.initialize_device():
                    recovery_actions.append("device_reinitialized")
                else:
                    recovery_actions.append("device_reinit_failed")

            else:
                # Heavy recovery: maintenance mode
                logger.warning("Too many consecutive failures - entering maintenance mode")
                self.device_status = DeviceStatus.MAINTENANCE
                self.maintenance_mode_until = time.time() + self.maintenance_cooldown
                recovery_actions.append("maintenance_mode")

                # Full cleanup
                await self.adb_fallback.cleanup_session()
                await self._emergency_cleanup()

        except Exception as e:
            logger.error(f"Auto-recovery failed: {e}")

    async def _emergency_cleanup(self) -> None:
        """Perform emergency cleanup of device state."""
        try:
            logger.info("Performing emergency cleanup...")

            # Force close all relevant apps
            await self.adb_fallback.execute_adb_command("shell am force-stop com.binance.dev")

            # Clear temporary files
            await self.adb_fallback.execute_adb_command("shell rm -f /sdcard/claim_*.png")
            await self.adb_fallback.execute_adb_command("shell rm -f /sdcard/tmp_*.png")

            # Reset device state
            await self.adb_fallback.execute_adb_command("shell input keyevent KEYCODE_HOME")

            logger.info("Emergency cleanup completed")

        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")

    def _record_trigger(self, trigger: FallbackTrigger, context: Dict[str, Any] = None) -> None:
        """Record fallback trigger for analytics."""
        trigger_record = {
            "timestamp": datetime.now().isoformat(),
            "trigger": trigger.value,
            "context": context or {},
            "device_status": self.device_status.value,
            "consecutive_failures": self.fallback_metrics.consecutive_failures
        }

        self.trigger_history.append(trigger_record)

        # Keep only last 50 triggers
        if len(self.trigger_history) > 50:
            self.trigger_history = self.trigger_history[-50:]

    def _update_average_claim_time(self, execution_time: float) -> None:
        """Update rolling average claim time."""
        total_claims = self.fallback_metrics.total_claims
        if total_claims == 1:
            self.fallback_metrics.avg_claim_time = execution_time
        else:
            # Rolling average with more weight on recent claims
            weight = min(0.3, 1.0 / total_claims)
            self.fallback_metrics.avg_claim_time = (
                (1 - weight) * self.fallback_metrics.avg_claim_time + weight * execution_time
            )

    async def _update_device_metrics(self) -> None:
        """Update device health metrics."""
        try:
            # Get battery level
            success, output = await self.adb_fallback.execute_adb_command(
                "shell dumpsys battery | grep level"
            )
            if success and "level:" in output:
                try:
                    battery_level = int(output.split("level:")[1].strip())
                    self.device_metrics.battery_level = battery_level
                except (ValueError, IndexError):
                    pass

            # Update screenshot count
            self.device_metrics.screenshot_count = self.adb_fallback.screenshot_counter
            self.device_metrics.last_heartbeat = datetime.now()

        except Exception as e:
            logger.debug(f"Failed to update device metrics: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for dashboard."""
        return {
            "device_status": self.device_status.value,
            "fallback_enabled": self.fallback_enabled,
            "auto_recovery_enabled": self.auto_recovery_enabled,
            "fallback_metrics": {
                "total_claims": self.fallback_metrics.total_claims,
                "successful_claims": self.fallback_metrics.successful_claims,
                "failed_claims": self.fallback_metrics.failed_claims,
                "success_rate": (
                    self.fallback_metrics.successful_claims / max(1, self.fallback_metrics.total_claims) * 100
                ),
                "avg_claim_time": self.fallback_metrics.avg_claim_time,
                "consecutive_failures": self.fallback_metrics.consecutive_failures,
                "last_claim_time": (
                    self.fallback_metrics.last_claim_time.isoformat()
                    if self.fallback_metrics.last_claim_time
                    else None
                )
            },
            "device_metrics": {
                "battery_level": self.device_metrics.battery_level,
                "screenshot_count": self.device_metrics.screenshot_count,
                "last_heartbeat": (
                    self.device_metrics.last_heartbeat.isoformat()
                    if self.device_metrics.last_heartbeat
                    else None
                )
            },
            "maintenance": {
                "maintenance_mode": time.time() < self.maintenance_mode_until,
                "maintenance_remaining": max(0, self.maintenance_mode_until - time.time()),
                "rate_limit_active": time.time() < self.rate_limit_until,
                "rate_limit_remaining": max(0, self.rate_limit_until - time.time())
            },
            "recent_triggers": self.trigger_history[-10:]  # Last 10 triggers
        }

    async def health_check(self) -> bool:
        """Perform comprehensive health check of the device coordinator."""
        try:
            # Check if device is connected
            if not await self.adb_fallback.check_device_connection():
                self.device_status = DeviceStatus.OFFLINE
                return False

            # Check device responsiveness
            if not await self.adb_fallback.wake_up_device():
                self.device_status = DeviceStatus.ERROR
                return False

            # Update device status
            if self.device_status == DeviceStatus.OFFLINE:
                self.device_status = DeviceStatus.READY

            await self._update_device_metrics()
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.device_status = DeviceStatus.ERROR
            return False

    def enable_fallback(self, enabled: bool = True) -> None:
        """Enable or disable ADB fallback."""
        self.fallback_enabled = enabled
        logger.info(f"ADB fallback {'enabled' if enabled else 'disabled'}")

    def enable_auto_recovery(self, enabled: bool = True) -> None:
        """Enable or disable automatic recovery."""
        self.auto_recovery_enabled = enabled
        logger.info(f"Auto-recovery {'enabled' if enabled else 'disabled'}")

    async def shutdown(self) -> None:
        """Graceful shutdown of the device coordinator."""
        try:
            logger.info("Shutting down device coordinator...")

            # Cleanup device session
            await self.adb_fallback.cleanup_session()

            # Update status
            self.device_status = DeviceStatus.OFFLINE

            logger.info("Device coordinator shutdown completed")

        except Exception as e:
            logger.error(f"Device coordinator shutdown failed: {e}")
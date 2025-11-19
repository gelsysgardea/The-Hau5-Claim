"""
Enhanced Main Entry Point for The-Hau5-Claim

This is the enhanced version that integrates ADB fallback capabilities
with the main redpacket claiming system.
"""
import asyncio
import sys
import os
import argparse
import signal
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from source.config import config
from lib.utils import logger, setup_logging
from device_coordinator import DeviceCoordinator, FallbackTrigger
from adb_fallback import ADBFallback


class EnhancedHau5Claim:
    """Enhanced Hau5 Claim system with ADB fallback integration."""

    def __init__(self):
        self.device_coordinator = DeviceCoordinator()
        self.adb_fallback = ADBFallback()
        self.running = False
        self.shutdown_requested = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Enhanced Hau5 Claim system initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
        self.running = False

    async def initialize(self) -> bool:
        """Initialize the enhanced system."""
        try:
            logger.info("Initializing Enhanced Hau5 Claim system...")

            # Initialize device coordinator
            if not await self.device_coordinator.initialize_device():
                logger.error("Failed to initialize device coordinator")
                return False

            logger.success("Enhanced Hau5 Claim system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    async def claim_redpacket_fallback(self, code: str, trigger_reason: str = "manual") -> Dict[str, Any]:
        """
        Claim redpacket using ADB fallback method.

        Args:
            code: 8-character redpacket code
            trigger_reason: Reason for using fallback

        Returns:
            Dict with claim result
        """
        try:
            # Convert string trigger to enum
            trigger_map = {
                "manual": FallbackTrigger.MANUAL_TRIGGER,
                "api_failures": FallbackTrigger.API_FAILURES,
                "ban_detected": FallbackTrigger.BAN_DETECTED,
                "session_expired": FallbackTrigger.SESSION_EXPIRED,
                "rate_limit": FallbackTrigger.RATE_LIMIT
            }

            trigger = trigger_map.get(trigger_reason, FallbackTrigger.MANUAL_TRIGGER)

            # Check if fallback should be triggered
            if not await self.device_coordinator.should_trigger_fallback(trigger):
                return {
                    "success": False,
                    "error": f"Fallback not available for trigger: {trigger_reason}",
                    "code": code,
                    "method": "adb_fallback_denied"
                }

            # Execute fallback claim
            result = await self.device_coordinator.execute_fallback_claim(code, trigger)

            return result

        except Exception as e:
            logger.error(f"ADB fallback claim failed for code {code}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "code": code,
                "method": "adb_fallback_error"
            }

    async def test_device_connectivity(self) -> Dict[str, Any]:
        """Test device connectivity and capabilities."""
        try:
            logger.info("Testing device connectivity...")

            test_results = {
                "device_connected": False,
                "adb_working": False,
                "screenshot_capable": False,
                "app_launch_capable": False,
                "total_score": 0,
                "details": {}
            }

            # Test device connection
            connected = await self.adb_fallback.check_device_connection()
            test_results["device_connected"] = connected
            test_results["details"]["connection"] = "✅ Connected" if connected else "❌ Not connected"

            if not connected:
                return test_results

            test_results["total_score"] += 25

            # Test basic ADB commands
            success, _ = await self.adb_fallback.execute_adb_command("shell getprop ro.product.model")
            test_results["adb_working"] = success
            test_results["details"]["adb_commands"] = "✅ Working" if success else "❌ Not working"

            if success:
                test_results["total_score"] += 25

            # Test screenshot capability
            screenshot_path = await self.adb_fallback.take_screenshot("connectivity_test.png")
            test_results["screenshot_capable"] = bool(screenshot_path)
            test_results["details"]["screenshots"] = "✅ Working" if screenshot_path else "❌ Not working"

            if screenshot_path:
                test_results["total_score"] += 25

            # Test app launch (don't wait for full launch)
            success, _ = await self.adb_fallback.execute_adb_command("shell am start -n com.binance.dev/.ui.MainActivity")
            test_results["app_launch_capable"] = success
            test_results["details"]["app_launch"] = "✅ Working" if success else "❌ Not working"

            if success:
                test_results["total_score"] += 25

            # Cleanup
            await self.adb_fallback.close_binance_app()

            return test_results

        except Exception as e:
            logger.error(f"Device connectivity test failed: {e}")
            return {
                "device_connected": False,
                "error": str(e),
                "total_score": 0
            }

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return await self.device_coordinator.get_system_status()

    async def run_interactive_mode(self):
        """Run interactive mode for manual testing."""
        logger.info("Starting interactive mode...")

        while self.running and not self.shutdown_requested:
            try:
                print("\n" + "="*60)
                print("🚀 Enhanced Hau5 Claim - Interactive Mode")
                print("="*60)
                print("1. Test device connectivity")
                print("2. Claim redpacket via ADB")
                print("3. Show system status")
                print("4. Toggle fallback enabled")
                print("5. Toggle auto-recovery")
                print("6. Initialize device")
                print("7. Health check")
                print("8. Exit")
                print("-"*60)

                choice = input("Select option (1-8): ").strip()

                if choice == "1":
                    # Test connectivity
                    print("Testing device connectivity...")
                    results = await self.test_device_connectivity()
                    print(f"\nConnectivity Test Results:")
                    print(f"Score: {results.get('total_score', 0)}/100")
                    for key, value in results.get('details', {}).items():
                        print(f"  {key}: {value}")

                elif choice == "2":
                    # Manual claim
                    code = input("Enter 8-character redpacket code: ").strip().upper()
                    if len(code) == 8:
                        print(f"Attempting ADB claim for code: {code}")
                        result = await self.claim_redpacket_fallback(code, "manual")
                        if result.get("success"):
                            print(f"✅ Claim successful! Time: {result.get('execution_time', 0):.1f}s")
                        else:
                            print(f"❌ Claim failed: {result.get('error', 'Unknown error')}")
                    else:
                        print("❌ Invalid code format")

                elif choice == "3":
                    # Show status
                    status = await self.get_system_status()
                    print(f"\nSystem Status:")
                    print(f"Device Status: {status['device_status']}")
                    print(f"Fallback Enabled: {status['fallback_enabled']}")
                    print(f"Auto-Recovery: {status['auto_recovery_enabled']}")
                    print(f"Total Claims: {status['fallback_metrics']['total_claims']}")
                    print(f"Success Rate: {status['fallback_metrics']['success_rate']:.1f}%")
                    print(f"Avg Claim Time: {status['fallback_metrics']['avg_claim_time']:.1f}s")

                elif choice == "4":
                    # Toggle fallback
                    current = self.device_coordinator.fallback_enabled
                    self.device_coordinator.enable_fallback(not current)
                    print(f"Fallback {'enabled' if not current else 'disabled'}")

                elif choice == "5":
                    # Toggle auto-recovery
                    current = self.device_coordinator.auto_recovery_enabled
                    self.device_coordinator.enable_auto_recovery(not current)
                    print(f"Auto-recovery {'enabled' if not current else 'disabled'}")

                elif choice == "6":
                    # Initialize device
                    print("Initializing device...")
                    success = await self.device_coordinator.initialize_device()
                    print(f"Initialization {'successful' if success else 'failed'}")

                elif choice == "7":
                    # Health check
                    print("Performing health check...")
                    health = await self.device_coordinator.health_check()
                    print(f"Health check: {'✅ Passed' if health else '❌ Failed'}")

                elif choice == "8":
                    # Exit
                    self.shutdown_requested = True
                    break

                else:
                    print("Invalid choice")

                if not self.shutdown_requested:
                    await asyncio.sleep(1)

            except KeyboardInterrupt:
                self.shutdown_requested = True
                break
            except Exception as e:
                logger.error(f"Interactive mode error: {e}")

    async def run_daemon_mode(self):
        """Run in daemon mode for integration with main bot."""
        logger.info("Starting daemon mode...")

        while self.running and not self.shutdown_requested:
            try:
                # Perform periodic health checks
                await self.device_coordinator.health_check()

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Daemon mode error: {e}")
                await asyncio.sleep(30)  # Shorter wait on error

    async def run(self, mode: str = "interactive"):
        """Main run method."""
        try:
            self.running = True

            # Initialize system
            if not await self.initialize():
                logger.error("Failed to initialize system")
                return 1

            if mode == "interactive":
                await self.run_interactive_mode()
            elif mode == "daemon":
                await self.run_daemon_mode()
            else:
                logger.error(f"Unknown mode: {mode}")
                return 1

        except Exception as e:
            logger.error(f"Run error: {e}", exc_info=True)
            return 1
        finally:
            await self.shutdown()
            return 0

    async def shutdown(self):
        """Graceful shutdown."""
        try:
            logger.info("Shutting down Enhanced Hau5 Claim system...")
            self.running = False

            # Shutdown device coordinator
            await self.device_coordinator.shutdown()

            logger.info("Enhanced Hau5 Claim system shutdown completed")

        except Exception as e:
            logger.error(f"Shutdown error: {e}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enhanced Hau5 Claim - ADB Fallback System")
    parser.add_argument(
        "--mode",
        choices=["interactive", "daemon"],
        default="interactive",
        help="Run mode (default: interactive)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Create and run the system
    system = EnhancedHau5Claim()
    return await system.run(args.mode)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
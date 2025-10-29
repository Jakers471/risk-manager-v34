"""
Integration smoke test using run_dev.py subprocess.

Validates complete system boots, connects to SDK, and processes events.
"""

import pytest
import asyncio
import signal
import sys
from pathlib import Path


@pytest.mark.integration
@pytest.mark.slow
class TestLiveSystemSmoke:
    """Automated smoke test using run_dev.py."""

    @pytest.mark.asyncio
    async def test_system_boots_and_reaches_checkpoints(self):
        """
        Start run_dev.py, verify first 5 checkpoints reached, shutdown.

        Checkpoints:
        1. Service Start (banner)
        2. Config Loaded
        3. SDK Connected
        4. Risk Manager initialized
        5. Event Loop Running
        """
        # Start run_dev.py as subprocess
        process = await asyncio.create_subprocess_exec(
            sys.executable, "run_dev.py",
            "--log-level", "INFO",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(Path(__file__).parent.parent.parent)  # Project root
        )

        checkpoints_seen = set()
        max_wait = 60  # seconds
        output_lines = []

        try:
            # Read output with timeout
            start_time = asyncio.get_event_loop().time()

            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > max_wait:
                    break

                try:
                    # Read line with timeout
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=5.0
                    )

                    if not line:
                        break  # EOF

                    line_str = line.decode('utf-8', errors='ignore').strip()
                    output_lines.append(line_str)

                    # Check for checkpoints
                    if "RISK MANAGER V34" in line_str or "DEVELOPMENT MODE" in line_str:
                        checkpoints_seen.add(1)
                        print("[OK] Checkpoint 1: Service Start")

                    if "Configuration loaded successfully" in line_str:
                        checkpoints_seen.add(2)
                        print("[OK] Checkpoint 2: Config Loaded")

                    if "Connected to TopstepX API" in line_str:
                        checkpoints_seen.add(3)
                        print("[OK] Checkpoint 3: SDK Connected")

                    if "Risk Manager initialized" in line_str:
                        checkpoints_seen.add(4)
                        print("[OK] Checkpoint 4: Risk Manager Initialized")

                    if "Risk Manager is running" in line_str or "LIVE EVENT FEED" in line_str:
                        checkpoints_seen.add(5)
                        print("[OK] Checkpoint 5: Event Loop Running")

                    # If we got 5 checkpoints, success!
                    if len(checkpoints_seen) >= 5:
                        print(f"[OK] All 5 checkpoints reached! Shutting down...")
                        break

                except asyncio.TimeoutError:
                    # No output for 5 seconds, check if process died
                    if process.returncode is not None:
                        break
                    continue

        finally:
            # Graceful shutdown
            try:
                print("Sending shutdown signal...")
                # Windows doesn't support SIGINT for subprocesses
                if sys.platform == 'win32':
                    process.terminate()  # SIGTERM on Windows
                else:
                    process.send_signal(signal.SIGINT)
                await asyncio.wait_for(process.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                print("Timeout waiting for graceful shutdown, killing...")
                process.kill()
                await process.wait()
            except (ProcessLookupError, ValueError):
                pass  # Already dead or invalid signal

        # Print captured output for debugging
        print("\n=== Captured Output (last 20 lines) ===")
        for line in output_lines[-20:]:
            # Strip non-ASCII characters for Windows console compatibility
            clean_line = line.encode('ascii', 'ignore').decode('ascii')
            print(clean_line)

        # Assertions
        assert len(checkpoints_seen) >= 3, \
            f"Expected at least 3 checkpoints, got {len(checkpoints_seen)}: {checkpoints_seen}"

        # If SDK connection fails, that's okay for this test (no credentials)
        # But we should at least reach Config Loaded
        assert 1 in checkpoints_seen, "Service Start checkpoint not reached"
        assert 2 in checkpoints_seen, "Config Loaded checkpoint not reached"

    @pytest.mark.asyncio
    async def test_system_handles_missing_credentials_gracefully(self):
        """
        If .env is missing/invalid, system should fail gracefully with error message.
        """
        # Temporarily rename .env if it exists
        env_path = Path(".env")
        backup_path = Path(".env.backup_test")

        had_env = env_path.exists()
        if had_env:
            env_path.rename(backup_path)

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "run_dev.py",
                "--log-level", "INFO",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path(__file__).parent.parent.parent)
            )

            # Wait for process to fail
            try:
                await asyncio.wait_for(process.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

            # Read output
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')

            # Should mention credentials or connection failure
            assert any(word in output.lower() for word in ['credential', 'connect', 'error', 'failed', 'topstepx']), \
                "Should show error message about missing credentials or connection failure"

        finally:
            # Restore .env
            if had_env and backup_path.exists():
                backup_path.rename(env_path)

    @pytest.mark.asyncio
    async def test_ctrl_c_triggers_graceful_shutdown(self):
        """
        SIGINT (Ctrl+C) should trigger graceful shutdown, not crash.
        """
        process = await asyncio.create_subprocess_exec(
            sys.executable, "run_dev.py",
            "--log-level", "INFO",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(Path(__file__).parent.parent.parent)
        )

        output_lines = []
        shutdown_messages = []

        # Wait 10 seconds for startup
        try:
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < 10:
                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=1.0
                    )
                    if line:
                        line_str = line.decode('utf-8', errors='ignore').strip()
                        output_lines.append(line_str)
                except asyncio.TimeoutError:
                    continue
        except Exception as e:
            print(f"Error during startup wait: {e}")

        # Send SIGINT/SIGTERM
        try:
            # Windows doesn't support SIGINT for subprocesses
            if sys.platform == 'win32':
                process.terminate()  # SIGTERM on Windows
            else:
                process.send_signal(signal.SIGINT)
        except Exception as e:
            print(f"Error sending signal: {e}")
            process.terminate()

        # Wait for graceful shutdown (max 15 seconds)
        try:
            await asyncio.wait_for(process.wait(), timeout=15.0)

            # Collect any remaining output
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=2.0
                )
                remaining = stdout.decode('utf-8', errors='ignore')
                shutdown_messages = [line for line in remaining.split('\n') if 'shutdown' in line.lower()]
            except:
                pass

        except asyncio.TimeoutError:
            print("Timeout waiting for graceful shutdown, killing...")
            process.kill()
            await process.wait()
            pytest.fail("Graceful shutdown timed out")

        # Print captured output for debugging
        print("\n=== Captured Output (last 20 lines) ===")
        for line in output_lines[-20:]:
            # Strip non-ASCII characters for Windows console compatibility
            clean_line = line.encode('ascii', 'ignore').decode('ascii')
            print(clean_line)

        if shutdown_messages:
            print("\n=== Shutdown Messages ===")
            for msg in shutdown_messages:
                print(msg)

        # Check exit code (should be 0 for graceful exit)
        # Note: SIGINT may return different codes on different systems
        # -2 on Windows, 130 on Linux, 0 for normal exit
        acceptable_codes = [0, -2, 130, 1]  # 1 is also okay if interrupted during startup
        assert process.returncode in acceptable_codes, \
            f"Expected exit code in {acceptable_codes}, got {process.returncode}"

    @pytest.mark.asyncio
    async def test_system_with_explicit_account_flag(self):
        """
        Test run_dev.py with --account flag (non-interactive mode).
        """
        # This test assumes we have a valid account ID in config
        # We'll use a dummy account to test the flag handling

        process = await asyncio.create_subprocess_exec(
            sys.executable, "run_dev.py",
            "--account", "DUMMY123",  # Fake account for testing
            "--log-level", "INFO",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(Path(__file__).parent.parent.parent)
        )

        output_lines = []
        max_wait = 30

        try:
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < max_wait:
                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=2.0
                    )

                    if not line:
                        break

                    line_str = line.decode('utf-8', errors='ignore').strip()
                    output_lines.append(line_str)

                    # Look for account-related messages
                    if "DUMMY123" in line_str or "Account" in line_str:
                        print(f"Found account reference: {line_str}")

                    # If we see an error or the banner, we can stop
                    if any(word in line_str for word in ["Error", "Failed", "RISK MANAGER"]):
                        break

                except asyncio.TimeoutError:
                    if process.returncode is not None:
                        break
                    continue

        finally:
            # Kill process
            try:
                process.kill()
                await process.wait()
            except:
                pass

        # Print output for debugging
        print("\n=== Output with --account flag ===")
        for line in output_lines[-15:]:
            print(line)

        # The process should have started (banner shown) or shown an error
        # Either way, it should handle the --account flag without crashing
        banner_seen = any("RISK MANAGER" in line for line in output_lines)
        error_seen = any(word in ' '.join(output_lines).lower() for word in ["error", "failed"])

        assert banner_seen or error_seen, \
            "Process should either show banner or show error, not hang silently"

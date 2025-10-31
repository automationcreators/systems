#!/usr/bin/env python3
"""
Personal OS Daily Scheduler
Alternative to LaunchAgent - runs daily automation tasks using Python scheduler
Avoids macOS security restrictions by running in user context
"""

import os
import sys
import time
import subprocess
import logging
import signal
from datetime import datetime
from pathlib import Path
import json

class DailyScheduler:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        self.pid_file = self.systems_dir / "scheduler.pid"
        self.config_file = self.systems_dir / "scheduler-config.json"
        self.log_file = self.systems_dir / "scheduler.log"
        self.running = True

        # Setup logging
        self.setup_logging()

        # Load configuration
        self.load_config()

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load or create scheduler configuration"""
        default_config = {
            "enabled": True,
            "morning_time": "09:00",  # 9:00 AM
            "evening_time": "20:00",  # 8:00 PM
            "check_interval_seconds": 60,  # Check every 60 seconds
            "run_on_startup": True,  # Run morning routine on scheduler startup
            "tasks": {
                "morning": {
                    "enabled": True,
                    "script": "systems/daily-morning.sh",
                    "timeout": 300
                },
                "evening": {
                    "enabled": True,
                    "script": "systems/daily-evening.sh",
                    "timeout": 300
                }
            },
            "last_run": {
                "morning": None,
                "evening": None
            }
        }

        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
        else:
            self.config = default_config

        self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def write_pid(self):
        """Write process ID to file"""
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        self.logger.info(f"Scheduler started with PID {os.getpid()}")

    def remove_pid(self):
        """Remove PID file"""
        if self.pid_file.exists():
            self.pid_file.unlink()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def run_task(self, task_name: str, script_path: str, timeout: int = 300) -> bool:
        """Run a scheduled task"""
        try:
            self.logger.info(f"Starting {task_name} task...")

            full_path = self.base_path / script_path

            if not full_path.exists():
                self.logger.error(f"Script not found: {full_path}")
                return False

            # Change to base directory and run script
            result = subprocess.run(
                [str(full_path)],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                self.logger.info(f"{task_name} task completed successfully")

                # Save output to log
                output_log = self.systems_dir / f"{task_name}-output.log"
                with open(output_log, 'w') as f:
                    f.write(f"=== {task_name} - {datetime.now().isoformat()} ===\n")
                    f.write(result.stdout)
                    if result.stderr:
                        f.write(f"\n=== STDERR ===\n{result.stderr}")

                return True
            else:
                self.logger.error(f"{task_name} task failed with code {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"{task_name} task timed out after {timeout} seconds")
            return False
        except Exception as e:
            self.logger.error(f"Error running {task_name} task: {e}")
            return False

    def should_run_task(self, task_name: str, scheduled_time: str) -> bool:
        """Check if a task should run based on schedule"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.strftime("%Y-%m-%d")

        # Parse scheduled time
        scheduled_hour, scheduled_minute = map(int, scheduled_time.split(":"))

        # Check if we're within 1 minute of scheduled time
        if current_time == scheduled_time or (
            now.hour == scheduled_hour and
            abs(now.minute - scheduled_minute) <= 1
        ):
            # Check if we already ran today
            last_run = self.config["last_run"].get(task_name)
            if last_run != current_date:
                return True

        return False

    def mark_task_completed(self, task_name: str):
        """Mark a task as completed for today"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.config["last_run"][task_name] = current_date
        self.save_config()

    def run(self):
        """Main scheduler loop"""
        self.write_pid()
        self.logger.info("Daily scheduler started")
        self.logger.info(f"Morning tasks scheduled for: {self.config['morning_time']}")
        self.logger.info(f"Evening tasks scheduled for: {self.config['evening_time']}")

        # Run on startup if configured
        if self.config["run_on_startup"]:
            self.logger.info("Running morning routine on startup...")
            task_config = self.config["tasks"]["morning"]
            if task_config["enabled"]:
                self.run_task("morning", task_config["script"], task_config["timeout"])

        check_interval = self.config["check_interval_seconds"]

        try:
            while self.running:
                now = datetime.now()

                # Check morning task
                if self.config["tasks"]["morning"]["enabled"]:
                    if self.should_run_task("morning", self.config["morning_time"]):
                        self.logger.info("Time for morning tasks!")
                        task_config = self.config["tasks"]["morning"]
                        if self.run_task("morning", task_config["script"], task_config["timeout"]):
                            self.mark_task_completed("morning")

                # Check evening task
                if self.config["tasks"]["evening"]["enabled"]:
                    if self.should_run_task("evening", self.config["evening_time"]):
                        self.logger.info("Time for evening tasks!")
                        task_config = self.config["tasks"]["evening"]
                        if self.run_task("evening", task_config["script"], task_config["timeout"]):
                            self.mark_task_completed("evening")

                # Sleep until next check
                time.sleep(check_interval)

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt, shutting down...")
        finally:
            self.remove_pid()
            self.logger.info("Scheduler stopped")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Personal OS Daily Scheduler")
    parser.add_argument(
        "--action",
        choices=["start", "stop", "status", "run-now"],
        default="start",
        help="Action to perform"
    )
    parser.add_argument(
        "--task",
        choices=["morning", "evening"],
        help="Task to run (for run-now action)"
    )

    args = parser.parse_args()

    scheduler = DailyScheduler()

    if args.action == "start":
        # Check if already running
        if scheduler.pid_file.exists():
            try:
                with open(scheduler.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is running
                os.kill(pid, 0)
                print(f"❌ Scheduler already running with PID {pid}")
                print(f"   To stop it, run: python3 systems/daily-scheduler.py --action stop")
                sys.exit(1)
            except (ProcessLookupError, ValueError):
                # Process not running, remove stale PID file
                scheduler.pid_file.unlink()

        print("🚀 Starting Daily Scheduler...")
        print(f"   Morning tasks: {scheduler.config['morning_time']}")
        print(f"   Evening tasks: {scheduler.config['evening_time']}")
        print(f"   Log file: {scheduler.log_file}")
        print(f"   PID file: {scheduler.pid_file}")
        print(f"\n   To stop: python3 systems/daily-scheduler.py --action stop")
        print(f"   To check status: python3 systems/daily-scheduler.py --action status")
        scheduler.run()

    elif args.action == "stop":
        if not scheduler.pid_file.exists():
            print("❌ Scheduler is not running (no PID file found)")
            sys.exit(1)

        try:
            with open(scheduler.pid_file, 'r') as f:
                pid = int(f.read().strip())

            print(f"🛑 Stopping scheduler (PID {pid})...")
            os.kill(pid, signal.SIGTERM)

            # Wait for process to stop
            for i in range(10):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.5)
                except ProcessLookupError:
                    print("✅ Scheduler stopped successfully")
                    scheduler.remove_pid()
                    sys.exit(0)

            print("⚠️  Scheduler did not stop gracefully, forcing...")
            os.kill(pid, signal.SIGKILL)
            scheduler.remove_pid()

        except (ProcessLookupError, ValueError) as e:
            print(f"❌ Error stopping scheduler: {e}")
            scheduler.remove_pid()
            sys.exit(1)

    elif args.action == "status":
        if not scheduler.pid_file.exists():
            print("❌ Scheduler is not running")
            print("\n💡 To start the scheduler:")
            print("   python3 systems/daily-scheduler.py --action start")
            sys.exit(1)

        try:
            with open(scheduler.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is actually running
            os.kill(pid, 0)

            print(f"✅ Scheduler is running (PID {pid})")
            print(f"\n📊 Configuration:")
            print(f"   Morning tasks: {scheduler.config['morning_time']} - {'✅ Enabled' if scheduler.config['tasks']['morning']['enabled'] else '❌ Disabled'}")
            print(f"   Evening tasks: {scheduler.config['evening_time']} - {'✅ Enabled' if scheduler.config['tasks']['evening']['enabled'] else '❌ Disabled'}")
            print(f"\n📅 Last Run:")
            print(f"   Morning: {scheduler.config['last_run']['morning'] or 'Never'}")
            print(f"   Evening: {scheduler.config['last_run']['evening'] or 'Never'}")
            print(f"\n📝 Log file: {scheduler.log_file}")

        except ProcessLookupError:
            print("❌ Scheduler PID file exists but process is not running")
            print("   (Stale PID file - removing...)")
            scheduler.remove_pid()
            sys.exit(1)

    elif args.action == "run-now":
        if not args.task:
            print("❌ --task required for run-now action")
            sys.exit(1)

        print(f"🚀 Running {args.task} task now...")
        task_config = scheduler.config["tasks"][args.task]

        if not task_config["enabled"]:
            print(f"⚠️  {args.task} task is disabled in configuration")
            sys.exit(1)

        success = scheduler.run_task(args.task, task_config["script"], task_config["timeout"])

        if success:
            print(f"✅ {args.task} task completed successfully")
            scheduler.mark_task_completed(args.task)
        else:
            print(f"❌ {args.task} task failed")
            sys.exit(1)

if __name__ == "__main__":
    main()

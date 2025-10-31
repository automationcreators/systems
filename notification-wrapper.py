#!/usr/bin/env python3
"""
/systems/notification-wrapper.py
Universal notification wrapper for all agents
Sends notifications via Telegram, Healthchecks.io, and local logs
RELEVANT FILES: systems/daily-morning.sh, systems/github-sync-agent.py
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

class NotificationWrapper:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.config_file = self.base_path / "systems" / "notification-config.json"
        self.load_config()

    def load_config(self):
        """Load notification configuration"""
        default_config = {
            "enabled": True,
            "telegram": {
                "enabled": False,
                "bot_token": "",  # Set this in config
                "chat_id": ""     # Set this in config
            },
            "healthchecks": {
                "enabled": False,
                "ping_url": ""    # Set this in config (e.g., https://hc-ping.com/YOUR-UUID)
            },
            "log_file": str(self.base_path / "systems" / "notifications.log"),
            "notification_types": {
                "success": True,
                "error": True,
                "warning": True,
                "info": False   # Only errors, warnings, and successes by default
            }
        }

        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # Merge with defaults
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

    def send_telegram(self, message: str) -> bool:
        """Send notification via Telegram"""
        if not self.config["telegram"]["enabled"]:
            return False

        bot_token = self.config["telegram"]["bot_token"]
        chat_id = self.config["telegram"]["chat_id"]

        if not bot_token or not chat_id:
            self.log("Telegram not configured (missing bot_token or chat_id)", "warning")
            return False

        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.log(f"Telegram send failed: {e}", "error")
            return False

    def ping_healthchecks(self, success: bool = True, message: Optional[str] = None) -> bool:
        """Ping Healthchecks.io"""
        if not self.config["healthchecks"]["enabled"]:
            return False

        ping_url = self.config["healthchecks"]["ping_url"]
        if not ping_url:
            self.log("Healthchecks not configured (missing ping_url)", "warning")
            return False

        try:
            url = ping_url
            if not success:
                url += "/fail"

            if message:
                response = requests.post(url, data=message.encode('utf-8'), timeout=10)
            else:
                response = requests.get(url, timeout=10)

            return response.status_code == 200
        except Exception as e:
            self.log(f"Healthchecks ping failed: {e}", "error")
            return False

    def log(self, message: str, level: str = "info"):
        """Log to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"

        log_file = Path(self.config["log_file"])
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'a') as f:
            f.write(log_entry)

    def notify(self, message: str, notification_type: str = "info", ping_healthchecks: bool = False):
        """Send notification through all enabled channels"""
        if not self.config["enabled"]:
            return

        # Check if this notification type is enabled
        if not self.config["notification_types"].get(notification_type, True):
            return

        # Add emoji prefix based on type
        emoji_map = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        emoji = emoji_map.get(notification_type, "📢")
        formatted_message = f"{emoji} {message}"

        # Log to file (always)
        self.log(message, notification_type)

        # Send to Telegram
        if self.config["telegram"]["enabled"]:
            self.send_telegram(formatted_message)

        # Ping Healthchecks.io
        if ping_healthchecks and self.config["healthchecks"]["enabled"]:
            success = notification_type in ["success", "info"]
            self.ping_healthchecks(success, message)

    def success(self, message: str, ping_healthchecks: bool = True):
        """Send success notification"""
        self.notify(message, "success", ping_healthchecks)

    def error(self, message: str, ping_healthchecks: bool = True):
        """Send error notification"""
        self.notify(message, "error", ping_healthchecks)

    def warning(self, message: str, ping_healthchecks: bool = False):
        """Send warning notification"""
        self.notify(message, "warning", ping_healthchecks)

    def info(self, message: str, ping_healthchecks: bool = False):
        """Send info notification"""
        self.notify(message, "info", ping_healthchecks)

# Global instance for easy importing
notifier = NotificationWrapper()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Notification Wrapper")
    parser.add_argument("--message", required=True, help="Message to send")
    parser.add_argument("--type", choices=["success", "error", "warning", "info"], default="info")
    parser.add_argument("--ping", action="store_true", help="Ping Healthchecks.io")
    parser.add_argument("--setup-telegram", action="store_true", help="Setup Telegram bot")
    parser.add_argument("--setup-healthchecks", action="store_true", help="Setup Healthchecks.io")
    parser.add_argument("--test", action="store_true", help="Send test notification")

    args = parser.parse_args()

    notif = NotificationWrapper()

    if args.setup_telegram:
        print("\n🤖 Telegram Bot Setup")
        print("=" * 50)
        print("\n1. Open Telegram and search for '@BotFather'")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the bot token")
        print("4. Start a chat with your bot and send any message")
        print("5. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates")
        print("6. Copy your chat_id from the response")
        print()

        bot_token = input("Enter bot token: ").strip()
        chat_id = input("Enter chat_id: ").strip()

        notif.config["telegram"]["bot_token"] = bot_token
        notif.config["telegram"]["chat_id"] = chat_id
        notif.config["telegram"]["enabled"] = True
        notif.save_config()

        print("\n✅ Telegram configured! Sending test message...")
        if notif.send_telegram("🎉 Telegram bot configured successfully!"):
            print("✅ Test message sent!")
        else:
            print("❌ Test message failed - check your bot token and chat_id")

    elif args.setup_healthchecks:
        print("\n🏥 Healthchecks.io Setup")
        print("=" * 50)
        print("\n1. Go to https://healthchecks.io")
        print("2. Create a free account")
        print("3. Create a new check")
        print("4. Copy the ping URL")
        print()

        ping_url = input("Enter ping URL: ").strip()

        notif.config["healthchecks"]["ping_url"] = ping_url
        notif.config["healthchecks"]["enabled"] = True
        notif.save_config()

        print("\n✅ Healthchecks.io configured! Sending test ping...")
        if notif.ping_healthchecks(True, "Test ping from notification wrapper"):
            print("✅ Test ping sent!")
        else:
            print("❌ Test ping failed - check your ping URL")

    elif args.test:
        print("\n🧪 Sending test notifications...")
        notif.success("Test success notification", ping_healthchecks=True)
        notif.warning("Test warning notification")
        notif.error("Test error notification", ping_healthchecks=True)
        print("✅ Test notifications sent!")

    else:
        # Send notification
        if args.type == "success":
            notif.success(args.message, args.ping)
        elif args.type == "error":
            notif.error(args.message, args.ping)
        elif args.type == "warning":
            notif.warning(args.message, args.ping)
        else:
            notif.info(args.message, args.ping)

        print(f"✅ Notification sent: {args.message}")

if __name__ == "__main__":
    main()

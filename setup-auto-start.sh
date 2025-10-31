#!/bin/bash
# Setup Personal OS Scheduler to start automatically at login
# This creates a simple LaunchAgent that doesn't need Full Disk Access

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_FILE="$HOME/Library/LaunchAgents/com.personalos.scheduler.plist"

echo "🔧 Setting up Personal OS Scheduler auto-start..."
echo ""

# Create the LaunchAgent plist
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.personalos.scheduler</string>

    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/scheduler-service.sh</string>
        <string>start</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <false/>

    <key>WorkingDirectory</key>
    <string>$BASE_DIR</string>

    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/scheduler-launchagent.log</string>

    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/scheduler-launchagent-error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ Created LaunchAgent plist: $PLIST_FILE"
echo ""

# Unload existing agent if running
if launchctl list | grep -q "com.personalos.scheduler"; then
    echo "🔄 Unloading existing scheduler LaunchAgent..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# Load the new agent
echo "📂 Loading scheduler LaunchAgent..."
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Scheduler LaunchAgent loaded successfully!"
    echo ""
    echo "📊 The scheduler will now:"
    echo "   • Start automatically when you log in"
    echo "   • Run morning tasks at 09:00 AM daily"
    echo "   • Run evening tasks at 20:00 PM (8:00 PM) daily"
    echo ""
    echo "💡 Useful commands:"
    echo "   Check status:      ./systems/scheduler-service.sh status"
    echo "   Stop scheduler:    ./systems/scheduler-service.sh stop"
    echo "   Start scheduler:   ./systems/scheduler-service.sh start"
    echo "   View logs:         tail -f $SCRIPT_DIR/scheduler.log"
    echo ""
    echo "🔧 To disable auto-start:"
    echo "   launchctl unload $PLIST_FILE"
else
    echo "❌ Failed to load LaunchAgent"
    echo "   Please check the error log: $SCRIPT_DIR/scheduler-launchagent-error.log"
fi

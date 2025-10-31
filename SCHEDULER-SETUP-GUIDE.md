# Personal OS Scheduler Setup Guide

## Overview

Your Personal OS now has a **Python-based scheduler** that replaces the problematic LaunchAgent. This avoids macOS security restrictions while providing reliable daily automation.

## ✅ Current Status

The scheduler is **RUNNING** and will:
- Run morning tasks daily at **9:00 AM**
- Run evening tasks daily at **8:00 PM**
- Sync all projects to GitHub as part of morning routine

---

## Quick Start

### Check Scheduler Status
```bash
cd /Users/elizabethknopf/Documents/claudec
./systems/scheduler-service.sh status
```

### Start/Stop Scheduler
```bash
./systems/scheduler-service.sh start    # Start the scheduler
./systems/scheduler-service.sh stop     # Stop the scheduler
./systems/scheduler-service.sh restart  # Restart the scheduler
```

### View Live Logs
```bash
./systems/scheduler-service.sh logs     # Follow the log file
```

### Run Tasks Immediately
```bash
./systems/scheduler-service.sh run-morning   # Run morning tasks now
./systems/scheduler-service.sh run-evening   # Run evening tasks now
```

---

## Auto-Start at Login

To make the scheduler start automatically when you log in:

```bash
cd /Users/elizabethknopf/Documents/claudec
./systems/setup-auto-start.sh
```

This creates a LaunchAgent that:
- ✅ Doesn't require Full Disk Access
- ✅ Starts automatically at login
- ✅ Works within macOS security restrictions
- ✅ Is easy to enable/disable

### Disable Auto-Start
```bash
launchctl unload ~/Library/LaunchAgents/com.personalos.scheduler.plist
```

### Re-enable Auto-Start
```bash
launchctl load ~/Library/LaunchAgents/com.personalos.scheduler.plist
```

---

## Configuration

The scheduler configuration is stored in:
```
systems/scheduler-config.json
```

### Default Settings
```json
{
  "enabled": true,
  "morning_time": "09:00",
  "evening_time": "20:00",
  "check_interval_seconds": 60,
  "run_on_startup": true,
  "tasks": {
    "morning": {
      "enabled": true,
      "script": "systems/daily-morning.sh",
      "timeout": 300
    },
    "evening": {
      "enabled": true,
      "script": "systems/daily-evening.sh",
      "timeout": 300
    }
  }
}
```

### Customize Schedule
Edit `systems/scheduler-config.json`:

```json
{
  "morning_time": "08:30",  // Run at 8:30 AM
  "evening_time": "21:00"   // Run at 9:00 PM
}
```

Then restart the scheduler:
```bash
./systems/scheduler-service.sh restart
```

---

## What Gets Automated?

### Morning Tasks (9:00 AM)
1. 🔍 Project Discovery & Registry Update
2. 📋 Document Parsing Refresh
3. 🔒 Security Monitoring Scan
4. 📊 Template Lineage Analytics
5. 🌐 Dashboard Data Integration
6. 💰 Token Usage Report
7. 📊 Storage & Backup Status
8. 🔄 **GitHub Sync** - Syncs all changed projects

### Evening Tasks (8:00 PM)
1. 📊 Daily Impact Report
2. 🔄 Daily Backup
3. 💡 Lifecycle Maintenance
4. 🧹 Storage Cleanup
5. 📋 Tomorrow's Priorities

---

## Logs and Monitoring

### Log Files
- **Main scheduler log**: `systems/scheduler.log`
- **Service manager log**: `systems/scheduler-service.log`
- **Morning task output**: `systems/morning-output.log`
- **Evening task output**: `systems/evening-output.log`

### Check Recent Activity
```bash
# Last 20 lines of scheduler log
tail -20 systems/scheduler.log

# Follow logs in real-time
tail -f systems/scheduler.log

# Check when tasks last ran
./systems/scheduler-service.sh status
```

---

## Troubleshooting

### Scheduler Not Running
```bash
# Check status
./systems/scheduler-service.sh status

# Start if stopped
./systems/scheduler-service.sh start
```

### Tasks Not Executing
1. Check if scheduler is running:
   ```bash
   ./systems/scheduler-service.sh status
   ```

2. Check logs for errors:
   ```bash
   tail -50 systems/scheduler.log
   ```

3. Test task manually:
   ```bash
   ./systems/scheduler-service.sh run-morning
   ```

### Permission Issues
The Python scheduler runs in your user context, so it has the same permissions as your terminal. If you still get permission errors:

1. Make sure scripts are executable:
   ```bash
   chmod +x systems/*.sh
   ```

2. Check script paths in config:
   ```bash
   cat systems/scheduler-config.json
   ```

### Scheduler Crashed
If the scheduler stops unexpectedly:

1. Check the logs:
   ```bash
   tail -50 systems/scheduler.log
   tail -50 systems/scheduler-service.log
   ```

2. Remove stale PID file:
   ```bash
   rm systems/scheduler.pid
   ```

3. Restart:
   ```bash
   ./systems/scheduler-service.sh start
   ```

---

## Alternative: Fix Original LaunchAgent (If Preferred)

If you prefer to use the original LaunchAgent instead:

### Option 1: Grant Full Disk Access
1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the **+** button
3. Add `/bin/bash`
4. Restart the LaunchAgent:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.user.dailymorning.plist
   launchctl load ~/Library/LaunchAgents/com.user.dailymorning.plist
   ```

### Option 2: Move Personal OS Outside Documents
```bash
# Stop scheduler
./systems/scheduler-service.sh stop

# Move Personal OS
mv /Users/elizabethknopf/Documents/claudec /Users/elizabethknopf/personal-os

# Update LaunchAgent plist paths
# Edit ~/Library/LaunchAgents/com.user.dailymorning.plist

# Reload
launchctl load ~/Library/LaunchAgents/com.user.dailymorning.plist
```

---

## Comparison: Python Scheduler vs LaunchAgent

### Python Scheduler (Recommended)
✅ No security permission issues
✅ Easy to start/stop/restart
✅ Clear, readable logs
✅ Run tasks on-demand
✅ Simple configuration
✅ Works immediately

### LaunchAgent (Original)
✅ Native macOS integration
✅ Managed by system
❌ Requires Full Disk Access
❌ Harder to debug
❌ Permission issues in Documents folder

---

## Summary

🎉 **Your scheduler is now set up and running!**

**Current Setup:**
- ✅ Python scheduler running (PID shown in status)
- ✅ Morning tasks: 9:00 AM daily
- ✅ Evening tasks: 8:00 PM daily
- ✅ GitHub sync included in morning tasks
- ✅ All 32 projects synced to GitHub

**To enable auto-start at login:**
```bash
./systems/setup-auto-start.sh
```

**Check everything is working:**
```bash
./systems/scheduler-service.sh status
```

---

*Generated on 2025-10-21*

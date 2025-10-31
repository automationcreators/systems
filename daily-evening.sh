#!/bin/bash
# Personal OS - Daily Evening Routine  
# Run this each evening to review progress and prepare for tomorrow

echo "🌙 Personal OS - Daily Evening Review"
echo "====================================="
date
echo ""

cd "/Users/elizabethknopf/Documents/claudec"

echo "📊 Today's Impact:"
echo "  Storage freed: $(python3 systems/storage-monitor.py --action status | grep 'Free space' | awk '{print $3, $4}')"
echo "  Active projects: $(ls active/ 2>/dev/null | wc -l | xargs)"
echo "  Staging projects: $(ls staging/ 2>/dev/null | wc -l | xargs)"
echo ""

echo "🔄 Running Daily Backup..."
python3 systems/backup-manager.py --action backup --type daily > /tmp/backup.log 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Daily backup completed successfully"
else
    echo "❌ Backup failed - check /tmp/backup.log"
fi
echo ""

echo "💡 Lifecycle Suggestions (Auto-executing safe ones):"
python3 systems/lifecycle-manager.py --action execute --auto > /tmp/lifecycle.log 2>&1
echo "✅ Lifecycle maintenance completed"
echo ""

echo "🔍 Scanning for Skill Opportunities..."
python3 systems/skills-creation-agent/skills_creation_agent.py > /tmp/skills-agent.log 2>&1
if [ $? -eq 0 ]; then
    # Check if there are new recommendations
    new_recs=$(grep "New recommendations:" /tmp/skills-agent.log | awk '{print $3}')
    backlog=$(grep "Backlog size:" /tmp/skills-agent.log | awk '{print $3}')
    if [ ! -z "$new_recs" ] && [ "$new_recs" -gt 0 ]; then
        echo "✅ Found $new_recs new skill opportunities (backlog: $backlog)"
        echo "   Report: systems/skills-creation-agent/reports/skills_opportunities_$(date +%Y-%m-%d).md"
    else
        echo "✅ Skills scan complete (no new opportunities today)"
    fi
else
    echo "⚠️  Skills scan failed - check /tmp/skills-agent.log"
fi
echo ""

echo "🧹 Quick Cleanup:"
python3 systems/storage-monitor.py --action cleanup | grep -E "(Files removed|Space freed)"
echo ""

echo "📋 Tomorrow's Priorities:"
echo "Consider starting projects from staging:"
ls -1 staging/ | head -3
echo ""

echo "🎯 System Health Check:"
backup_status=$(python3 systems/backup-manager.py --action status | grep "Overdue" | grep "No" > /dev/null && echo "✅" || echo "⚠️")
storage_status=$(python3 systems/storage-monitor.py --action status | grep "HEALTHY" > /dev/null && echo "✅" || echo "⚠️")
echo "  Backups: $backup_status"  
echo "  Storage: $storage_status"
echo ""

echo "✅ Evening review complete! Rest well!"
echo ""
echo "💡 Tomorrow morning run: ./systems/daily-morning.sh"
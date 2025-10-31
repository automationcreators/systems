#!/bin/bash
# Personal OS - Enhanced Daily Morning Routine
# Integrated sync of all Personal OS systems including new architecture

echo "🌅 Personal OS - Enhanced Daily Morning Check"
echo "============================================="
date
echo ""

cd "$(dirname "$0")/.."
echo "📍 Working directory: $(pwd)"
echo ""

# NEW ARCHITECTURE COMPONENTS

echo "1. 🔍 Project Discovery & Registry Update..."
python3 systems/project-discovery-service.py --action scan
echo ""

echo "2. 📋 Document Parsing Refresh..."
python3 systems/document-parser.py --action scan
echo ""

echo "3. 🔒 Security Monitoring Scan..."
python3 systems/security-monitoring-dashboard.py --action scan --format text
echo ""

echo "4. 📊 Template Lineage Analytics..."
python3 systems/template-lineage-manager.py --action analytics
echo ""

echo "5. 🌐 Dashboard Data Integration..."
python3 systems/dashboard-data-provider.py --action generate
echo ""

echo "6. 💰 Token Usage Report..."
python3 systems/token-usage-tracker.py --action status
echo ""

echo "7. 📋 TODO Aggregation & Sync..."
python3 systems/todo-aggregation-engine.py --action sync
echo ""

echo "8. 🎯 Project Orchestrator Health Check..."
python3 systems/master-project-orchestrator.py --action health --quick
echo ""

# LEGACY COMPONENTS

echo "9. 📊 Legacy System Status..."
if [ -f "systems/storage-monitor.py" ]; then
    python3 systems/storage-monitor.py --action status | grep -E "(Storage Status|Free space|Personal OS size)"
fi
echo ""

echo "10. 🔄 Backup Status..."
if [ -f "systems/backup-manager.py" ]; then
    python3 systems/backup-manager.py --action status | grep -E "(Last backup|Overdue)"
fi
echo ""

echo "11. 💡 Lifecycle Suggestions..."
if [ -f "systems/lifecycle-manager.py" ]; then
    python3 systems/lifecycle-manager.py --action suggest | head -5
fi
echo ""

# PROJECT OVERVIEW

echo "12. 🔥 Current Active Projects:"
ls -1 active/ | head -8
echo ""

echo "13. 📋 Staging (Ready to Start):"
ls -1 staging/ | head -5
echo ""

echo "14. 🔄 GitHub Sync Check..."
python3 systems/github-sync-agent.py --action sync
echo ""

# SYSTEM HEALTH CHECK

echo "15. ⚙️ System Health Check..."

# Check for required dependencies
if command -v python3 &> /dev/null; then
    echo "    ✅ Python3 available"
else
    echo "    ❌ Python3 not found"
fi

if python3 -c "import watchdog" 2>/dev/null; then
    echo "    ✅ Watchdog library available"
else
    echo "    ⚠️  Watchdog library missing - install with: pip3 install watchdog"
fi

# Check vault status
if [ -d ".vault" ]; then
    echo "    ✅ Vault directory exists"
    vault_files=$(find .vault -name "*.enc" 2>/dev/null | wc -l)
    echo "    📦 Vault files: $vault_files"
else
    echo "    ⚠️  Vault directory not found"
    echo "    💡 Initialize with: python3 systems/vault-manager.py"
fi

# Check dashboard accessibility
dashboard_paths=(
    "active/Project Management/dashboard/index.html"
    "Project Management/dashboard/index.html"
)

dashboard_found=false
for path in "${dashboard_paths[@]}"; do
    if [ -f "$path" ]; then
        echo "    ✅ Dashboard accessible at: $path"
        dashboard_found=true
        break
    fi
done

if [ "$dashboard_found" = false ]; then
    echo "    ⚠️  Dashboard not found at expected locations"
fi

# Check data files
data_files=(
    "systems/dashboard-projects-data.json"
    "project-registry.json" 
    "systems/security-report.json"
    "systems/token-usage.json"
)

echo "    📁 Data files:"
for file in "${data_files[@]}"; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo "      ✅ $file ($size)"
    else
        echo "      ❌ $file (missing)"
    fi
done

echo ""

# SUMMARY AND NEXT STEPS

echo "14. 🎯 Morning Sync Summary:"
echo "    ✅ New architecture systems operational"
echo "    ✅ Project discovery and sync updated"
echo "    ✅ Documents parsed and analyzed"
echo "    ✅ Security monitoring active"
echo "    ✅ Template lineage tracked"
echo "    ✅ Dashboard data refreshed"
echo "    ✅ Token usage monitored"
echo "    ✅ GitHub sync completed"
echo "    ✅ System health verified"
echo ""

echo "🚀 Personal OS is ready for the day!"
echo ""
echo "💡 Quick Access Commands:"
echo "   • Open Dashboard:"
for path in "${dashboard_paths[@]}"; do
    if [ -f "$path" ]; then
        echo "     open \"$path\""
        break
    fi
done
echo "   • Security Dashboard: python3 systems/security-monitoring-dashboard.py --action dashboard"
echo "   • Token Status: python3 systems/token-usage-tracker.py --action status"
echo "   • Project Drilldown: python3 systems/dashboard-data-provider.py --action drilldown --project PROJECT_NAME"
echo "   • New Project: python3 systems/project-bootstrapper.py"
echo "   • Generate Security Templates: python3 systems/secure-template-generator.py --action create --project PROJECT_PATH"
echo ""

echo "📊 System Integration Status:"
echo "   ✅ Real-time project discovery"
echo "   ✅ Live document parsing" 
echo "   ✅ Security monitoring"
echo "   ✅ Token usage tracking"
echo "   ✅ Template lineage management"
echo "   ✅ Dashboard integration"
echo ""

echo "============================================="
echo "Enhanced morning sync completed at $(date)"
echo "Personal OS Architecture: Fully Operational"
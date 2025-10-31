#!/usr/bin/env python3
"""
Master Project Orchestrator
Single entry point for all project operations - coordinates existing specialized tools
Provides manual trigger modes with progress indicators and error handling
"""

import json
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

class MasterProjectOrchestrator:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        self.project_registry_path = self.base_path / "project-registry.json"
        
        # Setup logging
        self.setup_logging()
        
        # Available tools and their commands
        self.tools = {
            "discovery": {
                "script": "project-discovery-service.py",
                "description": "Project discovery and registry updates",
                "commands": {
                    "scan": "--action scan",
                    "quick-scan": "--action scan"
                }
            },
            "document_parser": {
                "script": "document-parser.py", 
                "description": "Document parsing and analysis",
                "commands": {
                    "scan": "--action scan",
                    "parse-changed": "--action scan"
                }
            },
            "dashboard": {
                "script": "dashboard-data-provider.py",
                "description": "Dashboard data generation",
                "commands": {
                    "generate": "--action generate",
                    "matrix": "--action matrix", 
                    "alerts": "--action alerts",
                    "health-report": "--action health-report"
                }
            },
            "project_manager": {
                "script": "project-manager-enhanced.py",
                "description": "Project management and templates",
                "commands": {
                    "templates": "--action templates",
                    "apply-templates": "--action apply-templates",
                    "create": "--action create"
                }
            },
            "security": {
                "script": "security-monitoring-dashboard.py",
                "description": "Security monitoring and reports",
                "commands": {
                    "scan": "--action scan --format text",
                    "report": "--action dashboard"
                }
            },
            "backup": {
                "script": "backup-manager.py", 
                "description": "Backup management",
                "commands": {
                    "backup": "--action backup",
                    "status": "--action status"
                }
            },
            "token_tracker": {
                "script": "token-usage-tracker.py",
                "description": "Token usage tracking",
                "commands": {
                    "status": "--action status",
                    "report": "--action report"
                }
            }
        }
        
        print(f"🎯 Master Project Orchestrator initialized")
        print(f"   Available tools: {len(self.tools)}")
        print(f"   Systems directory: {self.systems_dir}")
    
    def setup_logging(self):
        """Setup orchestrator logging"""
        log_file = self.systems_dir / "orchestrator.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_tool(self, tool_name: str, command: str, additional_args: str = "", timeout: int = 300) -> Dict:
        """Run a specific tool with error handling and progress tracking"""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        script_path = self.systems_dir / tool["script"]
        
        if not script_path.exists():
            return {"success": False, "error": f"Script not found: {script_path}"}
        
        if command not in tool["commands"]:
            return {"success": False, "error": f"Command '{command}' not available for {tool_name}"}
        
        cmd_args = tool["commands"][command]
        if additional_args:
            cmd_args += f" {additional_args}"
        
        full_command = f"python3 {script_path} {cmd_args}"
        
        start_time = time.time()
        self.logger.info(f"Starting {tool_name}:{command} - {tool['description']}")
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.base_path)
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info(f"Completed {tool_name}:{command} in {duration:.1f}s")
                return {
                    "success": True,
                    "output": result.stdout,
                    "duration": duration,
                    "tool": tool_name,
                    "command": command
                }
            else:
                self.logger.error(f"Failed {tool_name}:{command}: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "output": result.stdout,
                    "duration": duration,
                    "tool": tool_name,
                    "command": command
                }
        
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout {tool_name}:{command} after {timeout}s")
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "duration": timeout,
                "tool": tool_name,
                "command": command
            }
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Exception in {tool_name}:{command}: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": duration,
                "tool": tool_name,
                "command": command
            }
    
    def sync_projects(self, quick: bool = False) -> Dict:
        """Sync project data - the core operation"""
        print(f"\\n🔄 PROJECT SYNC {'(QUICK)' if quick else ''}")
        print("=" * 80)
        
        results = []
        total_start = time.time()
        
        # Step 1: Project Discovery
        print("1. 📦 Running project discovery...")
        discovery_result = self.run_tool("discovery", "quick-scan" if quick else "scan")
        results.append(discovery_result)
        
        if discovery_result["success"]:
            print(f"   ✅ Discovery completed in {discovery_result['duration']:.1f}s")
        else:
            print(f"   ❌ Discovery failed: {discovery_result['error']}")
        
        # Step 2: Document Parsing (only if discovery succeeded)
        if discovery_result["success"]:
            print("2. 📋 Parsing documents...")
            doc_result = self.run_tool("document_parser", "parse-changed" if quick else "scan")
            results.append(doc_result)
            
            if doc_result["success"]:
                print(f"   ✅ Document parsing completed in {doc_result['duration']:.1f}s")
            else:
                print(f"   ❌ Document parsing failed: {doc_result['error']}")
        else:
            print("2. 📋 Skipping document parsing (discovery failed)")
            results.append({"success": False, "error": "Skipped due to discovery failure"})
        
        # Step 3: Security Scan (optional, continues even if fails)
        print("3. 🔒 Running security scan...")
        security_result = self.run_tool("security", "scan")
        results.append(security_result)
        
        if security_result["success"]:
            print(f"   ✅ Security scan completed in {security_result['duration']:.1f}s")
        else:
            print(f"   ⚠️  Security scan failed: {security_result['error']}")
        
        # Step 4: Dashboard Data Generation
        print("4. 📊 Generating dashboard data...")
        dashboard_result = self.run_tool("dashboard", "generate")
        results.append(dashboard_result)
        
        if dashboard_result["success"]:
            print(f"   ✅ Dashboard generation completed in {dashboard_result['duration']:.1f}s")
        else:
            print(f"   ❌ Dashboard generation failed: {dashboard_result['error']}")
        
        total_duration = time.time() - total_start
        success_count = sum(1 for r in results if r["success"])
        
        print(f"\\n📊 SYNC SUMMARY:")
        print(f"   Total time: {total_duration:.1f}s")
        print(f"   Successful steps: {success_count}/{len(results)}")
        
        return {
            "success": success_count >= 2,  # At least discovery and one other
            "results": results,
            "total_duration": total_duration,
            "summary": {
                "steps_completed": success_count,
                "steps_total": len(results),
                "quick_mode": quick
            }
        }
    
    def health_check(self) -> Dict:
        """Comprehensive health check of all systems"""
        print(f"\\n❤️  SYSTEM HEALTH CHECK")
        print("=" * 80)
        
        health_results = {}
        
        # Check dashboard health
        print("1. 📊 Checking dashboard health...")
        dashboard_health = self.run_tool("dashboard", "health-report")
        health_results["dashboard"] = dashboard_health["success"]
        
        # Check token status
        print("2. 💰 Checking token status...")
        token_result = self.run_tool("token_tracker", "status")
        health_results["tokens"] = token_result["success"]
        
        # Check backup status
        print("3. 📦 Checking backup status...")
        backup_result = self.run_tool("backup", "status")
        health_results["backup"] = backup_result["success"]
        
        # Check project registry
        print("4. 📋 Checking project registry...")
        registry_healthy = self.project_registry_path.exists()
        if registry_healthy:
            try:
                with open(self.project_registry_path, 'r') as f:
                    registry = json.load(f)
                    project_count = len(registry.get("projects", {}))
                    print(f"   ✅ Registry healthy: {project_count} projects")
            except Exception as e:
                registry_healthy = False
                print(f"   ❌ Registry corrupted: {e}")
        else:
            print(f"   ❌ Registry missing")
        
        health_results["registry"] = registry_healthy
        
        # Overall health
        healthy_systems = sum(health_results.values())
        total_systems = len(health_results)
        overall_healthy = healthy_systems >= (total_systems * 0.75)  # 75% threshold
        
        print(f"\\n🏥 HEALTH SUMMARY:")
        print(f"   Healthy systems: {healthy_systems}/{total_systems}")
        print(f"   Overall status: {'✅ HEALTHY' if overall_healthy else '⚠️  NEEDS ATTENTION'}")
        
        return {
            "success": overall_healthy,
            "healthy_systems": healthy_systems,
            "total_systems": total_systems,
            "system_status": health_results,
            "overall_healthy": overall_healthy
        }
    
    def project_maintenance(self, dry_run: bool = False) -> Dict:
        """Run project maintenance tasks"""
        print(f"\\n🔧 PROJECT MAINTENANCE {'(DRY RUN)' if dry_run else ''}")
        print("=" * 80)
        
        maintenance_results = []
        
        # Get health alerts first
        print("1. 🚨 Checking for health alerts...")
        alerts_result = self.run_tool("dashboard", "alerts")
        
        if alerts_result["success"]:
            print("   ✅ Health alerts generated")
            # Parse alerts from output to determine actions needed
            # This is where you'd implement specific maintenance actions
            # based on the alert types found
        else:
            print("   ❌ Failed to get health alerts")
        
        maintenance_results.append(alerts_result)
        
        # Template compliance check
        print("2. 📋 Checking template compliance...")
        # This would scan projects and apply missing templates
        # For now, just report what would be done
        
        if not dry_run:
            # In a real run, this would apply templates to projects missing them
            print("   💡 Template application would be implemented here")
        else:
            print("   💡 Dry run: Would check and apply missing templates")
        
        print(f"\\n🔧 MAINTENANCE SUMMARY:")
        print(f"   Tasks completed: {len(maintenance_results)}")
        
        return {
            "success": True,
            "results": maintenance_results,
            "dry_run": dry_run
        }

def main():
    """CLI interface for master project orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Master Project Orchestrator")
    parser.add_argument("--action", 
                       choices=["sync", "health", "maintenance", "run-tool", "list-tools"], 
                       required=True)
    parser.add_argument("--quick", action="store_true", help="Quick mode for sync")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for maintenance")
    parser.add_argument("--tool", help="Tool name for run-tool action")
    parser.add_argument("--command", help="Command for run-tool action")
    parser.add_argument("--args", help="Additional arguments for run-tool action", default="")
    
    args = parser.parse_args()
    
    orchestrator = MasterProjectOrchestrator()
    
    try:
        if args.action == "sync":
            result = orchestrator.sync_projects(quick=args.quick)
            exit_code = 0 if result["success"] else 1
            
        elif args.action == "health":
            result = orchestrator.health_check()
            exit_code = 0 if result["success"] else 1
            
        elif args.action == "maintenance":
            result = orchestrator.project_maintenance(dry_run=args.dry_run)
            exit_code = 0 if result["success"] else 1
            
        elif args.action == "run-tool":
            if not args.tool or not args.command:
                print("❌ Error: --tool and --command required for run-tool action")
                exit_code = 1
            else:
                result = orchestrator.run_tool(args.tool, args.command, args.args)
                exit_code = 0 if result["success"] else 1
                
                if result["success"]:
                    print(f"✅ Tool completed successfully")
                    if result.get("output"):
                        print(result["output"])
                else:
                    print(f"❌ Tool failed: {result['error']}")
                    if result.get("output"):
                        print(result["output"])
        
        elif args.action == "list-tools":
            print(f"\\n🛠️  AVAILABLE TOOLS")
            print("=" * 80)
            
            for tool_name, tool_info in orchestrator.tools.items():
                print(f"\\n🔧 {tool_name}")
                print(f"   Description: {tool_info['description']}")
                print(f"   Script: {tool_info['script']}")
                print(f"   Commands:")
                for cmd, args in tool_info['commands'].items():
                    print(f"     • {cmd}: {args}")
            
            exit_code = 0
    
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
        exit_code = 1
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
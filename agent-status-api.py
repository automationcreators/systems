#!/usr/bin/env python3
"""
/systems/agent-status-api.py
API to provide real-time status of all system agents
Reads agent logs and provides status for dashboard integration
RELEVANT FILES: systems/daily-morning.sh, systems/*.py, Project Management/dashboard/file-server.py
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class SystemAgentStatusAPI:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"

        # Define all system agents
        self.agents = {
            "github-sync": {
                "name": "GitHub Sync Agent",
                "description": "Syncs all active projects to private GitHub repositories",
                "script": "github-sync-agent.py",
                "log_file": "github-sync.log",
                "type": "sync",
                "commands": ["sync", "status", "enable", "disable", "set-visibility"]
            },
            "project-discovery": {
                "name": "Project Discovery Service",
                "description": "Discovers and registers new projects automatically",
                "script": "project-discovery-service.py",
                "log_file": "project-discovery.log",
                "type": "discovery",
                "commands": ["scan", "sync", "status"]
            },
            "security-monitor": {
                "name": "Security Monitoring",
                "description": "Scans projects for security vulnerabilities and compliance",
                "script": "security-monitoring-dashboard.py",
                "log_file": "security-monitor.log",
                "type": "security",
                "commands": ["scan", "dashboard", "status"]
            },
            "backup-manager": {
                "name": "Backup Manager",
                "description": "Creates encrypted backups of all projects",
                "script": "backup-manager.py",
                "log_file": "backup.log",
                "type": "backup",
                "commands": ["backup", "restore", "list", "status", "cleanup"]
            },
            "todo-aggregation": {
                "name": "TODO Aggregation Engine",
                "description": "Collects and aggregates TODOs from all projects",
                "script": "todo-aggregation-engine.py",
                "log_file": "todo-aggregation.log",
                "type": "aggregation",
                "commands": []
            },
            "document-parser": {
                "name": "Document Parser",
                "description": "Parses CLAUDE.md and TODO.md files from all projects",
                "script": "document-parser.py",
                "log_file": "document-parser.log",
                "type": "parser",
                "commands": ["scan", "parse", "test"]
            },
            "storage-monitor": {
                "name": "Storage Monitor",
                "description": "Monitors disk usage and finds duplicate files",
                "script": "storage-monitor.py",
                "log_file": "storage-monitor.log",
                "type": "utility",
                "commands": ["status", "scan-duplicates", "cleanup"]
            },
            "lifecycle-manager": {
                "name": "Lifecycle Manager",
                "description": "Manages project lifecycle and suggests actions",
                "script": "lifecycle-manager.py",
                "log_file": "lifecycle.log",
                "type": "management",
                "commands": ["suggest", "status"]
            },
            "token-tracker": {
                "name": "Token Usage Tracker",
                "description": "Tracks API token consumption across agents",
                "script": "token-usage-tracker.py",
                "log_file": "token-tracker.log",
                "type": "monitoring",
                "commands": ["status", "reset"]
            },
            "dashboard-data": {
                "name": "Dashboard Data Provider",
                "description": "Generates dashboard JSON data for all projects",
                "script": "dashboard-data-provider.py",
                "log_file": "dashboard-data.log",
                "type": "integration",
                "commands": ["generate", "drilldown", "status"]
            }
        }

    def get_agent_status(self, agent_id: str) -> Dict:
        """Get detailed status for a specific agent"""
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not found"}

        agent_info = self.agents[agent_id]
        log_file = self.systems_dir / agent_info["log_file"]
        script_file = self.systems_dir / agent_info["script"]

        # Check if agent files exist
        script_exists = script_file.exists()
        log_exists = log_file.exists()

        # Parse log file for status
        last_run = None
        last_error = None
        last_success = None

        if log_exists:
            try:
                # Read last 100 lines of log
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-100:]

                for line in reversed(lines):
                    if not last_run and any(keyword in line.lower() for keyword in ["starting", "completed", "failed", "initialized"]):
                        # Extract timestamp
                        try:
                            timestamp_str = line.split(' - ')[0]
                            last_run = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f").isoformat()
                        except:
                            pass

                    if not last_error and "error" in line.lower():
                        last_error = line.strip()

                    if not last_success and ("completed" in line.lower() or "success" in line.lower()):
                        last_success = line.strip()

                    if last_run and last_error and last_success:
                        break
            except Exception as e:
                pass

        # Determine health status
        health_status = "unknown"
        health_score = 50
        issues = []

        if not script_exists:
            health_status = "critical"
            health_score = 0
            issues.append("Agent script not found")
        elif not log_exists:
            health_status = "warning"
            health_score = 60
            issues.append("No log file found - agent may not have run yet")
        elif last_run:
            # Check how long ago last run was
            try:
                last_run_time = datetime.fromisoformat(last_run)
                age_days = (datetime.now() - last_run_time).days

                if age_days > 7:
                    health_status = "critical"
                    health_score = 20
                    issues.append(f"Last run was {age_days} days ago")
                elif age_days > 2:
                    health_status = "warning"
                    health_score = 60
                    issues.append(f"Last run was {age_days} days ago")
                elif last_error and not last_success:
                    health_status = "warning"
                    health_score = 70
                    issues.append("Last run had errors")
                else:
                    health_status = "healthy"
                    health_score = 100
            except:
                health_status = "unknown"
                health_score = 50

        return {
            "id": agent_id,
            "name": agent_info["name"],
            "type": agent_info["type"],
            "description": agent_info["description"],
            "status": "active" if script_exists else "missing",
            "health": {
                "status": health_status,
                "score": health_score,
                "last_check": datetime.now().isoformat(),
                "issues": issues
            },
            "last_run": last_run,
            "last_error": last_error,
            "last_success": last_success,
            "commands": agent_info["commands"],
            "file_name": agent_info["script"],
            "script_exists": script_exists,
            "log_exists": log_exists
        }

    def get_all_agents_status(self) -> Dict:
        """Get status for all agents"""
        agents_status = []
        healthy_count = 0
        warning_count = 0
        critical_count = 0

        for agent_id in self.agents:
            status = self.get_agent_status(agent_id)
            agents_status.append(status)

            health = status["health"]["status"]
            if health == "healthy":
                healthy_count += 1
            elif health == "warning":
                warning_count += 1
            elif health == "critical":
                critical_count += 1

        # Group by category
        categories = {}
        for agent in agents_status:
            agent_type = agent["type"]
            if agent_type not in categories:
                categories[agent_type] = []
            categories[agent_type].append(agent)

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_agents": len(self.agents),
                "healthy_agents": healthy_count,
                "warning_agents": warning_count,
                "critical_agents": critical_count,
                "active_agents": len([a for a in agents_status if a["script_exists"]])
            },
            "agents": agents_status,
            "categories": categories
        }

    def save_to_dashboard(self):
        """Save agent status to dashboard data file"""
        status_data = self.get_all_agents_status()

        dashboard_path = self.base_path / "active" / "Project Management" / "dashboard" / "data" / "systems-agent-data.json"
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dashboard_path, 'w') as f:
            json.dump(status_data, f, indent=2)

        print(f"✅ Saved agent status to {dashboard_path}")
        return status_data

def main():
    import argparse

    parser = argparse.ArgumentParser(description="System Agent Status API")
    parser.add_argument("--agent", help="Get status for specific agent")
    parser.add_argument("--save", action="store_true", help="Save status to dashboard")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    api = SystemAgentStatusAPI()

    if args.agent:
        status = api.get_agent_status(args.agent)
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"\n📊 Agent: {status['name']}")
            print(f"   Status: {status['status']}")
            print(f"   Health: {status['health']['status']} ({status['health']['score']}/100)")
            if status['health']['issues']:
                print(f"   Issues: {', '.join(status['health']['issues'])}")
            if status['last_run']:
                print(f"   Last Run: {status['last_run']}")
    elif args.save:
        status = api.save_to_dashboard()
        print(f"\n📊 System Agents Summary:")
        print(f"   Total: {status['summary']['total_agents']}")
        print(f"   ✅ Healthy: {status['summary']['healthy_agents']}")
        print(f"   ⚠️  Warning: {status['summary']['warning_agents']}")
        print(f"   🔴 Critical: {status['summary']['critical_agents']}")
    else:
        status = api.get_all_agents_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"\n📊 System Agents Status:")
            print(f"   Total: {status['summary']['total_agents']}")
            print(f"   ✅ Healthy: {status['summary']['healthy_agents']}")
            print(f"   ⚠️  Warning: {status['summary']['warning_agents']}")
            print(f"   🔴 Critical: {status['summary']['critical_agents']}")
            print(f"\n📋 Agents:")
            for agent in status['agents']:
                icon = "✅" if agent['health']['status'] == "healthy" else "⚠️" if agent['health']['status'] == "warning" else "🔴"
                print(f"   {icon} {agent['name']}: {agent['health']['status']}")

if __name__ == "__main__":
    main()

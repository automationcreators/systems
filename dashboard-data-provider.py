#!/usr/bin/env python3
"""
Dashboard Data Provider
Provides real project data from Personal OS systems to the dashboard
Integrates discovery service, document parser, and security monitoring
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Import Personal OS modules
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util

def load_module(module_name, file_path):
    """Dynamically load a Python module"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class DashboardDataProvider:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        self.project_registry_path = self.base_path / "project-registry.json"
        
        # Load Personal OS modules
        try:
            self.discovery_module = load_module("discovery", self.systems_dir / "project-discovery-service.py")
            self.parser_module = load_module("parser", self.systems_dir / "document-parser.py")
            self.security_module = load_module("security", self.systems_dir / "security-monitoring-dashboard.py")
            self.token_module = load_module("tracker", self.systems_dir / "token-tracker-integration.py")
            
            # Initialize services
            self.discovery_service = self.discovery_module.ProjectDiscoveryService()
            self.document_parser = self.parser_module.DocumentParser()
            self.security_dashboard = self.security_module.SecurityMonitoringDashboard()
        except Exception as e:
            print(f"Warning: Could not load some modules: {e}")
            self.discovery_service = None
            self.document_parser = None
            self.security_dashboard = None
        
        # Load project registry directly
        self.project_registry = self.load_project_registry()
    
    def load_project_registry(self) -> dict:
        """Load main project registry"""
        try:
            with open(self.project_registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load project registry: {e}")
            return {"projects": {}, "metadata": {}}
    
    def get_project_health_score(self, project: dict) -> int:
        """Calculate overall project health (1-100) - enhanced with Personal-OS logic"""
        health = 50  # Base score
        
        # Activity bonus
        activity_score = project.get("activity_score", 0)
        if activity_score > 8:
            health += 20
        elif activity_score > 5:
            health += 10
        elif activity_score < 2:
            health -= 20
        
        # Lifecycle stage impact
        lifecycle_stage = project.get("lifecycle_stage", "unknown")
        if lifecycle_stage == "active":
            health += 15
        elif lifecycle_stage == "staging":
            health += 5
        elif lifecycle_stage == "archived":
            health -= 30
        elif lifecycle_stage == "planned":
            health -= 10
        
        # Status impact
        status = project.get("status", "unknown")
        if status == "in_progress":
            health += 15
        elif status == "selected":
            health += 10
        elif status == "blocked":
            health -= 25
        
        # Priority impact
        priority = project.get("priority", "medium")
        if priority == "highest":
            health += 10
        elif priority == "high":
            health += 5
        elif priority == "low":
            health -= 5
        
        # Size impact (very large projects may be health risks)
        size_mb = project.get("size_mb", 0)
        if size_mb > 200:
            health -= 10
        
        # Personal impact boost
        personal_impact = project.get("personal_impact", {})
        if personal_impact:
            total_impact = sum([
                personal_impact.get("productivity", 0),
                personal_impact.get("learning", 0),
                personal_impact.get("career", 0),
                personal_impact.get("enjoyment", 0)
            ])
            if total_impact > 30:
                health += 15
            elif total_impact > 20:
                health += 10
        
        return max(0, min(100, health))
    
    def get_project_drilldown_data(self, project_id: str) -> dict:
        """Get comprehensive drilldown data for a specific project"""
        # Find project in registry
        project_info = self.project_registry.get("projects", {}).get(project_id)
        
        if not project_info:
            return {"error": f"Project {project_id} not found"}
        
        project_path = Path(project_info["path"])
        
        # Get document parsing data
        document_data = self.document_parser.parse_project_documents(project_path)
        
        # Get security status
        try:
            security_data = self.security_dashboard.scan_project_security(project_path)
        except Exception as e:
            print(f"Warning: Could not scan security for {project_id}: {e}")
            security_data = {"security_score": 0, "issues": []}
        
        # Combine all data
        drilldown = {
            "id": project_id,
            "basic_info": project_info,
            "documents": document_data,
            "security": security_data,
            "files": self.get_project_files(project_path),
            "recent_activity": self.get_recent_activity(project_path),
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "data_sources": ["discovery", "documents", "security", "filesystem"]
            }
        }
        
        return drilldown
    
    def get_project_files(self, project_path: Path) -> list:
        """Get list of important project files with metadata"""
        files = []
        
        important_files = [
            "CLAUDE.md", "TODO.md", "HANDOFFS.md", "SECURITY.md", "README.md",
            "package.json", "requirements.txt", ".env.example", ".gitignore"
        ]
        
        for filename in important_files:
            file_path = project_path / filename
            if file_path.exists():
                try:
                    stat = file_path.stat()
                    files.append({
                        "name": filename,
                        "path": str(file_path),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": self.get_file_type(filename),
                        "icon": self.get_file_icon(filename)
                    })
                except Exception as e:
                    print(f"Error accessing {file_path}: {e}")
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        return files
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type for display"""
        type_mapping = {
            "CLAUDE.md": "context",
            "TODO.md": "tasks",
            "HANDOFFS.md": "automation",
            "SECURITY.md": "security",
            "README.md": "documentation",
            "package.json": "config",
            "requirements.txt": "config",
            ".env.example": "config",
            ".gitignore": "config"
        }
        return type_mapping.get(filename, "file")
    
    def get_file_icon(self, filename: str) -> str:
        """Get emoji icon for file type"""
        icon_mapping = {
            "CLAUDE.md": "🤖",
            "TODO.md": "📋",
            "HANDOFFS.md": "🔄",
            "SECURITY.md": "🔒",
            "README.md": "📖",
            "package.json": "📦",
            "requirements.txt": "🐍",
            ".env.example": "⚙️",
            ".gitignore": "🙈"
        }
        return icon_mapping.get(filename, "📄")
    
    def get_recent_activity(self, project_path: Path) -> list:
        """Get recent activity for the project"""
        activities = []
        
        # Check for recent file modifications
        for file_path in project_path.glob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Only include recent modifications (last 7 days)
                    if (datetime.now() - modified).days <= 7:
                        activities.append({
                            "type": "file_modified",
                            "timestamp": modified.isoformat(),
                            "description": f"Modified {file_path.name}",
                            "file": file_path.name
                        })
                except Exception:
                    continue
        
        # Sort by timestamp (newest first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return activities[:10]  # Return only most recent 10 activities
    
    def get_dashboard_projects_data(self) -> dict:
        """Get enhanced project data for dashboard display"""
        dashboard_data = {
            "generated_at": datetime.now().isoformat(),
            "projects": {},
            "summary": {
                "total_projects": 0,
                "active_projects": 0,
                "completed_projects": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "overall_progress": 0
            },
            "token_status": {},
            "security_summary": {}
        }
        
        # Get token usage status
        dashboard_data["token_status"] = self.token_module.check_budget()
        
        # Get security summary
        try:
            security_data = self.security_dashboard.get_security_dashboard_data()
            dashboard_data["security_summary"] = {
                "overall_score": security_data["security_overview"]["overall_score"],
                "critical_issues": security_data["issue_summary"]["critical"],
                "total_issues": security_data["issue_summary"]["total"]
            }
        except Exception as e:
            print(f"Warning: Could not load security data: {e}")
            dashboard_data["security_summary"] = {
                "overall_score": 0,
                "critical_issues": 0,
                "total_issues": 0
            }
        
        # Process each project from unified registry
        projects = self.project_registry.get("projects", {})
        total_progress = 0
        active_count = 0
        completed_count = 0
        
        for project_id, project_info in projects.items():
            project_path = Path(project_info["path"])
            
            # Get enhanced project data
            document_data = self.document_parser.parse_project_documents(project_path)
            
            enhanced_project = {
                "id": project_id,
                "title": project_info.get("title", project_id),
                "status": project_info.get("status", "unknown"),
                "type": project_info.get("type", "unknown"),
                "path": project_info["path"],
                "last_modified": project_info.get("last_modified"),
                "activity_score": project_info.get("activity_score", 0),
                "progress": document_data.get("summary", {}).get("overall_progress", 0),
                "total_tasks": document_data.get("summary", {}).get("total_tasks", 0),
                "completed_tasks": document_data.get("summary", {}).get("completed_tasks", 0),
                "priority": self.determine_priority(project_info, document_data),
                "category": self.map_category(project_info.get("type", "unknown")),
                "tags": self.extract_tags(document_data),
                "security_score": 0,  # Will be populated later
                "has_todo": bool(document_data.get("documents", {}).get("todo")),
                "has_claude_md": bool(document_data.get("documents", {}).get("claude"))
            }
            
            dashboard_data["projects"][project_id] = enhanced_project
            
            # Update summary
            total_progress += enhanced_project["progress"]
            
            if enhanced_project["status"] == "active":
                active_count += 1
            elif enhanced_project["status"] == "archived" and enhanced_project["progress"] == 100:
                completed_count += 1
            
            dashboard_data["summary"]["total_tasks"] += enhanced_project["total_tasks"]
            dashboard_data["summary"]["completed_tasks"] += enhanced_project["completed_tasks"]
        
        # Calculate summary statistics
        dashboard_data["summary"]["total_projects"] = len(projects)
        dashboard_data["summary"]["active_projects"] = active_count
        dashboard_data["summary"]["completed_projects"] = completed_count
        
        if dashboard_data["summary"]["total_projects"] > 0:
            dashboard_data["summary"]["overall_progress"] = round(total_progress / len(projects), 1)
        
        return dashboard_data
    
    def determine_priority(self, project_info: dict, document_data: dict) -> str:
        """Determine project priority based on multiple factors"""
        activity_score = project_info.get("activity_score", 0)
        status = project_info.get("status", "unknown")
        
        # Check for urgent tasks in TODO.md
        todo_data = document_data.get("documents", {}).get("todo", {})
        high_priority_tasks = len(todo_data.get("high_priority", []))
        
        if high_priority_tasks > 0 or activity_score >= 9:
            return "highest"
        elif activity_score >= 7 or status == "active":
            return "high"
        elif activity_score >= 5:
            return "medium"
        else:
            return "low"
    
    def map_category(self, project_type: str) -> str:
        """Map project type to dashboard category"""
        category_mapping = {
            "claude-project": "🤖 AI Projects",
            "development": "💻 Development",
            "development-python": "🐍 Python Development",
            "development-nodejs": "📦 Node.js Development",
            "web-project": "🌐 Web Projects",
            "data-analysis": "📊 Data Analysis",
            "automation": "⚙️ Automation",
            "system-tool": "🛠️ System Tools",
            "dashboard": "📈 Dashboards",
            "ongoing": "🔄 Ongoing"
        }
        return category_mapping.get(project_type, "📁 General")
    
    def extract_tags(self, document_data: dict) -> list:
        """Extract tags from document data"""
        tags = []
        
        # Get tags from CLAUDE.md
        claude_data = document_data.get("documents", {}).get("claude", {})
        if claude_data.get("tags"):
            tags.extend(claude_data["tags"])
        
        # Add status-based tags
        summary = document_data.get("summary", {})
        if summary.get("total_tasks", 0) > 0:
            tags.append("has-tasks")
        
        if summary.get("completion_percentage", 0) > 80:
            tags.append("near-completion")
        
        return list(set(tags))  # Remove duplicates
    
    def get_priority_matrix_data(self) -> dict:
        """Generate priority matrix data for dashboard - from Personal-OS"""
        projects = self.project_registry.get("projects", {})
        matrix = {}
        
        priority_order = ["highest", "high", "medium", "low", "unknown"]
        phase_order = ["immediate", "short-term", "medium-term", "long-term", "unknown"]
        
        for priority in priority_order:
            matrix[priority] = {}
            for phase in phase_order:
                matrix[priority][phase] = []
        
        for project_id, project in projects.items():
            priority = project.get("priority", "unknown")
            phase = project.get("phase", "unknown")
            
            # Map unexpected phase values to known phases
            if phase not in phase_order:
                phase = "unknown"
            
            health_score = self.get_project_health_score(project)
            
            matrix_entry = {
                "id": project_id,
                "name": project.get("name", project_id),
                "title": project.get("title", ""),
                "lifecycle_stage": project.get("lifecycle_stage", "unknown"),
                "health_score": health_score,
                "activity_score": project.get("activity_score", 0),
                "personal_impact": project.get("personal_impact", {}),
                "estimated_effort": project.get("estimated_effort", "unknown"),
                "path": project.get("path", "")
            }
            
            matrix[priority][phase].append(matrix_entry)
        
        # Sort projects within each cell by health score (descending)
        for priority in matrix:
            for phase in matrix[priority]:
                matrix[priority][phase].sort(key=lambda x: x["health_score"], reverse=True)
        
        return {
            "matrix": matrix,
            "summary": {
                "total_projects": len(projects),
                "by_priority": {p: sum(len(matrix[p][ph]) for ph in phase_order) for p in priority_order},
                "by_phase": {ph: sum(len(matrix[p][ph]) for p in priority_order) for ph in phase_order},
                "high_health_count": sum(1 for p in projects.values() if self.get_project_health_score(p) > 70),
                "low_health_count": sum(1 for p in projects.values() if self.get_project_health_score(p) < 40)
            }
        }
    
    def get_health_alerts(self) -> dict:
        """Get projects that need attention - from Personal-OS"""
        projects = self.project_registry.get("projects", {})
        alerts = {
            "blocked": [],
            "stale": [],
            "large_inactive": [],
            "low_health": [],
            "missing_data": []
        }
        
        for project_id, project in projects.items():
            # Blocked projects
            if project.get("status") == "blocked":
                alerts["blocked"].append({
                    "id": project_id,
                    "name": project.get("name", project_id),
                    "reason": project.get("blocked_reason", "No reason specified")
                })
            
            # Low health projects
            health_score = self.get_project_health_score(project)
            if health_score < 40:
                alerts["low_health"].append({
                    "id": project_id,
                    "name": project.get("name", project_id),
                    "health_score": health_score,
                    "lifecycle_stage": project.get("lifecycle_stage", "unknown")
                })
            
            # Stale projects (active but no recent activity)
            if project.get("lifecycle_stage") == "active" and project.get("activity_score", 0) < 2:
                alerts["stale"].append({
                    "id": project_id,
                    "name": project.get("name", project_id),
                    "activity_score": project.get("activity_score", 0),
                    "last_modified": project.get("last_modified", "")
                })
            
            # Large inactive projects
            if (project.get("size_mb", 0) > 100 and 
                project.get("activity_score", 0) < 3 and 
                project.get("lifecycle_stage") in ["active", "staging"]):
                alerts["large_inactive"].append({
                    "id": project_id,
                    "name": project.get("name", project_id),
                    "size_mb": project.get("size_mb", 0),
                    "activity_score": project.get("activity_score", 0)
                })
            
            # Missing critical data
            missing_fields = []
            if not project.get("title"):
                missing_fields.append("title")
            if not project.get("lifecycle_stage"):
                missing_fields.append("lifecycle_stage")
            if not project.get("priority"):
                missing_fields.append("priority")
            
            if missing_fields:
                alerts["missing_data"].append({
                    "id": project_id,
                    "name": project.get("name", project_id),
                    "missing_fields": missing_fields
                })
        
        return alerts
    
    def save_dashboard_data(self):
        """Save enhanced dashboard data to JSON file"""
        dashboard_data = self.get_dashboard_projects_data()
        
        # Save to multiple locations for different consumers
        output_files = [
            self.systems_dir / "dashboard-projects-data.json",
            self.base_path / "active" / "Project Management" / "dashboard" / "projects-data.json"
        ]
        
        for output_file in output_files:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2)
            
            print(f"✅ Dashboard data saved to: {output_file}")
        
        return dashboard_data

def main():
    """CLI interface for dashboard data provider"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Dashboard Data Provider")
    parser.add_argument("--action", choices=["generate", "drilldown", "refresh", "matrix", "alerts", "health-report"], required=True)
    parser.add_argument("--project", help="Project ID for drilldown")
    
    args = parser.parse_args()
    
    provider = DashboardDataProvider()
    
    try:
        if args.action == "generate":
            data = provider.save_dashboard_data()
            
            print("📊 Dashboard Data Generated:")
            print(f"  Total Projects: {data['summary']['total_projects']}")
            print(f"  Active Projects: {data['summary']['active_projects']}")
            print(f"  Overall Progress: {data['summary']['overall_progress']}%")
            print(f"  Total Tasks: {data['summary']['total_tasks']}")
            print(f"  Security Score: {data['security_summary']['overall_score']}/100")
            
            # Show token usage
            token_status = data['token_status']
            print(f"  Token Usage: {token_status['weekly']['used']}/{token_status['weekly']['budget']} weekly")
        
        elif args.action == "drilldown":
            if not args.project:
                print("❌ Error: --project required for drilldown action")
                return
            
            data = provider.get_project_drilldown_data(args.project)
            
            if "error" in data:
                print(f"❌ {data['error']}")
                return
            
            print(f"🔍 Project Drilldown: {args.project}")
            print(f"  Title: {data['basic_info'].get('title', 'Unknown')}")
            print(f"  Type: {data['basic_info'].get('type', 'Unknown')}")
            print(f"  Status: {data['basic_info'].get('status', 'Unknown')}")
            print(f"  Progress: {data['documents']['summary']['overall_progress']}%")
            print(f"  Security Score: {data['security']['security_score']}/100")
            print(f"  Files: {len(data['files'])} important files")
            print(f"  Recent Activity: {len(data['recent_activity'])} actions")
            
            # Save drilldown data for dashboard
            drilldown_file = provider.systems_dir / f"project-{args.project}-drilldown.json"
            with open(drilldown_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  📁 Drilldown data saved to: {drilldown_file}")
        
        elif args.action == "refresh":
            # Trigger refresh of all data sources
            print("🔄 Refreshing all data sources...")
            
            # Run discovery scan
            discovered = provider.discovery_service.discover_all_projects()
            print(f"  📦 Discovery: {discovered} projects updated")
            
            # Run document parsing
            doc_results = provider.document_parser.scan_all_projects()
            print(f"  📋 Documents: {doc_results['summary']['total_projects']} projects parsed")
            
            # Run security scan
            security_report = provider.security_dashboard.generate_comprehensive_security_report()
            print(f"  🔒 Security: {security_report['total_projects_scanned']} projects scanned")
            
            # Generate final dashboard data
            data = provider.save_dashboard_data()
            print(f"  💾 Dashboard data generated with {data['summary']['total_projects']} projects")
        
        elif args.action == "matrix":
            matrix_data = provider.get_priority_matrix_data()
            print(f"\n📋 PROJECT PRIORITY MATRIX")
            print("=" * 80)
            
            for priority in ["highest", "high", "medium", "low", "unknown"]:
                if matrix_data["summary"]["by_priority"][priority] > 0:
                    print(f"\n🎯 {priority.upper()} PRIORITY ({matrix_data['summary']['by_priority'][priority]} projects):")
                    for phase in ["immediate", "short-term", "medium-term", "long-term", "unknown"]:
                        projects_in_phase = matrix_data["matrix"][priority][phase]
                        if projects_in_phase:
                            print(f"  📅 {phase.title()} ({len(projects_in_phase)} projects):")
                            for project in projects_in_phase[:5]:  # Show top 5
                                health_emoji = "🟢" if project["health_score"] > 70 else "🟡" if project["health_score"] > 40 else "🔴"
                                lifecycle_emoji = {"active": "🟢", "staging": "🟡", "planned": "🔵", "archived": "⚫"}.get(project["lifecycle_stage"], "❓")
                                print(f"    {health_emoji}{lifecycle_emoji} {project['name']} (Health: {project['health_score']})")
        
        elif args.action == "alerts":
            alerts = provider.get_health_alerts()
            print(f"\n⚠️  PROJECT HEALTH ALERTS")
            print("=" * 80)
            
            total_alerts = sum(len(alert_list) for alert_list in alerts.values())
            if total_alerts == 0:
                print("✅ No critical issues detected!")
            else:
                for alert_type, alert_list in alerts.items():
                    if alert_list:
                        type_names = {
                            "blocked": "🚫 BLOCKED PROJECTS",
                            "stale": "🕐 STALE PROJECTS",
                            "large_inactive": "💾 LARGE INACTIVE PROJECTS", 
                            "low_health": "❤️ LOW HEALTH PROJECTS",
                            "missing_data": "📝 MISSING DATA"
                        }
                        print(f"\n{type_names[alert_type]} ({len(alert_list)}):")
                        for alert in alert_list[:5]:  # Show top 5
                            if alert_type == "blocked":
                                print(f"   • {alert['name']} - {alert['reason']}")
                            elif alert_type == "low_health":
                                print(f"   • {alert['name']} - Health: {alert['health_score']}/100")
                            elif alert_type == "large_inactive":
                                print(f"   • {alert['name']} - {alert['size_mb']:.1f}MB, Activity: {alert['activity_score']}")
                            elif alert_type == "missing_data":
                                print(f"   • {alert['name']} - Missing: {', '.join(alert['missing_fields'])}")
                            else:
                                print(f"   • {alert['name']}")
        
        elif args.action == "health-report":
            projects = provider.project_registry.get("projects", {})
            health_scores = [(pid, provider.get_project_health_score(p)) for pid, p in projects.items()]
            health_scores.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\n❤️ PROJECT HEALTH REPORT")
            print("=" * 80)
            print(f"Total Projects: {len(projects)}")
            
            healthy = len([h for _, h in health_scores if h > 70])
            moderate = len([h for _, h in health_scores if 40 <= h <= 70])
            poor = len([h for _, h in health_scores if h < 40])
            
            print(f"🟢 Healthy (70+): {healthy}")
            print(f"🟡 Moderate (40-70): {moderate}")
            print(f"🔴 Poor (<40): {poor}")
            
            print(f"\n🏆 TOP 10 HEALTHIEST PROJECTS:")
            for pid, health in health_scores[:10]:
                project = projects[pid]
                print(f"   {health:3d}/100 - {project.get('name', pid)} ({project.get('lifecycle_stage', 'unknown')})")
            
            if poor > 0:
                print(f"\n⚠️ PROJECTS NEEDING ATTENTION:")
                for pid, health in health_scores[-5:]:
                    project = projects[pid]
                    print(f"   {health:3d}/100 - {project.get('name', pid)} ({project.get('lifecycle_stage', 'unknown')})")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
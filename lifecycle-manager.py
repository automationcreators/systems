#!/usr/bin/env python3
"""
Personal OS Project Lifecycle Manager
Handles project discovery, categorization, archiving, and cleanup automation
"""

import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
import subprocess

class ProjectLifecycleManager:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.active_dir = self.base_path / "active"
        self.staging_dir = self.base_path / "staging"
        self.archive_dir = self.base_path / "archive"
        self.systems_dir = self.base_path / "systems"
        
        # Ensure directories exist
        for directory in [self.active_dir, self.staging_dir, self.archive_dir, self.systems_dir]:
            directory.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Project metadata
        self.metadata_file = self.base_path / "project-registry.json"
        self.load_project_registry()
    
    def setup_logging(self):
        """Setup lifecycle event logging"""
        log_file = self.base_path / "systems" / "lifecycle.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_project_registry(self):
        """Load project metadata registry"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.project_registry = json.load(f)
        else:
            self.project_registry = {
                "projects": {},
                "last_updated": datetime.now().isoformat(),
                "settings": {
                    "auto_archive_days": 30,
                    "cleanup_check_interval": 7,
                    "backup_retention_days": 30
                }
            }
        
        self.save_project_registry()
    
    def save_project_registry(self):
        """Save project metadata registry"""
        self.project_registry["last_updated"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w') as f:
            json.dump(self.project_registry, f, indent=2)
    
    def discover_projects(self, scan_root=None) -> List[Dict]:
        """Discover all projects in the filesystem"""
        if not scan_root:
            scan_root = self.base_path
        
        scan_root = Path(scan_root)
        discovered_projects = []
        
        # Scan for project directories
        for item in scan_root.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['systems', 'active', 'staging', 'archive']:
                project_info = self.analyze_project(item)
                if project_info:
                    discovered_projects.append(project_info)
                    
                    # Update registry
                    project_id = project_info['id']
                    if project_id not in self.project_registry['projects']:
                        self.project_registry['projects'][project_id] = project_info
                        self.logger.info(f"Discovered new project: {project_id}")
                    else:
                        # Update existing project metadata
                        self.project_registry['projects'][project_id].update(project_info)
        
        self.save_project_registry()
        return discovered_projects
    
    def analyze_project(self, project_path: Path) -> Optional[Dict]:
        """Analyze a project directory to determine its type and metadata"""
        project_info = {
            "id": project_path.name,
            "name": project_path.name,
            "path": str(project_path),
            "discovered_at": datetime.now().isoformat(),
            "last_modified": datetime.fromtimestamp(project_path.stat().st_mtime).isoformat(),
            "size_mb": self.get_directory_size(project_path),
            "file_count": len(list(project_path.rglob('*'))),
        }
        
        # Determine project type based on contents
        project_type = self.classify_project_type(project_path)
        project_info["type"] = project_type
        
        # Analyze activity level
        activity_score = self.calculate_activity_score(project_path)
        project_info["activity_score"] = activity_score
        
        # Determine current lifecycle stage
        current_stage = self.determine_lifecycle_stage(project_path)
        project_info["lifecycle_stage"] = current_stage
        
        # Look for project metadata files
        metadata = self.extract_project_metadata(project_path)
        project_info.update(metadata)
        
        return project_info
    
    def classify_project_type(self, project_path: Path) -> str:
        """Classify project type based on directory contents"""
        files = list(project_path.rglob('*'))
        file_extensions = [f.suffix.lower() for f in files if f.is_file()]
        file_names = [f.name.lower() for f in files if f.is_file()]
        
        # Check for specific markers
        if any(name in file_names for name in ['package.json', 'requirements.txt', 'cargo.toml', 'go.mod']):
            return "development"
        
        if any(name in file_names for name in ['claude.md', 'project-notes.md', 'todo.md']):
            return "claude-project"
        
        if '.py' in file_extensions and any('scraper' in str(f).lower() for f in files):
            return "scraper"
        
        if any(ext in file_extensions for ext in ['.csv', '.xlsx', '.json']) and len(files) < 50:
            return "data-analysis"
        
        if any(name in file_names for name in ['dashboard.html', 'index.html']):
            return "dashboard"
        
        # Check activity pattern
        if len(files) < 10:
            return "one-off"
        elif any('system' in str(f).lower() or 'tool' in str(f).lower() for f in files):
            return "system-tool"
        else:
            return "ongoing"
    
    def calculate_activity_score(self, project_path: Path) -> float:
        """Calculate project activity score based on recent file modifications"""
        now = datetime.now()
        total_score = 0.0
        file_count = 0
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                file_count += 1
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                days_ago = (now - mod_time).days
                
                # Score based on recency (higher = more recent)
                if days_ago == 0:
                    total_score += 10.0
                elif days_ago <= 7:
                    total_score += 5.0
                elif days_ago <= 30:
                    total_score += 2.0
                elif days_ago <= 90:
                    total_score += 1.0
        
        return total_score / max(file_count, 1)
    
    def determine_lifecycle_stage(self, project_path: Path) -> str:
        """Determine current lifecycle stage of project"""
        parent_dir = project_path.parent.name
        
        if parent_dir == "active":
            return "active"
        elif parent_dir == "staging":
            return "staging"
        elif parent_dir == "archive":
            return "archived"
        elif parent_dir == "systems":
            return "system"
        else:
            # Determine based on activity and location
            activity_score = self.calculate_activity_score(project_path)
            
            if activity_score > 5.0:
                return "should_be_active"
            elif activity_score > 1.0:
                return "should_be_staging"
            else:
                return "should_be_archived"
    
    def extract_project_metadata(self, project_path: Path) -> Dict:
        """Extract metadata from project files"""
        metadata = {}
        
        # Look for CLAUDE.md
        claude_file = project_path / "CLAUDE.md"
        if claude_file.exists():
            try:
                content = claude_file.read_text()
                # Extract title from first # header
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        metadata["title"] = line[2:].strip()
                        break
                
                # Look for tags or categories
                if "Tags:" in content:
                    tag_line = [line for line in lines if "Tags:" in line][0]
                    tags = tag_line.split("Tags:")[1].strip().split(",")
                    metadata["tags"] = [tag.strip() for tag in tags]
                    
            except Exception as e:
                self.logger.warning(f"Could not parse CLAUDE.md in {project_path}: {e}")
        
        # Look for package.json for Node projects
        package_file = project_path / "package.json"
        if package_file.exists():
            try:
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                metadata["title"] = package_data.get("name", metadata.get("title"))
                metadata["description"] = package_data.get("description")
            except Exception as e:
                self.logger.warning(f"Could not parse package.json in {project_path}: {e}")
        
        return metadata
    
    def get_directory_size(self, path: Path) -> float:
        """Get directory size in MB"""
        total_size = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            self.logger.warning(f"Could not calculate size for {path}: {e}")
        
        return round(total_size / (1024 * 1024), 2)
    
    def suggest_lifecycle_actions(self) -> List[Dict]:
        """Suggest lifecycle actions for projects"""
        suggestions = []
        
        for project_id, project_info in self.project_registry['projects'].items():
            project_path = Path(project_info['path'])
            
            if not project_path.exists():
                suggestions.append({
                    "action": "remove_registry_entry",
                    "project": project_id,
                    "reason": "Project directory no longer exists",
                    "priority": "high"
                })
                continue
            
            # Check if project should be moved
            current_stage = project_info['lifecycle_stage']
            activity_score = project_info.get('activity_score', 0)
            last_modified = datetime.fromisoformat(project_info['last_modified'])
            days_inactive = (datetime.now() - last_modified).days
            
            if current_stage in ['should_be_active', 'should_be_staging', 'should_be_archived']:
                target_stage = current_stage.replace('should_be_', '')
                suggestions.append({
                    "action": "move_project",
                    "project": project_id,
                    "from": project_info['path'],
                    "to": target_stage,
                    "reason": f"Activity score: {activity_score:.1f}, {days_inactive} days inactive",
                    "priority": "medium"
                })
            
            # Check for auto-archiving
            if days_inactive > self.project_registry['settings']['auto_archive_days'] and current_stage not in ['archived', 'system']:
                suggestions.append({
                    "action": "auto_archive",
                    "project": project_id,
                    "reason": f"Inactive for {days_inactive} days (threshold: {self.project_registry['settings']['auto_archive_days']})",
                    "priority": "low"
                })
            
            # Check for large projects that might need cleanup
            if project_info['size_mb'] > 100:
                suggestions.append({
                    "action": "review_cleanup",
                    "project": project_id,
                    "reason": f"Large project: {project_info['size_mb']}MB",
                    "priority": "low"
                })
        
        return suggestions
    
    def execute_lifecycle_action(self, action: Dict) -> bool:
        """Execute a lifecycle action"""
        try:
            if action['action'] == 'move_project':
                return self.move_project(action['project'], action['to'])
            
            elif action['action'] == 'auto_archive':
                return self.archive_project(action['project'])
            
            elif action['action'] == 'remove_registry_entry':
                del self.project_registry['projects'][action['project']]
                self.save_project_registry()
                self.logger.info(f"Removed registry entry for {action['project']}")
                return True
            
            elif action['action'] == 'review_cleanup':
                # This requires manual intervention
                self.logger.info(f"Manual review needed for {action['project']}: {action['reason']}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute action {action['action']} for {action['project']}: {e}")
            return False
        
        return False
    
    def move_project(self, project_id: str, target_stage: str) -> bool:
        """Move project to appropriate lifecycle stage"""
        if project_id not in self.project_registry['projects']:
            self.logger.error(f"Project {project_id} not found in registry")
            return False
        
        project_info = self.project_registry['projects'][project_id]
        current_path = Path(project_info['path'])
        
        # Determine target directory
        target_dirs = {
            'active': self.active_dir,
            'staging': self.staging_dir,
            'archived': self.archive_dir,
            'system': self.systems_dir
        }
        
        if target_stage not in target_dirs:
            self.logger.error(f"Invalid target stage: {target_stage}")
            return False
        
        target_dir = target_dirs[target_stage]
        target_path = target_dir / project_id
        
        if target_path.exists():
            self.logger.error(f"Target path already exists: {target_path}")
            return False
        
        try:
            shutil.move(str(current_path), str(target_path))
            
            # Update registry
            project_info['path'] = str(target_path)
            project_info['lifecycle_stage'] = target_stage
            project_info['moved_at'] = datetime.now().isoformat()
            
            self.save_project_registry()
            self.logger.info(f"Moved project {project_id} to {target_stage}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move project {project_id}: {e}")
            return False
    
    def archive_project(self, project_id: str) -> bool:
        """Archive a project"""
        return self.move_project(project_id, 'archived')
    
    def cleanup_old_archives(self, days_old: int = 365) -> List[str]:
        """Identify archives older than specified days for cleanup"""
        old_archives = []
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for project_id, project_info in self.project_registry['projects'].items():
            if project_info['lifecycle_stage'] == 'archived':
                last_modified = datetime.fromisoformat(project_info['last_modified'])
                if last_modified < cutoff_date:
                    old_archives.append(project_id)
        
        return old_archives
    
    def generate_lifecycle_report(self) -> Dict:
        """Generate comprehensive lifecycle report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_projects": len(self.project_registry['projects']),
            "by_stage": {},
            "by_type": {},
            "total_size_mb": 0,
            "suggestions": self.suggest_lifecycle_actions(),
            "old_archives": self.cleanup_old_archives()
        }
        
        # Analyze by stage and type
        for project_info in self.project_registry['projects'].values():
            stage = project_info['lifecycle_stage']
            proj_type = project_info.get('type', 'unknown')
            
            report['by_stage'][stage] = report['by_stage'].get(stage, 0) + 1
            report['by_type'][proj_type] = report['by_type'].get(proj_type, 0) + 1
            report['total_size_mb'] += project_info.get('size_mb', 0)
        
        return report

def main():
    """CLI interface for lifecycle management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Personal OS Project Lifecycle Manager")
    parser.add_argument("--action", choices=["discover", "report", "suggest", "execute", "move", "archive"], required=True)
    parser.add_argument("--project", help="Project ID")
    parser.add_argument("--stage", choices=["active", "staging", "archived", "system"], help="Target stage")
    parser.add_argument("--auto", action="store_true", help="Auto-execute safe suggestions")
    
    args = parser.parse_args()
    
    manager = ProjectLifecycleManager()
    
    try:
        if args.action == "discover":
            projects = manager.discover_projects()
            print(f"✅ Discovered {len(projects)} projects")
            for project in projects:
                print(f"  • {project['id']} ({project['type']}) - {project['lifecycle_stage']}")
        
        elif args.action == "report":
            report = manager.generate_lifecycle_report()
            print(f"\n📊 Lifecycle Report:")
            print(f"  Total projects: {report['total_projects']}")
            print(f"  Total size: {report['total_size_mb']:.1f} MB")
            print(f"  By stage: {report['by_stage']}")
            print(f"  By type: {report['by_type']}")
            print(f"  Suggestions: {len(report['suggestions'])}")
            print(f"  Old archives: {len(report['old_archives'])}")
        
        elif args.action == "suggest":
            suggestions = manager.suggest_lifecycle_actions()
            print(f"\n💡 Lifecycle Suggestions ({len(suggestions)}):")
            for suggestion in suggestions:
                print(f"  • {suggestion['action']}: {suggestion['project']} - {suggestion['reason']}")
        
        elif args.action == "move":
            if not args.project or not args.stage:
                print("Error: --project and --stage required for move action")
                return
            
            success = manager.move_project(args.project, args.stage)
            if success:
                print(f"✅ Moved {args.project} to {args.stage}")
            else:
                print(f"❌ Failed to move {args.project}")
        
        elif args.action == "archive":
            if not args.project:
                print("Error: --project required for archive action")
                return
            
            success = manager.archive_project(args.project)
            if success:
                print(f"✅ Archived {args.project}")
            else:
                print(f"❌ Failed to archive {args.project}")
        
        elif args.action == "execute":
            suggestions = manager.suggest_lifecycle_actions()
            
            if args.auto:
                # Auto-execute low-risk suggestions
                executed = 0
                for suggestion in suggestions:
                    if suggestion['priority'] in ['low', 'medium'] and suggestion['action'] != 'review_cleanup':
                        if manager.execute_lifecycle_action(suggestion):
                            executed += 1
                            print(f"✅ Executed: {suggestion['action']} for {suggestion['project']}")
                
                print(f"\n🤖 Auto-executed {executed} suggestions")
            else:
                # Interactive mode
                for suggestion in suggestions:
                    print(f"\n💡 {suggestion['action']}: {suggestion['project']}")
                    print(f"   Reason: {suggestion['reason']}")
                    response = input("   Execute? (y/n/q): ").lower().strip()
                    
                    if response == 'q':
                        break
                    elif response == 'y':
                        if manager.execute_lifecycle_action(suggestion):
                            print("   ✅ Executed")
                        else:
                            print("   ❌ Failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
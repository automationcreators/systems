#!/usr/bin/env python3
"""
Real-Time Project Discovery Service
Monitors file system for new projects and syncs with dashboard
Zero token usage - pure rule-based detection
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import importlib.util

# Token tracking integration
import sys
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("token_tracker", Path(__file__).parent / "token-tracker-integration.py")
tracker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker_module)

class ProjectDiscoveryHandler(FileSystemEventHandler):
    def __init__(self, discovery_service):
        self.discovery_service = discovery_service
        self.logger = discovery_service.logger
    
    def on_created(self, event):
        if event.is_directory:
            self.logger.info(f"New directory detected: {event.src_path}")
            # Delay slightly to allow directory to be fully created
            threading.Timer(2.0, self.discovery_service.check_new_project, [event.src_path]).start()
    
    def on_modified(self, event):
        # Check for modifications to project files
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.name in ['CLAUDE.md', 'TODO.md', 'package.json', 'requirements.txt']:
                self.discovery_service.queue_project_update(file_path.parent)

class ProjectDiscoveryService:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        
        # Watch these directories for new projects
        self.watch_dirs = [
            self.base_path,
            self.base_path / "active",
            self.base_path / "staging", 
            self.base_path / "archive"
        ]
        
        # Registry and state files
        self.registry_file = self.base_path / "project-registry.json"
        self.dashboard_sync_file = self.systems_dir / "dashboard-sync.json"
        self.update_queue_file = self.systems_dir / "project-updates.json"
        
        # Setup logging
        self.setup_logging()
        
        # Load current state
        self.load_registry()
        self.known_projects = set(self.registry.get("projects", {}).keys())
        
        # Update queue for batching changes
        self.update_queue = set()
        self.last_sync = datetime.now()
        
        # File system observer
        self.observer = None
        
        self.logger.info("Project Discovery Service initialized")
    
    def setup_logging(self):
        """Setup discovery service logging"""
        log_file = self.systems_dir / "project-discovery.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_registry(self):
        """Load existing project registry"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                "projects": {},
                "last_updated": datetime.now().isoformat(),
                "discovery_settings": {
                    "auto_discovery": True,
                    "sync_frequency_minutes": 5,
                    "watch_patterns": ["CLAUDE.md", "TODO.md", "package.json", "requirements.txt"]
                }
            }
    
    def save_registry(self):
        """Save project registry"""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def is_project_directory(self, path: Path) -> bool:
        """Determine if directory is a project using rules-based detection"""
        if not path.is_dir():
            return False
        
        # Skip system directories
        skip_dirs = {'.git', '.venv', 'node_modules', '__pycache__', '.DS_Store', 
                    'systems', '.vault', 'backups'}
        if path.name in skip_dirs:
            return False
        
        # Check for project indicators
        project_indicators = [
            'CLAUDE.md',       # Claude project marker
            'package.json',    # Node.js project
            'requirements.txt', # Python project
            'Cargo.toml',      # Rust project
            'go.mod',          # Go project
            'README.md',       # General project
            'index.html',      # Web project
            '.gitignore'       # Git project
        ]
        
        # Count indicators present
        indicators_found = 0
        for indicator in project_indicators:
            if (path / indicator).exists():
                indicators_found += 1
        
        # Multiple files indicate a project, or certain key files
        key_indicators = {'CLAUDE.md', 'package.json', 'requirements.txt'}
        has_key_indicator = any((path / indicator).exists() for indicator in key_indicators)
        
        return indicators_found >= 2 or has_key_indicator
    
    def analyze_project_quick(self, path: Path) -> Dict:
        """Quick project analysis using rules (no AI tokens)"""
        project_info = {
            "id": path.name,
            "name": path.name,
            "path": str(path),
            "discovered_at": datetime.now().isoformat(),
            "type": "unknown",
            "status": "discovered",
            "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
        
        # Determine project type based on files present
        if (path / "CLAUDE.md").exists():
            project_info["type"] = "claude-project"
        elif (path / "package.json").exists():
            project_info["type"] = "development-nodejs"
        elif (path / "requirements.txt").exists():
            project_info["type"] = "development-python"
        elif (path / "index.html").exists():
            project_info["type"] = "web-project"
        elif len([f for f in path.glob("*.csv")]) > 0:
            project_info["type"] = "data-analysis"
        elif any(word in path.name.lower() for word in ['scraper', 'bot', 'crawler']):
            project_info["type"] = "automation"
        else:
            # Check file patterns for more clues
            py_files = len([f for f in path.glob("*.py")])
            js_files = len([f for f in path.glob("*.js")])
            
            if py_files > js_files:
                project_info["type"] = "development-python"
            elif js_files > 0:
                project_info["type"] = "development-web"
            else:
                project_info["type"] = "general"
        
        # Determine current stage based on location
        parent_name = path.parent.name
        if parent_name == "active":
            project_info["status"] = "active"
        elif parent_name == "staging":
            project_info["status"] = "staging"
        elif parent_name == "archive":
            project_info["status"] = "archived"
        else:
            project_info["status"] = "discovered"  # Needs manual classification
        
        return project_info
    
    def check_new_project(self, path_str: str):
        """Check if new directory is a project and register it"""
        path = Path(path_str)
        
        # Check if it's a potential new project directory
        is_new_project = False
        if path.is_dir() and path.parent.name in ['active', 'staging', 'archive']:
            # This is a new folder in one of our watched directories
            is_new_project = True
            project_id = path.name
            
            if project_id not in self.known_projects:
                self.logger.info(f"New folder detected: {path}")
                
                # Trigger template inheritance for new folders
                self.apply_template_inheritance(path)
                
                # Re-check if it's now a project after template application
                if self.is_project_directory(path):
                    # New project detected!
                    project_info = self.analyze_project_quick(path)
                    
                    # Add to registry
                    self.registry["projects"][project_id] = project_info
                    self.known_projects.add(project_id)
                    self.save_registry()
                    
                    # Queue for dashboard sync
                    self.queue_dashboard_sync(project_info)
                    
                    # Track token usage for discovery operation
                    tracker_module.track_discovery_operation()
                    
                    self.logger.info(f"New project registered: {project_id} ({project_info['type']})")
                    return True
                else:
                    self.logger.info(f"New folder {project_id} created but needs manual project setup")
                    return False
        
        # Existing logic for checking if directory is already a project
        if not self.is_project_directory(path):
            self.logger.debug(f"Directory is not a project: {path}")
            return False
        
        project_id = path.name
        if project_id in self.known_projects:
            self.logger.debug(f"Project already known: {project_id}")
            return False
        
        # Existing project detected
        project_info = self.analyze_project_quick(path)
        
        # Add to registry
        self.registry["projects"][project_id] = project_info
        self.known_projects.add(project_id)
        self.save_registry()
        
        # Queue for dashboard sync
        self.queue_dashboard_sync(project_info)
        
        # Track token usage for discovery operation
        tracker_module.track_discovery_operation()
        
        self.logger.info(f"Existing project registered: {project_id} ({project_info['type']})")
        return True
    
    def apply_template_inheritance(self, project_path: Path):
        """Apply template inheritance to new project folder"""
        try:
            # Import template generator
            template_generator_path = self.systems_dir / "secure-template-generator.py"
            if template_generator_path.exists():
                spec = importlib.util.spec_from_file_location("template_gen", template_generator_path)
                template_gen = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(template_gen)
                
                # Initialize template generator
                generator = template_gen.SecureTemplateGenerator(self.base_path)
                
                # Detect project type and apply appropriate template
                project_type = self.detect_project_type(project_path)
                
                # Apply template inheritance
                generator.apply_project_template(project_path, project_type)
                
                self.logger.info(f"Applied {project_type} template to {project_path.name}")
                
        except Exception as e:
            self.logger.error(f"Failed to apply template inheritance: {e}")
    
    def detect_project_type(self, project_path: Path) -> str:
        """Detect project type based on existing files and directory structure"""
        # Check for specific project indicators
        if (project_path / "package.json").exists():
            return "nodejs"
        elif (project_path / "requirements.txt").exists() or any(project_path.glob("*.py")):
            return "python"
        elif (project_path / "Cargo.toml").exists():
            return "rust"
        elif (project_path / "go.mod").exists():
            return "golang"
        elif any(project_path.glob("*.html")) or any(project_path.glob("*.css")) or any(project_path.glob("*.js")):
            return "web"
        elif any(project_path.glob("*.md")):
            return "documentation"
        else:
            return "general"
    
    def queue_project_update(self, project_path: Path):
        """Queue project for update due to file changes"""
        project_id = project_path.name
        if project_id in self.known_projects:
            self.update_queue.add(project_id)
            self.logger.debug(f"Queued update for project: {project_id}")
    
    def process_update_queue(self):
        """Process queued project updates"""
        if not self.update_queue:
            return
        
        for project_id in list(self.update_queue):
            if project_id in self.registry["projects"]:
                project_path = Path(self.registry["projects"][project_id]["path"])
                if project_path.exists():
                    # Update project info
                    updated_info = self.analyze_project_quick(project_path)
                    self.registry["projects"][project_id].update(updated_info)
                    self.registry["projects"][project_id]["last_updated"] = datetime.now().isoformat()
                    
                    # Queue for dashboard sync
                    self.queue_dashboard_sync(self.registry["projects"][project_id])
                    
                    self.logger.info(f"Updated project: {project_id}")
        
        # Clear processed updates
        self.update_queue.clear()
        self.save_registry()
    
    def queue_dashboard_sync(self, project_info: Dict):
        """Queue project for dashboard synchronization"""
        try:
            # Load existing sync queue
            if self.dashboard_sync_file.exists():
                with open(self.dashboard_sync_file, 'r') as f:
                    sync_data = json.load(f)
            else:
                sync_data = {
                    "pending_updates": [],
                    "last_sync": datetime.now().isoformat()
                }
            
            # Add project to sync queue
            sync_data["pending_updates"].append({
                "project_id": project_info["id"],
                "action": "update",
                "data": project_info,
                "timestamp": datetime.now().isoformat()
            })
            
            # Save sync queue
            with open(self.dashboard_sync_file, 'w') as f:
                json.dump(sync_data, f, indent=2)
            
            self.logger.debug(f"Queued dashboard sync for: {project_info['id']}")
            
        except Exception as e:
            self.logger.error(f"Failed to queue dashboard sync: {e}")
    
    def sync_with_dashboard(self):
        """Synchronize pending changes with dashboard"""
        if not self.dashboard_sync_file.exists():
            return
        
        try:
            with open(self.dashboard_sync_file, 'r') as f:
                sync_data = json.load(f)
            
            if not sync_data["pending_updates"]:
                return
            
            # Update dashboard data files
            self.update_dashboard_data(sync_data["pending_updates"])
            
            # Clear pending updates
            sync_data["pending_updates"] = []
            sync_data["last_sync"] = datetime.now().isoformat()
            
            with open(self.dashboard_sync_file, 'w') as f:
                json.dump(sync_data, f, indent=2)
            
            # Track token usage for dashboard sync
            tracker_module.track_dashboard_sync()
            
            self.logger.info(f"Dashboard sync completed at {datetime.now()}")
            
        except Exception as e:
            self.logger.error(f"Dashboard sync failed: {e}")
    
    def update_dashboard_data(self, pending_updates: List[Dict]):
        """Update dashboard data files with pending changes"""
        # Try multiple dashboard locations
        dashboard_locations = [
            self.base_path / "Project Management" / "dashboard",
            self.base_path / "active" / "Project Management" / "dashboard",
            self.base_path / "staging" / "Project Management" / "dashboard"
        ]
        
        dashboard_dir = None
        for location in dashboard_locations:
            if location.exists():
                dashboard_dir = location
                break
        
        if not dashboard_dir:
            self.logger.warning("Dashboard directory not found in any expected location")
            return
        
        # Update idea backlog for dashboard - try multiple locations
        backlog_locations = [
            self.base_path / "Personal-OS" / "project-management" / "idea-backlog.json",
            self.base_path / "active" / "Personal-OS" / "project-management" / "idea-backlog.json",
            self.base_path / "systems" / "idea-backlog.json"
        ]
        
        backlog_file = None
        for location in backlog_locations:
            if location.exists():
                backlog_file = location
                break
        
        # If no backlog file exists, create in systems directory
        if not backlog_file:
            backlog_file = self.base_path / "systems" / "idea-backlog.json"
        
        if backlog_file.exists():
            with open(backlog_file, 'r') as f:
                backlog = json.load(f)
        else:
            backlog = {"ideas": []}
        
        # Process each pending update
        for update in pending_updates:
            project_data = update["data"]
            
            # Convert to dashboard format
            dashboard_project = {
                "id": project_data["id"],
                "title": project_data["name"],
                "category": project_data["type"],
                "priority": "medium",  # Default priority
                "effort": "medium",    # Default effort
                "status": project_data["status"],
                "description": f"Auto-discovered {project_data['type']} project",
                "tags": [project_data["type"]],
                "created_date": project_data["discovered_at"],
                "phase": "discovery",
                "auto_discovered": True
            }
            
            # Check if project already exists in backlog
            existing = None
            for i, idea in enumerate(backlog["ideas"]):
                if idea["id"] == project_data["id"]:
                    existing = i
                    break
            
            if existing is not None:
                # Update existing entry
                backlog["ideas"][existing].update(dashboard_project)
            else:
                # Add new entry
                backlog["ideas"].append(dashboard_project)
        
        # Save updated backlog
        backlog_file.parent.mkdir(parents=True, exist_ok=True)
        with open(backlog_file, 'w') as f:
            json.dump(backlog, f, indent=2)
        
        self.logger.info(f"Updated dashboard with {len(pending_updates)} project changes")
    
    def start_monitoring(self):
        """Start file system monitoring"""
        if self.observer:
            self.logger.warning("Monitoring already started")
            return
        
        self.observer = Observer()
        handler = ProjectDiscoveryHandler(self)
        
        # Watch specified directories
        for watch_dir in self.watch_dirs:
            if watch_dir.exists():
                self.observer.schedule(handler, str(watch_dir), recursive=True)
                self.logger.info(f"Watching directory: {watch_dir}")
        
        self.observer.start()
        self.logger.info("File system monitoring started")
    
    def stop_monitoring(self):
        """Stop file system monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.logger.info("File system monitoring stopped")
    
    def run_service(self):
        """Run the discovery service with periodic sync"""
        self.start_monitoring()
        
        try:
            while True:
                # Process any queued updates
                self.process_update_queue()
                
                # Sync with dashboard
                self.sync_with_dashboard()
                
                # Wait for next cycle
                sync_frequency = self.registry.get("discovery_settings", {}).get("sync_frequency_minutes", 5)
                time.sleep(sync_frequency * 60)
                
        except KeyboardInterrupt:
            self.logger.info("Service interrupted by user")
        finally:
            self.stop_monitoring()
    
    def manual_sync(self):
        """Manually trigger sync operations"""
        self.logger.info("Manual sync triggered")
        self.process_update_queue()
        self.sync_with_dashboard()
        return True
    
    def discover_all_projects(self):
        """One-time full discovery scan"""
        discovered = 0
        
        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue
                
            for item in watch_dir.iterdir():
                if item.is_dir() and self.is_project_directory(item):
                    if self.check_new_project(str(item)):
                        discovered += 1
        
        self.logger.info(f"Discovery scan complete: {discovered} new projects found")
        return discovered

def main():
    """CLI interface for project discovery service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Discovery Service")
    parser.add_argument("--action", choices=["start", "scan", "sync", "status"], required=True)
    parser.add_argument("--daemon", action="store_true", help="Run as background service")
    
    args = parser.parse_args()
    
    service = ProjectDiscoveryService()
    
    try:
        if args.action == "start":
            if args.daemon:
                service.run_service()
            else:
                print("Starting monitoring... Press Ctrl+C to stop")
                service.start_monitoring()
                while True:
                    time.sleep(1)
        
        elif args.action == "scan":
            discovered = service.discover_all_projects()
            print(f"✅ Discovered {discovered} new projects")
        
        elif args.action == "sync":
            service.manual_sync()
            print("✅ Manual sync completed")
        
        elif args.action == "status":
            total_projects = len(service.registry.get("projects", {}))
            last_updated = service.registry.get("last_updated", "Never")
            print(f"📊 Discovery Service Status:")
            print(f"  Total projects: {total_projects}")
            print(f"  Last updated: {last_updated}")
            print(f"  Monitoring: {'✅' if service.observer else '❌'}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        service.logger.error(f"Service error: {e}")

if __name__ == "__main__":
    main()
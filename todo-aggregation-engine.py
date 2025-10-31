#!/usr/bin/env python3
"""
TODO Aggregation Engine
Parse all TODO.md files efficiently with caching and incremental updates
Cross-project dependency tracking and priority bubble-up to dashboard
Manual sync triggers per project or bulk operations
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import logging

class TodoAggregationEngine:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        self.project_registry_path = self.base_path / "project-registry.json"
        self.cache_file = self.systems_dir / "todo-cache.json"
        self.aggregated_file = self.systems_dir / "aggregated-todos.json"
        
        # Setup logging
        self.setup_logging()
        
        # Load cache and registry
        self.cache = self.load_cache()
        self.project_registry = self.load_project_registry()
        
        print(f"📋 TODO Aggregation Engine initialized")
        print(f"   Cache file: {self.cache_file}")
        print(f"   Aggregated output: {self.aggregated_file}")
    
    def setup_logging(self):
        """Setup logging for TODO engine"""
        log_file = self.systems_dir / "todo-aggregation.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_cache(self) -> Dict:
        """Load TODO parsing cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading cache: {e}")
        
        return {
            "last_scan": "",
            "file_hashes": {},
            "parsed_todos": {},
            "cross_references": {},
            "priority_matrix": {}
        }
    
    def save_cache(self):
        """Save TODO parsing cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
    
    def load_project_registry(self) -> Dict:
        """Load project registry"""
        try:
            with open(self.project_registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading project registry: {e}")
            return {"projects": {}}
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file contents"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def parse_todo_file(self, file_path: Path, project_id: str) -> Dict:
        """Parse a single TODO.md file"""
        try:
            content = file_path.read_text()
            
            todo_data = {
                "project_id": project_id,
                "file_path": str(file_path),
                "parsed_at": datetime.now().isoformat(),
                "sections": {},
                "tasks": [],
                "cross_references": [],
                "priorities": {},
                "stats": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "high_priority": 0,
                    "blocked_tasks": 0,
                    "due_tasks": 0
                }
            }
            
            current_section = "general"
            lines = content.split('\\n')
            
            for line_num, line in enumerate(lines, 1):
                original_line = line
                line = line.strip()
                
                # Section headers
                if line.startswith('#'):
                    section_match = re.search(r'#+\\s*(.*)', line)
                    if section_match:
                        current_section = section_match.group(1).lower().replace(' ', '_')
                        todo_data["sections"][current_section] = {
                            "line": line_num,
                            "title": section_match.group(1),
                            "tasks": []
                        }
                    continue
                
                # Task lines - support both formats: "- [ ]" and "- [x]" 
                task_match = re.match(r'^\\s*[-*]\\s*\\[(.?)\\]\\s*(.*)', original_line)
                if task_match:
                    completed = task_match.group(1).lower() == 'x'
                    task_text = task_match.group(2)
                    
                    # Parse task metadata
                    priority = self.extract_priority(task_text)
                    due_date = self.extract_due_date(task_text)
                    dependencies = self.extract_dependencies(task_text)
                    project_refs = self.extract_project_references(task_text)
                    blocked = 'blocked' in task_text.lower() or 'waiting' in task_text.lower()
                    
                    task = {
                        "id": f"{project_id}:{line_num}",
                        "text": task_text,
                        "completed": completed,
                        "section": current_section,
                        "line_number": line_num,
                        "priority": priority,
                        "due_date": due_date,
                        "dependencies": dependencies,
                        "project_references": project_refs,
                        "blocked": blocked,
                        "project_id": project_id
                    }
                    
                    todo_data["tasks"].append(task)
                    
                    # Add to section
                    if current_section not in todo_data["sections"]:
                        todo_data["sections"][current_section] = {
                            "line": line_num,
                            "title": current_section.title(),
                            "tasks": []
                        }
                    todo_data["sections"][current_section]["tasks"].append(task)
                    
                    # Update stats
                    todo_data["stats"]["total_tasks"] += 1
                    if completed:
                        todo_data["stats"]["completed_tasks"] += 1
                    if priority == "high":
                        todo_data["stats"]["high_priority"] += 1
                    if blocked:
                        todo_data["stats"]["blocked_tasks"] += 1
                    if due_date:
                        todo_data["stats"]["due_tasks"] += 1
                    
                    # Track cross-references
                    if project_refs:
                        todo_data["cross_references"].extend(project_refs)
            
            return todo_data
            
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return {
                "project_id": project_id,
                "file_path": str(file_path),
                "error": str(e),
                "parsed_at": datetime.now().isoformat()
            }
    
    def extract_priority(self, task_text: str) -> str:
        """Extract priority from task text"""
        text_lower = task_text.lower()
        if any(marker in text_lower for marker in ['urgent', '!high', 'critical', '🔥']):
            return "high"
        elif any(marker in text_lower for marker in ['important', '!medium', '⚡']):
            return "medium"
        elif any(marker in text_lower for marker in ['!low', 'nice to have', '🔸']):
            return "low"
        return "normal"
    
    def extract_due_date(self, task_text: str) -> Optional[str]:
        """Extract due date from task text"""
        # Look for patterns like "due: 2025-01-15", "by Jan 15", "@2025-01-15"
        patterns = [
            r'due:\\s*(\\d{4}-\\d{2}-\\d{2})',
            r'by\\s*(\\w+\\s+\\d{1,2})',
            r'@(\\d{4}-\\d{2}-\\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, task_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_dependencies(self, task_text: str) -> List[str]:
        """Extract task dependencies"""
        # Look for patterns like "depends on: task-id", "after: project:task"
        dependencies = []
        
        patterns = [
            r'depends on:\\s*([\\w-]+(?::[\\w-]+)?)',
            r'after:\\s*([\\w-]+(?::[\\w-]+)?)',
            r'blocked by:\\s*([\\w-]+(?::[\\w-]+)?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, task_text, re.IGNORECASE)
            dependencies.extend(matches)
        
        return dependencies
    
    def extract_project_references(self, task_text: str) -> List[str]:
        """Extract project references"""
        # Look for patterns like "@project-name", "in: project-name"
        references = []
        
        patterns = [
            r'@([\\w-]+)',
            r'in:\\s*([\\w-]+)',
            r'project:\\s*([\\w-]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, task_text, re.IGNORECASE)
            references.extend(matches)
        
        return references
    
    def scan_project_todos(self, project_id: str, force_refresh: bool = False) -> Optional[Dict]:
        """Scan TODOs for a specific project"""
        projects = self.project_registry.get("projects", {})
        
        if project_id not in projects:
            self.logger.error(f"Project {project_id} not found in registry")
            return None
        
        project = projects[project_id]
        project_path = Path(project["path"])
        
        if not project_path.exists():
            self.logger.warning(f"Project path does not exist: {project_path}")
            return None
        
        todo_file = project_path / "TODO.md"
        
        if not todo_file.exists():
            # No TODO file, return empty structure
            return {
                "project_id": project_id,
                "file_path": str(todo_file),
                "exists": False,
                "parsed_at": datetime.now().isoformat(),
                "stats": {"total_tasks": 0, "completed_tasks": 0, "high_priority": 0, "blocked_tasks": 0, "due_tasks": 0}
            }
        
        # Check if file has changed
        current_hash = self.get_file_hash(todo_file)
        cached_hash = self.cache["file_hashes"].get(str(todo_file), "")
        
        if not force_refresh and current_hash == cached_hash and str(todo_file) in self.cache["parsed_todos"]:
            self.logger.debug(f"Using cached TODO data for {project_id}")
            return self.cache["parsed_todos"][str(todo_file)]
        
        # Parse the file
        self.logger.info(f"Parsing TODO file: {todo_file}")
        todo_data = self.parse_todo_file(todo_file, project_id)
        
        # Update cache
        self.cache["file_hashes"][str(todo_file)] = current_hash
        self.cache["parsed_todos"][str(todo_file)] = todo_data
        
        return todo_data
    
    def scan_all_projects(self, force_refresh: bool = False) -> Dict:
        """Scan all projects for TODOs"""
        print(f"\\n📋 SCANNING PROJECT TODOs {'(FORCE REFRESH)' if force_refresh else ''}")
        print("=" * 80)
        
        projects = self.project_registry.get("projects", {})
        all_todos = {}
        stats = {
            "total_projects": len(projects),
            "projects_with_todos": 0,
            "total_tasks": 0,
            "high_priority_tasks": 0,
            "blocked_tasks": 0,
            "overdue_tasks": 0,
            "cross_references": 0
        }
        
        for project_id in projects:
            print(f"   📁 Scanning {project_id}...")
            todo_data = self.scan_project_todos(project_id, force_refresh)
            
            if todo_data:
                all_todos[project_id] = todo_data
                
                if todo_data.get("exists", True) and todo_data.get("stats", {}).get("total_tasks", 0) > 0:
                    stats["projects_with_todos"] += 1
                
                task_stats = todo_data.get("stats", {})
                stats["total_tasks"] += task_stats.get("total_tasks", 0)
                stats["high_priority_tasks"] += task_stats.get("high_priority", 0)
                stats["blocked_tasks"] += task_stats.get("blocked_tasks", 0)
                
                # Count cross-references
                cross_refs = todo_data.get("cross_references", [])
                stats["cross_references"] += len(cross_refs)
        
        # Save cache
        self.save_cache()
        
        print(f"\\n📊 SCAN SUMMARY:")
        print(f"   Projects scanned: {stats['total_projects']}")
        print(f"   Projects with TODOs: {stats['projects_with_todos']}")
        print(f"   Total tasks: {stats['total_tasks']}")
        print(f"   High priority: {stats['high_priority_tasks']}")
        print(f"   Blocked: {stats['blocked_tasks']}")
        print(f"   Cross-references: {stats['cross_references']}")
        
        return {
            "todos": all_todos,
            "stats": stats,
            "scanned_at": datetime.now().isoformat()
        }
    
    def generate_priority_matrix(self, todo_data: Dict) -> Dict:
        """Generate priority matrix for all TODOs"""
        matrix = {
            "high": {"immediate": [], "short_term": [], "long_term": []},
            "medium": {"immediate": [], "short_term": [], "long_term": []}, 
            "normal": {"immediate": [], "short_term": [], "long_term": []},
            "low": {"immediate": [], "short_term": [], "long_term": []}
        }
        
        for project_id, project_todos in todo_data["todos"].items():
            if "tasks" not in project_todos:
                continue
                
            for task in project_todos["tasks"]:
                if task["completed"]:
                    continue
                
                priority = task.get("priority", "normal")
                
                # Determine time frame based on due date
                time_frame = "long_term"  # default
                due_date = task.get("due_date")
                
                if due_date:
                    try:
                        # Simple date parsing - could be enhanced
                        if "today" in due_date.lower() or "asap" in task["text"].lower():
                            time_frame = "immediate"
                        elif any(word in due_date.lower() for word in ["week", "soon"]):
                            time_frame = "short_term"
                    except:
                        pass
                elif task.get("blocked"):
                    time_frame = "immediate"  # Blocked tasks need immediate attention
                
                matrix[priority][time_frame].append({
                    "task": task,
                    "project": project_id
                })
        
        return matrix
    
    def generate_cross_project_dependencies(self, todo_data: Dict) -> Dict:
        """Generate cross-project dependency graph"""
        dependencies = {}
        
        for project_id, project_todos in todo_data["todos"].items():
            if "tasks" not in project_todos:
                continue
            
            project_deps = []
            
            for task in project_todos["tasks"]:
                if task["completed"]:
                    continue
                
                # Task dependencies
                for dep in task.get("dependencies", []):
                    if ":" in dep:  # Cross-project dependency
                        dep_project, dep_task = dep.split(":", 1)
                        project_deps.append({
                            "type": "task_dependency",
                            "source_task": task["id"],
                            "target_project": dep_project,
                            "target_task": dep_task,
                            "blocked": True
                        })
                
                # Project references
                for ref in task.get("project_references", []):
                    project_deps.append({
                        "type": "project_reference", 
                        "source_task": task["id"],
                        "target_project": ref,
                        "blocked": False
                    })
            
            if project_deps:
                dependencies[project_id] = project_deps
        
        return dependencies
    
    def save_aggregated_data(self, todo_data: Dict):
        """Save aggregated TODO data"""
        # Generate additional analysis
        priority_matrix = self.generate_priority_matrix(todo_data)
        dependencies = self.generate_cross_project_dependencies(todo_data)
        
        aggregated = {
            "generated_at": datetime.now().isoformat(),
            "summary": todo_data["stats"],
            "todos_by_project": todo_data["todos"],
            "priority_matrix": priority_matrix,
            "cross_project_dependencies": dependencies,
            "metadata": {
                "version": "1.0",
                "projects_scanned": len(todo_data["todos"]),
                "cache_file": str(self.cache_file)
            }
        }
        
        try:
            with open(self.aggregated_file, 'w') as f:
                json.dump(aggregated, f, indent=2)
            
            print(f"✅ Aggregated TODO data saved to: {self.aggregated_file}")
            self.logger.info(f"Saved aggregated TODO data: {len(aggregated['todos_by_project'])} projects")
            
        except Exception as e:
            self.logger.error(f"Error saving aggregated data: {e}")

def main():
    """CLI interface for TODO aggregation engine"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TODO Aggregation Engine")
    parser.add_argument("--action", 
                       choices=["sync", "scan-project", "matrix", "dependencies", "stats"], 
                       required=True)
    parser.add_argument("--project", help="Project ID for scan-project action")
    parser.add_argument("--force", action="store_true", help="Force refresh (ignore cache)")
    
    args = parser.parse_args()
    
    engine = TodoAggregationEngine()
    
    try:
        if args.action == "sync":
            # Full sync of all project TODOs
            todo_data = engine.scan_all_projects(force_refresh=args.force)
            engine.save_aggregated_data(todo_data)
            
        elif args.action == "scan-project":
            if not args.project:
                print("❌ Error: --project required for scan-project action")
                return 1
            
            result = engine.scan_project_todos(args.project, force_refresh=args.force)
            if result:
                print(f"\\n📋 TODO SCAN: {args.project}")
                print("=" * 80)
                
                if result.get("exists", True):
                    stats = result.get("stats", {})
                    print(f"Tasks: {stats.get('total_tasks', 0)} total, {stats.get('completed_tasks', 0)} completed")
                    print(f"Priority: {stats.get('high_priority', 0)} high priority")
                    print(f"Blocked: {stats.get('blocked_tasks', 0)} tasks")
                    print(f"Due: {stats.get('due_tasks', 0)} tasks")
                else:
                    print("No TODO.md file found")
            
        elif args.action == "matrix":
            # Load existing aggregated data
            if engine.aggregated_file.exists():
                with open(engine.aggregated_file, 'r') as f:
                    data = json.load(f)
                
                print(f"\\n📋 TODO PRIORITY MATRIX")
                print("=" * 80)
                
                matrix = data.get("priority_matrix", {})
                for priority in ["high", "medium", "normal", "low"]:
                    if priority in matrix:
                        total = sum(len(matrix[priority][tf]) for tf in matrix[priority])
                        if total > 0:
                            print(f"\\n🎯 {priority.upper()} PRIORITY ({total} tasks):")
                            for time_frame in ["immediate", "short_term", "long_term"]:
                                tasks = matrix[priority][time_frame]
                                if tasks:
                                    print(f"  📅 {time_frame.replace('_', ' ').title()} ({len(tasks)} tasks):")
                                    for item in tasks[:3]:  # Show top 3
                                        task = item["task"]
                                        project = item["project"]
                                        print(f"    • {project}: {task['text'][:60]}...")
            else:
                print("❌ No aggregated TODO data found. Run sync first.")
        
        elif args.action == "dependencies":
            # Show cross-project dependencies
            if engine.aggregated_file.exists():
                with open(engine.aggregated_file, 'r') as f:
                    data = json.load(f)
                
                print(f"\\n🔗 CROSS-PROJECT DEPENDENCIES")
                print("=" * 80)
                
                deps = data.get("cross_project_dependencies", {})
                if not deps:
                    print("✅ No cross-project dependencies found")
                else:
                    for project, project_deps in deps.items():
                        print(f"\\n📁 {project}:")
                        for dep in project_deps[:5]:  # Show top 5
                            if dep["type"] == "task_dependency":
                                print(f"   🔗 Depends on {dep['target_project']}:{dep['target_task']}")
                            else:
                                print(f"   📎 References {dep['target_project']}")
            else:
                print("❌ No aggregated TODO data found. Run sync first.")
        
        elif args.action == "stats":
            # Show TODO statistics
            if engine.aggregated_file.exists():
                with open(engine.aggregated_file, 'r') as f:
                    data = json.load(f)
                
                print(f"\\n📊 TODO STATISTICS")
                print("=" * 80)
                
                summary = data.get("summary", {})
                print(f"Projects scanned: {summary.get('total_projects', 0)}")
                print(f"Projects with TODOs: {summary.get('projects_with_todos', 0)}")
                print(f"Total tasks: {summary.get('total_tasks', 0)}")
                print(f"High priority tasks: {summary.get('high_priority_tasks', 0)}")
                print(f"Blocked tasks: {summary.get('blocked_tasks', 0)}")
                print(f"Cross-references: {summary.get('cross_references', 0)}")
                
                print(f"\\nGenerated: {data.get('generated_at', 'Unknown')}")
            else:
                print("❌ No aggregated TODO data found. Run sync first.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
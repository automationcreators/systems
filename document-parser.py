#!/usr/bin/env python3
"""
Live Document Parser
Parses TODO.md and CLAUDE.md files for real-time dashboard updates
Zero token usage - pure regex and rule-based parsing
"""

import re
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

# Token tracking integration
import sys
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("token_tracker", Path(__file__).parent / "token-tracker-integration.py")
tracker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker_module)

class DocumentParser:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        
        # Cache for parsed documents to detect changes
        self.cache_file = self.systems_dir / "document-parse-cache.json"
        self.load_cache()
        
        # Setup logging
        self.setup_logging()
        
        self.logger.info("Document Parser initialized")
    
    def setup_logging(self):
        """Setup document parser logging"""
        log_file = self.systems_dir / "document-parser.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_cache(self):
        """Load document parsing cache"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = {
                "documents": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def save_cache(self):
        """Save document parsing cache"""
        self.cache["last_updated"] = datetime.now().isoformat()
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file content for change detection"""
        if not file_path.exists():
            return ""
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return hashlib.md5(content.encode()).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to hash file {file_path}: {e}")
            return ""
    
    def has_file_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last parse"""
        file_key = str(file_path)
        current_hash = self.calculate_file_hash(file_path)
        
        if file_key not in self.cache["documents"]:
            return True
        
        cached_hash = self.cache["documents"][file_key].get("hash", "")
        return current_hash != cached_hash
    
    def parse_todo_md(self, file_path: Path) -> Dict:
        """Parse TODO.md file and extract task information"""
        if not file_path.exists():
            return {"error": "File not found"}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse task information using regex
            tasks = {
                "high_priority": [],
                "medium_priority": [],
                "low_priority": [],
                "completed": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "completion_percentage": 0
            }
            
            # Regex patterns for different task types
            patterns = {
                "incomplete_task": r'^-\s*\[\s*\]\s*(.+)$',
                "completed_task": r'^-\s*\[x\]\s*(.+)$',
                "high_priority": r'(?i)(urgent|high\s*priority|critical|\!\!\!)',
                "medium_priority": r'(?i)(medium\s*priority|important|\!\!)',
                "low_priority": r'(?i)(low\s*priority|nice\s*to\s*have|\!)',
                "due_date": r'(?i)due:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
                "assigned": r'(?i)assigned:?\s*(\w+)',
                "tags": r'#(\w+)',
            }
            
            lines = content.split('\n')
            current_section = "general"
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                if line.startswith('##') or line.startswith('#'):
                    section_name = line.lstrip('#').strip().lower()
                    if 'high' in section_name or 'urgent' in section_name:
                        current_section = "high_priority"
                    elif 'medium' in section_name:
                        current_section = "medium_priority"
                    elif 'low' in section_name:
                        current_section = "low_priority" 
                    elif 'completed' in section_name or 'done' in section_name:
                        current_section = "completed"
                    continue
                
                # Parse incomplete tasks
                incomplete_match = re.search(patterns["incomplete_task"], line, re.MULTILINE)
                if incomplete_match:
                    task_text = incomplete_match.group(1).strip()
                    
                    # Extract additional info
                    priority = self.extract_task_priority(task_text, patterns)
                    due_date = self.extract_due_date(task_text, patterns)
                    tags = self.extract_tags(task_text, patterns)
                    
                    task_info = {
                        "text": task_text,
                        "priority": priority or current_section,
                        "due_date": due_date,
                        "tags": tags,
                        "completed": False,
                        "section": current_section
                    }
                    
                    # Categorize by priority
                    if priority == "high_priority" or current_section == "high_priority":
                        tasks["high_priority"].append(task_info)
                    elif priority == "medium_priority" or current_section == "medium_priority":
                        tasks["medium_priority"].append(task_info)
                    else:
                        tasks["low_priority"].append(task_info)
                    
                    tasks["total_tasks"] += 1
                
                # Parse completed tasks  
                completed_match = re.search(patterns["completed_task"], line, re.MULTILINE)
                if completed_match:
                    task_text = completed_match.group(1).strip()
                    
                    task_info = {
                        "text": task_text,
                        "priority": current_section,
                        "completed": True,
                        "section": current_section,
                        "tags": self.extract_tags(task_text, patterns)
                    }
                    
                    tasks["completed"].append(task_info)
                    tasks["total_tasks"] += 1
                    tasks["completed_tasks"] += 1
            
            # Calculate completion percentage
            if tasks["total_tasks"] > 0:
                tasks["completion_percentage"] = round((tasks["completed_tasks"] / tasks["total_tasks"]) * 100, 1)
            
            # Add file metadata
            stat = file_path.stat()
            tasks["file_info"] = {
                "path": str(file_path),
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size,
                "hash": self.calculate_file_hash(file_path)
            }
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"Failed to parse TODO.md {file_path}: {e}")
            return {"error": str(e)}
    
    def extract_task_priority(self, task_text: str, patterns: Dict) -> Optional[str]:
        """Extract priority from task text"""
        if re.search(patterns["high_priority"], task_text):
            return "high_priority"
        elif re.search(patterns["medium_priority"], task_text):
            return "medium_priority"
        elif re.search(patterns["low_priority"], task_text):
            return "low_priority"
        return None
    
    def extract_due_date(self, task_text: str, patterns: Dict) -> Optional[str]:
        """Extract due date from task text"""
        match = re.search(patterns["due_date"], task_text)
        return match.group(1) if match else None
    
    def extract_tags(self, task_text: str, patterns: Dict) -> List[str]:
        """Extract tags from task text"""
        return re.findall(patterns["tags"], task_text)
    
    def parse_claude_md(self, file_path: Path) -> Dict:
        """Parse CLAUDE.md file and extract project context"""
        if not file_path.exists():
            return {"error": "File not found"}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            context = {
                "title": "",
                "project_type": "",
                "status": "",
                "description": "",
                "requirements": [],
                "current_status": [],
                "notes": "",
                "tags": [],
                "metadata": {}
            }
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line_strip = line.strip()
                
                # Extract title (first # heading)
                if line_strip.startswith('# ') and not context["title"]:
                    context["title"] = line_strip[2:].strip()
                    continue
                
                # Extract metadata from ** fields
                if line_strip.startswith('**') and line_strip.endswith('**'):
                    # Look for next line with value
                    continue
                elif ':' in line_strip and any(keyword in line_strip.lower() for keyword in ['project type', 'created', 'security', 'status']):
                    parts = line_strip.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower().replace('**', '').replace('*', '')
                        value = parts[1].strip()
                        context["metadata"][key] = value
                        
                        if 'project type' in key:
                            context["project_type"] = value
                        elif 'status' in key:
                            context["status"] = value
                
                # Detect sections
                if line_strip.startswith('##'):
                    section_name = line_strip[2:].strip().lower()
                    if 'overview' in section_name or 'description' in section_name:
                        current_section = "description"
                    elif 'status' in section_name:
                        current_section = "status"
                    elif 'requirements' in section_name:
                        current_section = "requirements"
                    elif 'notes' in section_name:
                        current_section = "notes"
                    continue
                
                # Extract content based on current section
                if current_section == "description" and line_strip and not line_strip.startswith('#'):
                    context["description"] += line_strip + " "
                
                elif current_section == "requirements":
                    if line_strip.startswith('- '):
                        context["requirements"].append(line_strip[2:].strip())
                
                elif current_section == "status":
                    if '- [' in line_strip:
                        context["current_status"].append({
                            "text": line_strip.strip(),
                            "completed": '[x]' in line_strip
                        })
                
                elif current_section == "notes" and line_strip and not line_strip.startswith('#'):
                    context["notes"] += line_strip + " "
                
                # Extract tags
                tags = re.findall(r'#(\w+)', line)
                context["tags"].extend(tags)
            
            # Clean up extracted text
            context["description"] = context["description"].strip()
            context["notes"] = context["notes"].strip()
            context["tags"] = list(set(context["tags"]))  # Remove duplicates
            
            # Calculate status completion
            if context["current_status"]:
                completed_status = sum(1 for item in context["current_status"] if item["completed"])
                context["status_completion"] = round((completed_status / len(context["current_status"])) * 100, 1)
            else:
                context["status_completion"] = 0
            
            # Add file metadata
            stat = file_path.stat()
            context["file_info"] = {
                "path": str(file_path),
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size,
                "hash": self.calculate_file_hash(file_path)
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to parse CLAUDE.md {file_path}: {e}")
            return {"error": str(e)}
    
    def parse_project_documents(self, project_path: Path) -> Dict:
        """Parse all relevant documents in a project directory"""
        project_data = {
            "project_path": str(project_path),
            "project_name": project_path.name,
            "parsed_at": datetime.now().isoformat(),
            "documents": {},
            "summary": {}
        }
        
        # Track document parsing operation
        parsing_operations = 0
        
        # Parse TODO.md
        todo_file = project_path / "TODO.md"
        if todo_file.exists() and self.has_file_changed(todo_file):
            self.logger.info(f"Parsing TODO.md: {todo_file}")
            project_data["documents"]["todo"] = self.parse_todo_md(todo_file)
            parsing_operations += 1
            
            # Cache the result
            self.cache["documents"][str(todo_file)] = {
                "parsed_at": datetime.now().isoformat(),
                "hash": self.calculate_file_hash(todo_file),
                "data": project_data["documents"]["todo"]
            }
        elif todo_file.exists():
            # Use cached data
            cached_data = self.cache["documents"].get(str(todo_file), {})
            if "data" in cached_data:
                project_data["documents"]["todo"] = cached_data["data"]
        
        # Parse CLAUDE.md
        claude_file = project_path / "CLAUDE.md"
        if claude_file.exists() and self.has_file_changed(claude_file):
            self.logger.info(f"Parsing CLAUDE.md: {claude_file}")
            project_data["documents"]["claude"] = self.parse_claude_md(claude_file)
            parsing_operations += 1
            
            # Cache the result
            self.cache["documents"][str(claude_file)] = {
                "parsed_at": datetime.now().isoformat(),
                "hash": self.calculate_file_hash(claude_file),
                "data": project_data["documents"]["claude"]
            }
        elif claude_file.exists():
            # Use cached data
            cached_data = self.cache["documents"].get(str(claude_file), {})
            if "data" in cached_data:
                project_data["documents"]["claude"] = cached_data["data"]
        
        # Generate project summary
        project_data["summary"] = self.generate_project_summary(project_data["documents"])
        
        # Track token usage if we actually parsed documents
        if parsing_operations > 0:
            tracker_module.track_document_parsing()
        
        # Save cache
        self.save_cache()
        
        return project_data
    
    def generate_project_summary(self, documents: Dict) -> Dict:
        """Generate summary from parsed documents"""
        summary = {
            "overall_progress": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "high_priority_tasks": 0,
            "overdue_tasks": 0,
            "project_status": "unknown",
            "last_activity": None,
            "key_info": {}
        }
        
        # TODO.md summary
        if "todo" in documents and "error" not in documents["todo"]:
            todo_data = documents["todo"]
            summary["total_tasks"] = todo_data.get("total_tasks", 0)
            summary["completed_tasks"] = todo_data.get("completed_tasks", 0)
            summary["overall_progress"] = todo_data.get("completion_percentage", 0)
            summary["high_priority_tasks"] = len(todo_data.get("high_priority", []))
            
            # Check for overdue tasks
            today = datetime.now().date()
            for task_list in [todo_data.get("high_priority", []), todo_data.get("medium_priority", []), todo_data.get("low_priority", [])]:
                for task in task_list:
                    if task.get("due_date"):
                        try:
                            due_date = datetime.fromisoformat(task["due_date"]).date()
                            if due_date < today:
                                summary["overdue_tasks"] += 1
                        except:
                            pass
            
            # Get last activity from file info
            if "file_info" in todo_data:
                summary["last_activity"] = todo_data["file_info"]["last_modified"]
        
        # CLAUDE.md summary
        if "claude" in documents and "error" not in documents["claude"]:
            claude_data = documents["claude"]
            summary["project_status"] = claude_data.get("status", "unknown")
            
            # Combine progress if both exist
            if claude_data.get("status_completion", 0) > 0:
                if summary["overall_progress"] > 0:
                    # Average the two progress metrics
                    summary["overall_progress"] = round((summary["overall_progress"] + claude_data["status_completion"]) / 2, 1)
                else:
                    summary["overall_progress"] = claude_data["status_completion"]
            
            summary["key_info"] = {
                "title": claude_data.get("title", ""),
                "type": claude_data.get("project_type", ""),
                "description": claude_data.get("description", "")[:200] + "..." if len(claude_data.get("description", "")) > 200 else claude_data.get("description", ""),
                "tags": claude_data.get("tags", [])
            }
            
            # Update last activity if CLAUDE.md is more recent
            if "file_info" in claude_data:
                claude_activity = claude_data["file_info"]["last_modified"]
                if not summary["last_activity"] or claude_activity > summary["last_activity"]:
                    summary["last_activity"] = claude_activity
        
        return summary
    
    def scan_all_projects(self) -> Dict:
        """Scan all projects and parse their documents"""
        results = {
            "scanned_at": datetime.now().isoformat(),
            "projects": {},
            "summary": {
                "total_projects": 0,
                "projects_with_todos": 0,
                "projects_with_claude_md": 0,
                "average_progress": 0
            }
        }
        
        # Scan active, staging, and archive directories
        scan_dirs = [
            self.base_path / "active",
            self.base_path / "staging",
            self.base_path / "archive"
        ]
        
        total_progress = 0
        progress_count = 0
        
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            
            for project_dir in scan_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                
                project_data = self.parse_project_documents(project_dir)
                results["projects"][project_dir.name] = project_data
                results["summary"]["total_projects"] += 1
                
                # Count document types
                if "todo" in project_data["documents"]:
                    results["summary"]["projects_with_todos"] += 1
                if "claude" in project_data["documents"]:
                    results["summary"]["projects_with_claude_md"] += 1
                
                # Add to average progress calculation
                if project_data["summary"]["overall_progress"] > 0:
                    total_progress += project_data["summary"]["overall_progress"]
                    progress_count += 1
        
        # Calculate average progress
        if progress_count > 0:
            results["summary"]["average_progress"] = round(total_progress / progress_count, 1)
        
        return results

def main():
    """CLI interface for document parser"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Document Parser for Personal OS")
    parser.add_argument("--action", choices=["scan", "parse", "test"], required=True)
    parser.add_argument("--project", help="Project name to parse")
    parser.add_argument("--file", help="Specific file to parse")
    
    args = parser.parse_args()
    
    doc_parser = DocumentParser()
    
    try:
        if args.action == "scan":
            results = doc_parser.scan_all_projects()
            print(f"📊 Document Parsing Results:")
            print(f"  Total projects: {results['summary']['total_projects']}")
            print(f"  Projects with TODO.md: {results['summary']['projects_with_todos']}")
            print(f"  Projects with CLAUDE.md: {results['summary']['projects_with_claude_md']}")
            print(f"  Average progress: {results['summary']['average_progress']}%")
        
        elif args.action == "parse":
            if not args.project:
                print("Error: --project required for parse action")
                return
            
            project_paths = [
                Path(doc_parser.base_path) / "active" / args.project,
                Path(doc_parser.base_path) / "staging" / args.project,
                Path(doc_parser.base_path) / "archive" / args.project
            ]
            
            project_path = None
            for path in project_paths:
                if path.exists():
                    project_path = path
                    break
            
            if not project_path:
                print(f"❌ Project not found: {args.project}")
                return
            
            results = doc_parser.parse_project_documents(project_path)
            print(f"📋 {args.project} Analysis:")
            print(f"  Progress: {results['summary']['overall_progress']}%")
            print(f"  Total tasks: {results['summary']['total_tasks']}")
            print(f"  Completed tasks: {results['summary']['completed_tasks']}")
            print(f"  High priority: {results['summary']['high_priority_tasks']}")
            print(f"  Status: {results['summary']['project_status']}")
        
        elif args.action == "test":
            # Test with a specific file
            if args.file:
                file_path = Path(args.file)
                if file_path.name == "TODO.md":
                    result = doc_parser.parse_todo_md(file_path)
                elif file_path.name == "CLAUDE.md":
                    result = doc_parser.parse_claude_md(file_path)
                else:
                    print("❌ Only TODO.md and CLAUDE.md files supported")
                    return
                
                print(f"📄 Parse Results for {file_path}:")
                print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
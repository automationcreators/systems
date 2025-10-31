#!/usr/bin/env python3
"""
Data Migration Tool for Project Management System Consolidation
Migrates idea-backlog.json files into project-registry.json as single source of truth
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil

class DataMigrationTool:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.project_registry_path = self.base_path / "project-registry.json"
        
        # Find all idea-backlog.json files
        self.backlog_files = [
            self.base_path / "active" / "Personal-OS" / "project-management" / "idea-backlog.json",
            self.base_path / "active" / "Project Management" / "idea-backlog.json"
        ]
        
        self.backup_dir = self.base_path / "systems" / "backups" / "migration-backup"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔧 Data Migration Tool initialized")
        print(f"   Base path: {self.base_path}")
        print(f"   Registry: {self.project_registry_path}")
        print(f"   Backup dir: {self.backup_dir}")
    
    def backup_files(self):
        """Backup all files before migration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = self.backup_dir / f"pre-migration-{timestamp}"
        backup_subdir.mkdir(exist_ok=True)
        
        print(f"\n📦 Creating migration backup...")
        
        # Backup project registry
        if self.project_registry_path.exists():
            shutil.copy2(self.project_registry_path, backup_subdir / "project-registry.json")
            print(f"   ✅ Backed up: project-registry.json")
        
        # Backup all idea-backlog files
        for i, backlog_file in enumerate(self.backlog_files):
            if backlog_file.exists():
                backup_name = f"idea-backlog-{i+1}.json"
                shutil.copy2(backlog_file, backup_subdir / backup_name)
                print(f"   ✅ Backed up: {backlog_file} → {backup_name}")
        
        print(f"   📁 Backup location: {backup_subdir}")
        return backup_subdir
    
    def load_project_registry(self) -> Dict:
        """Load existing project registry"""
        try:
            with open(self.project_registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load project registry: {e}")
            return {"projects": {}, "metadata": {}}
    
    def load_idea_backlogs(self) -> List[Dict]:
        """Load all idea-backlog.json files"""
        backlogs = []
        
        for backlog_file in self.backlog_files:
            if backlog_file.exists():
                try:
                    with open(backlog_file, 'r') as f:
                        data = json.load(f)
                        backlogs.append({
                            "file": str(backlog_file),
                            "data": data,
                            "ideas": data.get("ideas", [])
                        })
                        print(f"   📖 Loaded {len(data.get('ideas', []))} ideas from {backlog_file}")
                except Exception as e:
                    print(f"   ❌ Error loading {backlog_file}: {e}")
        
        return backlogs
    
    def convert_idea_to_project(self, idea: Dict, source_file: str) -> Dict:
        """Convert idea-backlog entry to project registry format"""
        project_id = idea.get("id", idea.get("title", "").lower().replace(" ", "-"))
        
        # Map idea fields to project registry fields
        project = {
            "id": project_id,
            "name": idea.get("title", project_id),
            "path": "",  # Will be populated when project is created
            "discovered_at": datetime.now().isoformat(),
            "last_modified": "",
            "size_mb": 0.0,
            "file_count": 0,
            "type": self.map_category_to_type(idea.get("category", "unknown")),
            "activity_score": 0.0,
            "lifecycle_stage": self.map_status_to_stage(idea.get("status", "backlog")),
            
            # Enhanced fields from idea backlog
            "title": idea.get("title"),
            "description": idea.get("description", ""),
            "category": idea.get("category", "unknown"),
            "status": idea.get("status", "backlog"),
            "priority": idea.get("priority", "medium"),
            "phase": idea.get("phase", "short-term"),
            "estimated_effort": idea.get("estimatedEffort", "medium"),
            "personal_impact": idea.get("personalImpact", {}),
            "tags": idea.get("tags", []),
            "notes": idea.get("notes", ""),
            "date_added": idea.get("dateAdded", ""),
            "date_selected": idea.get("dateSelected", ""),
            
            # Migration metadata
            "migrated_from": source_file,
            "migrated_at": datetime.now().isoformat()
        }
        
        return project
    
    def map_category_to_type(self, category: str) -> str:
        """Map idea category to project type"""
        mapping = {
            "content-creation": "claude-project",
            "development": "development",
            "data-analysis": "data-analysis", 
            "automation": "system-tool",
            "productivity": "system-tool",
            "dashboard": "dashboard",
            "unknown": "claude-project"
        }
        return mapping.get(category, "claude-project")
    
    def map_status_to_stage(self, status: str) -> str:
        """Map idea status to lifecycle stage"""
        mapping = {
            "backlog": "planned",
            "selected": "staging", 
            "in_progress": "active",
            "completed": "archived",
            "blocked": "staging"
        }
        return mapping.get(status, "planned")
    
    def merge_backlogs_to_registry(self) -> Dict:
        """Merge all idea backlogs into project registry"""
        print(f"\n🔄 Starting data migration...")
        
        # Load existing data
        registry = self.load_project_registry()
        backlogs = self.load_idea_backlogs()
        
        if not backlogs:
            print("   ❌ No idea-backlog files found to migrate")
            return registry
        
        # Track migration stats
        stats = {
            "existing_projects": len(registry.get("projects", {})),
            "new_projects": 0,
            "updated_projects": 0,
            "duplicates_skipped": 0
        }
        
        # Process each backlog
        for backlog in backlogs:
            print(f"\n   📋 Processing: {backlog['file']}")
            
            for idea in backlog["ideas"]:
                project = self.convert_idea_to_project(idea, backlog["file"])
                project_id = project["id"]
                
                if project_id in registry.get("projects", {}):
                    # Update existing project with idea data
                    existing = registry["projects"][project_id]
                    
                    # Only update if idea has more recent or better data
                    if not existing.get("title") or len(project.get("description", "")) > len(existing.get("description", "")):
                        existing.update({
                            "title": project["title"],
                            "description": project["description"],
                            "priority": project["priority"],
                            "phase": project["phase"],
                            "personal_impact": project["personal_impact"],
                            "tags": project["tags"],
                            "notes": project["notes"],
                            "enhanced_from": project["migrated_from"],
                            "enhanced_at": project["migrated_at"]
                        })
                        stats["updated_projects"] += 1
                        print(f"      ✅ Enhanced: {project_id}")
                    else:
                        stats["duplicates_skipped"] += 1
                        print(f"      ⏭️ Skipped duplicate: {project_id}")
                else:
                    # Add new project
                    if "projects" not in registry:
                        registry["projects"] = {}
                    registry["projects"][project_id] = project
                    stats["new_projects"] += 1
                    print(f"      ➕ Added: {project_id}")
        
        # Update metadata
        registry["metadata"] = {
            "last_migration": datetime.now().isoformat(),
            "migration_stats": stats,
            "data_sources": ["project-discovery", "idea-backlogs"],
            "version": "2.0"
        }
        
        print(f"\n📊 Migration Summary:")
        print(f"   • Existing projects: {stats['existing_projects']}")
        print(f"   • New projects added: {stats['new_projects']}")
        print(f"   • Existing projects enhanced: {stats['updated_projects']}")
        print(f"   • Duplicates skipped: {stats['duplicates_skipped']}")
        print(f"   • Total projects: {len(registry['projects'])}")
        
        return registry
    
    def save_project_registry(self, registry: Dict):
        """Save updated project registry"""
        try:
            with open(self.project_registry_path, 'w') as f:
                json.dump(registry, f, indent=2, default=str)
            print(f"   ✅ Saved updated project registry: {self.project_registry_path}")
        except Exception as e:
            print(f"   ❌ Error saving project registry: {e}")
            raise
    
    def validate_migration(self, registry: Dict) -> bool:
        """Validate migration results"""
        print(f"\n🔍 Validating migration...")
        
        issues = []
        projects = registry.get("projects", {})
        
        # Check for required fields
        for project_id, project in projects.items():
            if not project.get("name"):
                issues.append(f"Project {project_id} missing name")
            if not project.get("type"):
                issues.append(f"Project {project_id} missing type")
            if not project.get("lifecycle_stage"):
                issues.append(f"Project {project_id} missing lifecycle_stage")
        
        # Check data integrity
        if len(projects) == 0:
            issues.append("No projects found after migration")
        
        if issues:
            print("   ⚠️ Validation issues found:")
            for issue in issues:
                print(f"      • {issue}")
            return False
        else:
            print(f"   ✅ Validation passed - {len(projects)} projects migrated successfully")
            return True
    
    def cleanup_old_files(self, dry_run=True):
        """Remove old idea-backlog.json files after successful migration"""
        if dry_run:
            print(f"\n🗑️ Dry run - Files that would be deleted:")
            for backlog_file in self.backlog_files:
                if backlog_file.exists():
                    print(f"   • {backlog_file}")
        else:
            print(f"\n🗑️ Removing old idea-backlog.json files...")
            for backlog_file in self.backlog_files:
                if backlog_file.exists():
                    backlog_file.unlink()
                    print(f"   ✅ Deleted: {backlog_file}")

def main():
    """CLI interface for data migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Migration Tool for Project Management Consolidation")
    parser.add_argument("--action", choices=["migrate-backlogs", "validate", "cleanup"], required=True)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    migrator = DataMigrationTool()
    
    try:
        if args.action == "migrate-backlogs":
            if not args.force:
                response = input("\n🚨 This will modify project-registry.json and consolidate idea-backlog files. Continue? (y/n): ")
                if response.lower() != 'y':
                    print("Migration cancelled")
                    return
            
            # Create backup
            backup_dir = migrator.backup_files()
            
            # Perform migration
            registry = migrator.merge_backlogs_to_registry()
            
            if not args.dry_run:
                # Save results
                migrator.save_project_registry(registry)
                
                # Validate
                if migrator.validate_migration(registry):
                    print(f"\n🎉 Migration completed successfully!")
                    
                    # Ask about cleanup
                    if not args.force:
                        response = input("\n🗑️ Delete old idea-backlog.json files? (y/n): ")
                        if response.lower() == 'y':
                            migrator.cleanup_old_files(dry_run=False)
                        else:
                            migrator.cleanup_old_files(dry_run=True)
                    
                    print(f"\n📁 Backup location: {backup_dir}")
                    print(f"📊 Updated registry: {migrator.project_registry_path}")
                else:
                    print(f"\n❌ Migration validation failed - check issues above")
                    return 1
            else:
                print(f"\n🔍 Dry run completed - no changes made")
        
        elif args.action == "validate":
            registry = migrator.load_project_registry()
            migrator.validate_migration(registry)
        
        elif args.action == "cleanup":
            migrator.cleanup_old_files(dry_run=args.dry_run)
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    main()
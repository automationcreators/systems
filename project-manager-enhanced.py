#!/usr/bin/env python3
"""
Enhanced Personal OS Project Manager
Integrates with lifecycle management, security vault, and dashboard
"""

import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import tempfile

# Import our other systems
import sys
sys.path.append(str(Path(__file__).parent))

class EnhancedProjectManager:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.active_dir = self.base_path / "active"
        self.staging_dir = self.base_path / "staging"
        self.systems_dir = self.base_path / "systems"
        self.vault_dir = self.base_path / ".vault"
        
        # Template directories - updated for systems consolidation
        self.template_dir = self.systems_dir / "templates"
        self.rules_file = self.systems_dir / "enhanced-rules.json"
        self.project_registry_path = self.base_path / "project-registry.json"
        
        # Ensure template directory exists
        self.template_dir.mkdir(exist_ok=True)
        
        # Ensure directories exist
        for directory in [self.active_dir, self.staging_dir, self.systems_dir]:
            directory.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Load enhanced rules
        self.load_enhanced_rules()
    
    def setup_logging(self):
        """Setup project management logging"""
        log_file = self.systems_dir / "project-manager.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_enhanced_rules(self):
        """Load enhanced project creation and management rules"""
        default_rules = {
            "project_types": {
                "claude-project": {
                    "description": "Claude Code project with structured templates",
                    "templates": ["CLAUDE.md", "TODO.md", "HANDOFFS.md", "SECURITY.md"],
                    "security_level": "isolated",
                    "lifecycle_stage": "active",
                    "auto_backup": True,
                    "chat_tracking": True
                },
                "development": {
                    "description": "Software development project",
                    "templates": ["README.md", "CLAUDE.md", ".gitignore"],
                    "security_level": "project",
                    "lifecycle_stage": "active",
                    "auto_backup": True,
                    "chat_tracking": True
                },
                "data-analysis": {
                    "description": "Data analysis and research project",
                    "templates": ["CLAUDE.md", "data-notes.md"],
                    "security_level": "shared",
                    "lifecycle_stage": "staging",
                    "auto_backup": True,
                    "chat_tracking": False
                },
                "one-off": {
                    "description": "Quick one-time project",
                    "templates": ["quick-notes.md"],
                    "security_level": "shared",
                    "lifecycle_stage": "staging",
                    "auto_backup": False,
                    "chat_tracking": False
                },
                "system-tool": {
                    "description": "Personal productivity system or tool",
                    "templates": ["CLAUDE.md", "TODO.md", "README.md"],
                    "security_level": "system",
                    "lifecycle_stage": "systems",
                    "auto_backup": True,
                    "chat_tracking": True
                }
            },
            "security_settings": {
                "system": {
                    "vault_access": "auto",
                    "api_keys": "master",
                    "storage_access": "full"
                },
                "isolated": {
                    "vault_access": "request",
                    "api_keys": "dedicated",
                    "storage_access": "project"
                },
                "project": {
                    "vault_access": "request",
                    "api_keys": "prompt",
                    "storage_access": "project"
                },
                "shared": {
                    "vault_access": "auto",
                    "api_keys": "master",
                    "storage_access": "shared"
                }
            },
            "auto_actions": {
                "daily_discovery": True,
                "weekly_lifecycle_review": True,
                "monthly_security_audit": True,
                "backup_frequency": "daily",
                "cleanup_threshold_days": 30
            },
            "integrations": {
                "dashboard_sync": True,
                "chat_logging": True,
                "terminal_tracking": True,
                "github_integration": False,
                "cloud_backup": True
            }
        }
        
        if self.rules_file.exists():
            with open(self.rules_file, 'r') as f:
                self.rules = json.load(f)
                # Merge with defaults
                for key, value in default_rules.items():
                    if key not in self.rules:
                        self.rules[key] = value
        else:
            self.rules = default_rules
            self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.save_rules()
        
        # Load template hierarchy
        self.template_hierarchy = self.load_template_hierarchy()
    
    def load_template_hierarchy(self) -> Dict:
        """Load template hierarchy configuration"""
        hierarchy_file = self.template_dir / "template-hierarchy.json"
        
        default_hierarchy = {
            "base": {
                "description": "Base template for all projects",
                "parent": None,
                "files": ["CLAUDE.md", "TODO.md"],
                "variables": {
                    "PROJECT_NAME": "Project Name",
                    "PROJECT_TYPE": "Project Type",
                    "CREATED_DATE": "Creation Date",
                    "SECURITY_LEVEL": "Security Level"
                }
            },
            "development": {
                "description": "Software development projects",
                "parent": "base",
                "files": ["README.md", ".gitignore", "requirements.txt"],
                "variables": {
                    "FRAMEWORK": "Development Framework",
                    "LANGUAGE": "Programming Language"
                }
            },
            "claude-project": {
                "description": "Claude Code projects with enhanced context",
                "parent": "base", 
                "files": ["HANDOFFS.md", "SECURITY.md"],
                "variables": {
                    "CLAUDE_CONTEXT": "Claude-specific context",
                    "PROJECT_GOALS": "Project objectives"
                }
            },
            "data-analysis": {
                "description": "Data analysis and research projects",
                "parent": "base",
                "files": ["data-notes.md", "analysis-log.md"],
                "variables": {
                    "DATA_SOURCES": "Data sources",
                    "ANALYSIS_TYPE": "Type of analysis"
                }
            },
            "system-tool": {
                "description": "Personal productivity tools",
                "parent": "development",
                "files": ["ARCHITECTURE.md", "DEPLOYMENT.md"],
                "variables": {
                    "TOOL_PURPOSE": "Tool's primary purpose",
                    "INTEGRATION_POINTS": "System integrations"
                }
            }
        }
        
        if hierarchy_file.exists():
            try:
                with open(hierarchy_file, 'r') as f:
                    hierarchy = json.load(f)
                # Merge with defaults for any missing templates
                for template, config in default_hierarchy.items():
                    if template not in hierarchy:
                        hierarchy[template] = config
                return hierarchy
            except Exception as e:
                self.logger.error(f"Error loading template hierarchy: {e}")
                
        # Save default hierarchy
        with open(hierarchy_file, 'w') as f:
            json.dump(default_hierarchy, f, indent=2)
        
        return default_hierarchy
    
    def get_template_inheritance_chain(self, template_type: str) -> List[str]:
        """Get the full inheritance chain for a template type"""
        chain = []
        current = template_type
        
        while current and current in self.template_hierarchy:
            chain.append(current)
            current = self.template_hierarchy[current].get("parent")
            
            # Prevent infinite loops
            if current in chain:
                break
        
        return chain
    
    def resolve_template_files(self, template_type: str) -> List[str]:
        """Resolve all files for a template including inheritance"""
        inheritance_chain = self.get_template_inheritance_chain(template_type)
        all_files = []
        
        # Collect files from inheritance chain (child overrides parent)
        for template in reversed(inheritance_chain):  # Start from base
            template_config = self.template_hierarchy.get(template, {})
            files = template_config.get("files", [])
            for file in files:
                if file not in all_files:
                    all_files.append(file)
        
        return all_files
    
    def resolve_template_variables(self, template_type: str) -> Dict:
        """Resolve all variables for a template including inheritance"""
        inheritance_chain = self.get_template_inheritance_chain(template_type)
        all_variables = {}
        
        # Collect variables from inheritance chain (child overrides parent)
        for template in reversed(inheritance_chain):  # Start from base
            template_config = self.template_hierarchy.get(template, {})
            variables = template_config.get("variables", {})
            all_variables.update(variables)
        
        return all_variables
    
    def save_rules(self):
        """Save enhanced rules"""
        with open(self.rules_file, 'w') as f:
            json.dump(self.rules, f, indent=2)
    
    def create_project_interactive(self) -> Optional[str]:
        """Interactive project creation with security wizard"""
        print("\n🚀 Enhanced Project Creation Wizard")
        print("=" * 50)
        
        # Get basic project info
        project_name = input("Project name: ").strip()
        if not project_name:
            print("❌ Project name is required")
            return None
        
        project_id = project_name.lower().replace(" ", "-").replace("_", "-")
        
        # Show project types
        print(f"\n📋 Available Project Types:")
        for i, (type_key, type_info) in enumerate(self.rules["project_types"].items(), 1):
            print(f"  {i}. {type_key}: {type_info['description']}")
        
        try:
            type_choice = int(input(f"\\nSelect type (1-{len(self.rules['project_types'])}): "))
            project_type = list(self.rules["project_types"].keys())[type_choice - 1]
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return None
        
        type_config = self.rules["project_types"][project_type]
        
        # Security configuration
        print(f"\\n🔐 Security Configuration:")
        print(f"  Default level: {type_config['security_level']}")
        
        security_settings = self.rules["security_settings"][type_config["security_level"]]
        print(f"  Vault access: {security_settings['vault_access']}")
        print(f"  API keys: {security_settings['api_keys']}")
        print(f"  Storage access: {security_settings['storage_access']}")
        
        change_security = input("\\nChange security settings? (y/n): ").lower().strip() == 'y'
        
        if change_security:
            print("\\n🛡️ Security Levels:")
            for i, (level, settings) in enumerate(self.rules["security_settings"].items(), 1):
                print(f"  {i}. {level}: {settings['vault_access']} vault, {settings['api_keys']} keys")
            
            try:
                security_choice = int(input(f"Select security level (1-{len(self.rules['security_settings'])}): "))
                security_level = list(self.rules["security_settings"].keys())[security_choice - 1]
                security_settings = self.rules["security_settings"][security_level]
            except (ValueError, IndexError):
                print("Using default security settings")
                security_level = type_config['security_level']
        else:
            security_level = type_config['security_level']
        
        # Additional options
        print(f"\\n⚙️ Additional Options:")
        chat_tracking = input(f"Enable chat tracking? (default: {type_config['chat_tracking']}) (y/n): ").lower().strip()
        chat_tracking = chat_tracking == 'y' if chat_tracking else type_config['chat_tracking']
        
        auto_backup = input(f"Enable auto backup? (default: {type_config['auto_backup']}) (y/n): ").lower().strip()
        auto_backup = auto_backup == 'y' if auto_backup else type_config['auto_backup']
        
        # Create project
        project_config = {
            "name": project_name,
            "id": project_id,
            "type": project_type,
            "security_level": security_level,
            "chat_tracking": chat_tracking,
            "auto_backup": auto_backup,
            "created_at": datetime.now().isoformat(),
            "templates": type_config["templates"],
            "lifecycle_stage": type_config["lifecycle_stage"]
        }
        
        return self.create_project(project_config)
    
    def create_project(self, config: Dict) -> Optional[str]:
        """Create project with enhanced configuration"""
        project_id = config["id"]
        
        # Determine target directory based on lifecycle stage
        stage_dirs = {
            "active": self.active_dir,
            "staging": self.staging_dir,
            "systems": self.systems_dir
        }
        
        target_dir = stage_dirs.get(config["lifecycle_stage"], self.staging_dir)
        project_path = target_dir / project_id
        
        if project_path.exists():
            self.logger.error(f"Project already exists: {project_path}")
            return None
        
        try:
            # Create project directory
            project_path.mkdir(parents=True)
            
            # Create templates
            self.create_project_templates(project_path, config)
            
            # Setup security if needed
            if config["security_level"] == "isolated":
                self.setup_project_security(project_id, config)
            
            # Initialize chat tracking if enabled
            if config["chat_tracking"]:
                self.setup_chat_tracking(project_id, config)
            
            # Create project metadata
            metadata_file = project_path / ".project-meta.json"
            with open(metadata_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Register with lifecycle manager
            self.register_with_lifecycle_manager(project_id, config)
            
            # Update dashboard if integration enabled
            if self.rules["integrations"]["dashboard_sync"]:
                self.update_dashboard_integration(project_id, config)
            
            self.logger.info(f"Created project: {project_id} in {target_dir}")
            print(f"✅ Project created: {project_path}")
            
            return str(project_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create project {project_id}: {e}")
            if project_path.exists():
                shutil.rmtree(project_path)
            return None
    
    def create_project_templates(self, project_path: Path, config: Dict):
        """Create project templates with hierarchical inheritance and variable substitution"""
        project_type = config.get("type", "base")
        
        # Get all files for this template type (including inherited)
        template_files = self.resolve_template_files(project_type)
        
        # Get all variables for this template type (including inherited)
        template_variables = self.resolve_template_variables(project_type)
        
        # Base template variables
        template_vars = {
            "PROJECT_NAME": config["name"],
            "PROJECT_ID": config["id"],
            "PROJECT_TYPE": config["type"],
            "CREATED_DATE": datetime.now().strftime("%Y-%m-%d"),
            "SECURITY_LEVEL": config["security_level"],
            "CHAT_TRACKING": "Yes" if config["chat_tracking"] else "No",
            "AUTO_BACKUP": "Yes" if config["auto_backup"] else "No"
        }
        
        # Add template-specific variables
        template_vars.update(template_variables)
        
        # Create all template files
        for template_name in template_files:
            target_file = project_path / template_name
            
            # Try to find template file in hierarchy
            template_content = self.find_template_content(template_name, project_type)
            
            if template_content:
                # Substitute variables
                for var, value in template_vars.items():
                    if isinstance(value, str):
                        template_content = template_content.replace(f"{{{var}}}", value)
                
                target_file.write_text(template_content)
            else:
                # Create basic template
                self.create_basic_template(target_file, template_name, template_vars)
    
    def find_template_content(self, template_name: str, project_type: str) -> Optional[str]:
        """Find template content by searching through inheritance chain"""
        inheritance_chain = self.get_template_inheritance_chain(project_type)
        
        # Search for template file in inheritance order (child first)
        for template_type in inheritance_chain:
            template_file = self.template_dir / template_type / template_name
            if template_file.exists():
                try:
                    return template_file.read_text()
                except Exception as e:
                    self.logger.error(f"Error reading template {template_file}: {e}")
        
        # Try master template directory
        master_template = self.template_dir / "master" / template_name
        if master_template.exists():
            try:
                return master_template.read_text()
            except Exception as e:
                self.logger.error(f"Error reading master template {master_template}: {e}")
        
        return None
    
    def create_basic_template(self, target_file: Path, template_name: str, vars: Dict):
        """Create basic template if template file doesn't exist"""
        if template_name == "CLAUDE.md":
            content = f"""# {vars['PROJECT_NAME']}

**Project Type:** {vars['PROJECT_TYPE']}  
**Created:** {vars['CREATED_DATE']}  
**Security Level:** {vars['SECURITY_LEVEL']}  

## Project Overview

Brief description of what this project does and its goals.

## Current Status

- [ ] Initial setup complete
- [ ] Requirements gathered
- [ ] Implementation started

## Context for Claude

This is a {vars['PROJECT_TYPE']} project with {vars['SECURITY_LEVEL']} security settings.

Chat tracking: {vars['CHAT_TRACKING']}  
Auto backup: {vars['AUTO_BACKUP']}

## Notes

Add project-specific notes, requirements, and context here.
"""
        
        elif template_name == "TODO.md":
            content = f"""# {vars['PROJECT_NAME']} - TODO

## High Priority
- [ ] Define project requirements
- [ ] Set up initial structure

## Medium Priority
- [ ] Add documentation
- [ ] Create tests

## Low Priority
- [ ] Optimize performance
- [ ] Add features

## Completed
- [x] Project created ({vars['CREATED_DATE']})

---
*Last updated: {vars['CREATED_DATE']}*
"""
        
        elif template_name == "README.md":
            content = f"""# {vars['PROJECT_NAME']}

{vars['PROJECT_TYPE']} project created on {vars['CREATED_DATE']}.

## Description

Brief description of the project.

## Usage

How to use this project.

## Requirements

List any dependencies or requirements.
"""
        
        else:
            content = f"""# {template_name}

Project: {vars['PROJECT_NAME']}  
Created: {vars['CREATED_DATE']}  
Type: {vars['PROJECT_TYPE']}  

Add content specific to {template_name} here.
"""
        
        target_file.write_text(content)
    
    def setup_project_security(self, project_id: str, config: Dict):
        """Setup isolated security for project"""
        try:
            # Create project-specific vault entry
            vault_script = self.vault_dir / "vault-manager.py"
            if vault_script.exists():
                # This would create project-specific credential storage
                subprocess.run([
                    "python3", str(vault_script),
                    "--action", "setup-project",
                    "--project", project_id
                ], cwd=str(self.vault_dir), check=False)
            
            self.logger.info(f"Setup security for project: {project_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup security for {project_id}: {e}")
    
    def setup_chat_tracking(self, project_id: str, config: Dict):
        """Setup chat tracking for project"""
        try:
            # Create chat tracking directory
            chat_dir = self.systems_dir / "chat-sessions" / project_id
            chat_dir.mkdir(parents=True, exist_ok=True)
            
            # Create initial chat session file
            session_file = chat_dir / f"session-{datetime.now().strftime('%Y%m%d')}.json"
            session_data = {
                "project_id": project_id,
                "created_at": datetime.now().isoformat(),
                "sessions": [],
                "total_duration": 0,
                "active_terminal": None
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.info(f"Setup chat tracking for project: {project_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup chat tracking for {project_id}: {e}")
    
    def register_with_lifecycle_manager(self, project_id: str, config: Dict):
        """Register project with lifecycle manager"""
        try:
            # This would integrate with the lifecycle manager
            # For now, we'll create a registration file
            registration_file = self.systems_dir / "project-registrations.json"
            
            if registration_file.exists():
                with open(registration_file, 'r') as f:
                    registrations = json.load(f)
            else:
                registrations = {}
            
            registrations[project_id] = {
                "config": config,
                "registered_at": datetime.now().isoformat(),
                "lifecycle_events": []
            }
            
            with open(registration_file, 'w') as f:
                json.dump(registrations, f, indent=2)
            
            self.logger.info(f"Registered project with lifecycle manager: {project_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to register project {project_id}: {e}")
    
    def update_dashboard_integration(self, project_id: str, config: Dict):
        """Update dashboard with new project"""
        try:
            # Update the idea backlog with new project
            backlog_file = self.base_path / "Personal-OS" / "project-management" / "idea-backlog.json"
            
            if backlog_file.exists():
                with open(backlog_file, 'r') as f:
                    backlog = json.load(f)
            else:
                backlog = {"ideas": []}
            
            # Add project to backlog
            new_idea = {
                "id": project_id,
                "title": config["name"],
                "category": config["type"],
                "priority": "medium",
                "effort": "medium",
                "status": "selected" if config["lifecycle_stage"] == "active" else "backlog",
                "description": f"Enhanced {config['type']} project with {config['security_level']} security",
                "tags": [config["type"], config["security_level"]],
                "created_date": config["created_at"],
                "phase": "planning"
            }
            
            backlog["ideas"].append(new_idea)
            
            with open(backlog_file, 'w') as f:
                json.dump(backlog, f, indent=2)
            
            self.logger.info(f"Updated dashboard integration for project: {project_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to update dashboard for {project_id}: {e}")
    
    def list_projects(self, lifecycle_stage: str = None) -> List[Dict]:
        """List projects with enhanced metadata"""
        projects = []
        
        search_dirs = []
        if lifecycle_stage:
            stage_dirs = {
                "active": [self.active_dir],
                "staging": [self.staging_dir],
                "systems": [self.systems_dir]
            }
            search_dirs = stage_dirs.get(lifecycle_stage, [])
        else:
            search_dirs = [self.active_dir, self.staging_dir, self.systems_dir]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            for project_dir in search_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                
                metadata_file = project_dir / ".project-meta.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        metadata["path"] = str(project_dir)
                        metadata["current_stage"] = search_dir.name
                        projects.append(metadata)
                        
                    except Exception as e:
                        self.logger.error(f"Could not read metadata for {project_dir}: {e}")
        
        return projects
    
    def generate_project_report(self) -> Dict:
        """Generate comprehensive project report"""
        projects = self.list_projects()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_projects": len(projects),
            "by_stage": {},
            "by_type": {},
            "security_levels": {},
            "chat_tracking_enabled": 0,
            "auto_backup_enabled": 0
        }
        
        for project in projects:
            # Count by stage
            stage = project["current_stage"]
            report["by_stage"][stage] = report["by_stage"].get(stage, 0) + 1
            
            # Count by type
            proj_type = project["type"]
            report["by_type"][proj_type] = report["by_type"].get(proj_type, 0) + 1
            
            # Count by security level
            security = project["security_level"]
            report["security_levels"][security] = report["security_levels"].get(security, 0) + 1
            
            # Count features
            if project.get("chat_tracking", False):
                report["chat_tracking_enabled"] += 1
            
            if project.get("auto_backup", False):
                report["auto_backup_enabled"] += 1
        
        return report

def main():
    """CLI interface for enhanced project management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Personal OS Project Manager")
    parser.add_argument("--action", choices=["create", "list", "report", "interactive", "templates", "inheritance", "apply-templates"], required=True)
    parser.add_argument("--type", help="Project type")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--stage", choices=["active", "staging", "systems"], help="Lifecycle stage filter")
    parser.add_argument("--project-path", help="Project path for applying templates")
    
    args = parser.parse_args()
    
    manager = EnhancedProjectManager()
    
    try:
        if args.action == "interactive":
            project_path = manager.create_project_interactive()
            if project_path:
                print(f"\\n🎉 Project created successfully at: {project_path}")
            else:
                print("\\n❌ Project creation failed")
        
        elif args.action == "create":
            if not args.name or not args.type:
                print("Error: --name and --type required for create action")
                return
            
            config = {
                "name": args.name,
                "id": args.name.lower().replace(" ", "-"),
                "type": args.type,
                "security_level": "shared",
                "chat_tracking": True,
                "auto_backup": True,
                "created_at": datetime.now().isoformat(),
                "templates": ["CLAUDE.md", "TODO.md"],
                "lifecycle_stage": "staging"
            }
            
            project_path = manager.create_project(config)
            if project_path:
                print(f"✅ Project created: {project_path}")
            else:
                print("❌ Project creation failed")
        
        elif args.action == "list":
            projects = manager.list_projects(args.stage)
            print(f"\\n📋 Projects ({len(projects)}):")
            for project in projects:
                print(f"  • {project['name']} ({project['type']}) - {project['current_stage']} - {project['security_level']} security")
        
        elif args.action == "report":
            report = manager.generate_project_report()
            print(f"\\n📊 Project Report:")
            print(f"  Total projects: {report['total_projects']}")
            print(f"  By stage: {report['by_stage']}")
            print(f"  By type: {report['by_type']}")
            print(f"  Security levels: {report['security_levels']}")
            print(f"  Chat tracking: {report['chat_tracking_enabled']} projects")
            print(f"  Auto backup: {report['auto_backup_enabled']} projects")
        
        elif args.action == "templates":
            print(f"\n📋 TEMPLATE HIERARCHY")
            print("=" * 80)
            
            for template_type, config in manager.template_hierarchy.items():
                print(f"\n🏷️  {template_type}")
                print(f"   Description: {config['description']}")
                print(f"   Parent: {config.get('parent', 'None')}")
                print(f"   Files: {', '.join(config.get('files', []))}")
                
                # Show inheritance chain
                chain = manager.get_template_inheritance_chain(template_type)
                if len(chain) > 1:
                    print(f"   Inheritance: {' ← '.join(chain)}")
        
        elif args.action == "inheritance":
            if not args.type:
                print("❌ Error: --type required for inheritance action")
                return
            
            print(f"\n🔍 TEMPLATE INHERITANCE: {args.type}")
            print("=" * 80)
            
            if args.type not in manager.template_hierarchy:
                print(f"❌ Template type '{args.type}' not found")
                return
            
            # Show inheritance chain
            chain = manager.get_template_inheritance_chain(args.type)
            print(f"Inheritance Chain: {' ← '.join(chain)}")
            
            # Show resolved files
            files = manager.resolve_template_files(args.type)
            print(f"\nResolved Files: {', '.join(files)}")
            
            # Show resolved variables
            variables = manager.resolve_template_variables(args.type)
            print(f"\nResolved Variables:")
            for var, desc in variables.items():
                print(f"   • {var}: {desc}")
        
        elif args.action == "apply-templates":
            if not args.project_path:
                print("❌ Error: --project-path required for apply-templates action")
                return
            
            project_path = Path(args.project_path)
            if not project_path.exists():
                print(f"❌ Project path does not exist: {project_path}")
                return
            
            project_type = args.type or "claude-project"
            
            print(f"\n🔧 APPLYING TEMPLATES")
            print("=" * 80)
            print(f"Project Path: {project_path}")
            print(f"Template Type: {project_type}")
            
            # Create mock config for template application
            config = {
                "name": project_path.name,
                "id": project_path.name.lower().replace(" ", "-"),
                "type": project_type,
                "security_level": "project",
                "chat_tracking": True,
                "auto_backup": True
            }
            
            try:
                manager.create_project_templates(project_path, config)
                print(f"✅ Templates applied successfully")
                
                # Show what was created
                files = manager.resolve_template_files(project_type)
                print(f"\nCreated Files:")
                for file_name in files:
                    file_path = project_path / file_name
                    if file_path.exists():
                        print(f"   ✅ {file_name}")
                    else:
                        print(f"   ❌ {file_name} (failed)")
                        
            except Exception as e:
                print(f"❌ Failed to apply templates: {e}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
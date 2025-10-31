#!/usr/bin/env python3
"""
Secure Template Generator
Generates secure .env templates and enhanced project templates with security best practices
Zero token usage - rule-based template generation with security defaults
"""

import os
import json
import logging
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Token tracking integration
import sys
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("token_tracker", Path(__file__).parent / "token-tracker-integration.py")
tracker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker_module)

class SecureTemplateGenerator:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        self.templates_dir = self.systems_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # Security configuration
        self.security_config_file = self.systems_dir / "security-template-config.json"
        self.load_security_config()
        
        # Template lineage tracking
        self.lineage_file = self.systems_dir / "template-lineage.json"
        self.load_lineage_tracking()
        
        # Setup logging
        self.setup_logging()
        
        self.logger.info("Secure Template Generator initialized")
    
    def setup_logging(self):
        """Setup template generator logging"""
        log_file = self.systems_dir / "template-generator.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_security_config(self):
        """Load security template configuration"""
        default_config = {
            "env_templates": {
                "development": {
                    "required_vars": [
                        "NODE_ENV=development",
                        "PORT=3000",
                        "DATABASE_URL=# Add your database connection string",
                        "JWT_SECRET=# Generate with: openssl rand -hex 64",
                        "API_KEY=# Your API key here"
                    ],
                    "optional_vars": [
                        "DEBUG=true",
                        "LOG_LEVEL=info",
                        "CORS_ORIGIN=http://localhost:3000"
                    ],
                    "security_notes": [
                        "# SECURITY CHECKLIST:",
                        "# 1. Never commit this file to git (check .gitignore)",
                        "# 2. Use strong, unique passwords and secrets", 
                        "# 3. Rotate API keys regularly",
                        "# 4. Use different secrets for dev/staging/production",
                        "# 5. Consider using a secret management service"
                    ]
                },
                "python": {
                    "required_vars": [
                        "ENVIRONMENT=development",
                        "SECRET_KEY=# Generate with: python -c 'import secrets; print(secrets.token_hex(32))'",
                        "DATABASE_URL=# Your database connection string",
                        "API_KEY=# Your API key here"
                    ],
                    "optional_vars": [
                        "DEBUG=True",
                        "LOG_LEVEL=INFO",
                        "ALLOWED_HOSTS=localhost,127.0.0.1"
                    ]
                },
                "web": {
                    "required_vars": [
                        "REACT_APP_API_URL=http://localhost:3001",
                        "REACT_APP_ENV=development"
                    ],
                    "optional_vars": [
                        "REACT_APP_DEBUG=true",
                        "REACT_APP_ANALYTICS_ID=# Analytics tracking ID"
                    ]
                },
                "claude-project": {
                    "required_vars": [
                        "ANTHROPIC_API_KEY=# Your Claude API key",
                        "PROJECT_MODE=development"
                    ],
                    "optional_vars": [
                        "OPENAI_API_KEY=# Optional OpenAI key for comparison",
                        "MAX_TOKENS=4000",
                        "TEMPERATURE=0.7"
                    ]
                }
            },
            "gitignore_patterns": [
                ".env",
                ".env.local", 
                ".env.*.local",
                "*.log",
                ".DS_Store",
                "__pycache__/",
                "node_modules/"
            ],
            "security_files": {
                "SECURITY.md": True,
                ".env.example": True,
                "README_SECURITY.md": False
            }
        }
        
        if self.security_config_file.exists():
            with open(self.security_config_file, 'r') as f:
                self.security_config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in self.security_config:
                        self.security_config[key] = value
        else:
            self.security_config = default_config
        
        self.save_security_config()
    
    def save_security_config(self):
        """Save security configuration"""
        with open(self.security_config_file, 'w') as f:
            json.dump(self.security_config, f, indent=2)
    
    def load_lineage_tracking(self):
        """Load template lineage tracking"""
        if self.lineage_file.exists():
            with open(self.lineage_file, 'r') as f:
                self.lineage = json.load(f)
        else:
            self.lineage = {
                "templates": {},
                "generated_files": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def save_lineage_tracking(self):
        """Save template lineage tracking"""
        self.lineage["last_updated"] = datetime.now().isoformat()
        with open(self.lineage_file, 'w') as f:
            json.dump(self.lineage, f, indent=2)
    
    def generate_secure_secret(self, length: int = 64) -> str:
        """Generate cryptographically secure random string"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def detect_project_type(self, project_path: Path) -> str:
        """Detect project type for appropriate template selection"""
        if not project_path.exists():
            return "general"
        
        # Check for specific files to determine type
        if (project_path / "package.json").exists():
            # Check if it's a React app
            try:
                with open(project_path / "package.json", 'r') as f:
                    package_data = json.load(f)
                    if "react" in package_data.get("dependencies", {}):
                        return "web"
                    else:
                        return "development"
            except:
                return "development"
        
        elif (project_path / "requirements.txt").exists():
            return "python"
        
        elif (project_path / "CLAUDE.md").exists():
            return "claude-project"
        
        elif any(f.suffix == '.html' for f in project_path.glob("*.html")):
            return "web"
        
        else:
            return "development"
    
    def generate_env_template(self, project_path: Path, project_type: str = None) -> Tuple[str, str]:
        """Generate secure .env template and .env.example files"""
        if not project_type:
            project_type = self.detect_project_type(project_path)
        
        template_config = self.security_config["env_templates"].get(project_type, self.security_config["env_templates"]["development"])
        
        env_content = []
        example_content = []
        
        # Add header with security notes
        header = [
            "# ====================================",
            f"# Environment Configuration for {project_path.name}",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Project Type: {project_type}",
            "# ====================================",
            ""
        ]
        
        env_content.extend(header)
        example_content.extend(header)
        
        # Add security notes
        if "security_notes" in template_config:
            env_content.extend(template_config["security_notes"])
            example_content.extend(template_config["security_notes"])
            env_content.append("")
            example_content.append("")
        
        # Add required variables
        env_content.append("# Required Configuration")
        example_content.append("# Required Configuration")
        
        for var in template_config.get("required_vars", []):
            if "=" in var:
                key, value = var.split("=", 1)
                
                # Generate actual values for .env, placeholders for .env.example
                if "secret" in key.lower() or "key" in key.lower():
                    # Generate secure secret for .env
                    if "jwt" in key.lower():
                        actual_value = self.generate_secure_secret(64)
                    else:
                        actual_value = f"# REPLACE_WITH_YOUR_{key.upper()}"
                    
                    example_value = f"# YOUR_{key.upper()}_HERE"
                    
                    env_content.append(f"{key}={actual_value}")
                    example_content.append(f"{key}={example_value}")
                    
                elif value.startswith("#"):
                    # Keep comments as-is
                    env_content.append(var)
                    example_content.append(var)
                else:
                    # Regular config value
                    env_content.append(var)
                    example_content.append(var)
            else:
                env_content.append(f"{var}=")
                example_content.append(f"{var}=")
        
        # Add optional variables
        if template_config.get("optional_vars"):
            env_content.append("")
            env_content.append("# Optional Configuration")
            example_content.append("")
            example_content.append("# Optional Configuration")
            
            for var in template_config["optional_vars"]:
                env_content.append(f"# {var}")
                example_content.append(f"# {var}")
        
        # Add custom section for project-specific variables
        env_content.extend([
            "",
            "# Project-Specific Configuration",
            "# Add your custom environment variables below:",
            "",
            "# Custom APIs",
            "# CUSTOM_API_KEY=",
            "# CUSTOM_API_URL=",
            "",
            "# Feature Flags", 
            "# ENABLE_FEATURE_X=false",
            "# ENABLE_BETA_FEATURES=false",
            "",
            "# External Services",
            "# REDIS_URL=",
            "# ELASTICSEARCH_URL=",
            ""
        ])
        
        example_content.extend([
            "",
            "# Project-Specific Configuration", 
            "# Add your custom environment variables below:",
            "# See .env for examples",
            ""
        ])
        
        return "\n".join(env_content), "\n".join(example_content)
    
    def generate_gitignore(self, project_path: Path, project_type: str = None) -> str:
        """Generate comprehensive .gitignore file"""
        if not project_type:
            project_type = self.detect_project_type(project_path)
        
        gitignore_sections = {
            "Environment Files": [
                ".env",
                ".env.local",
                ".env.*.local", 
                ".env.backup",
                "!.env.example"
            ],
            "Logs": [
                "*.log",
                "logs/",
                "npm-debug.log*",
                "yarn-debug.log*",
                "yarn-error.log*"
            ],
            "Runtime Data": [
                "pids",
                "*.pid",
                "*.seed",
                "*.pid.lock"
            ],
            "OS Generated Files": [
                ".DS_Store",
                ".DS_Store?", 
                "._*",
                ".Spotlight-V100",
                ".Trashes",
                "ehthumbs.db",
                "Thumbs.db"
            ]
        }
        
        # Add type-specific ignores
        if project_type in ["development", "web"]:
            gitignore_sections["Node.js"] = [
                "node_modules/",
                "npm-debug.log*",
                "yarn-debug.log*",
                "yarn-error.log*",
                ".npm",
                ".yarn-integrity",
                "build/",
                "dist/"
            ]
        
        if project_type == "python":
            gitignore_sections["Python"] = [
                "__pycache__/",
                "*.py[cod]",
                "*$py.class",
                "*.so",
                ".Python",
                "env/",
                "venv/",
                ".venv",
                "pip-log.txt",
                "pip-delete-this-directory.txt",
                ".pytest_cache/"
            ]
        
        # Build gitignore content
        content = [
            f"# .gitignore for {project_path.name}",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Project Type: {project_type}",
            "",
            "# ====================================", 
            "# SECURITY: Never commit sensitive data!",
            "# ====================================",
            ""
        ]
        
        for section_name, patterns in gitignore_sections.items():
            content.append(f"# {section_name}")
            content.extend(patterns)
            content.append("")
        
        # Add custom section
        content.extend([
            "# Project-Specific Ignores",
            "# Add custom patterns below:",
            "",
            "# Temporary files",
            "*.tmp",
            "*.temp",
            "",
            "# IDE files", 
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# Local development",
            "local/",
            "dev-data/",
            "test-data/",
            ""
        ])
        
        return "\n".join(content)
    
    def generate_security_md(self, project_path: Path, project_type: str = None) -> str:
        """Generate SECURITY.md template"""
        if not project_type:
            project_type = self.detect_project_type(project_path)
        
        content = [
            f"# Security Guidelines for {project_path.name}",
            "",
            f"**Project Type:** {project_type}  ",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}  ",
            f"**Status:** Development",
            "",
            "## 🔐 Security Checklist",
            "",
            "### Environment & Secrets",
            "- [ ] `.env` file is in `.gitignore`",
            "- [ ] No secrets committed to repository",
            "- [ ] Strong, unique secrets generated",
            "- [ ] Different secrets for dev/staging/production", 
            "- [ ] Regular API key rotation schedule",
            "",
            "### Code Security",
            "- [ ] Input validation implemented",
            "- [ ] SQL injection prevention",
            "- [ ] XSS protection enabled",
            "- [ ] CSRF protection implemented",
            "- [ ] Authentication & authorization working",
            "",
            "### Infrastructure",
            "- [ ] HTTPS enabled in production",
            "- [ ] Security headers configured",
            "- [ ] Rate limiting implemented",
            "- [ ] Logging & monitoring active",
            "- [ ] Error handling doesn't leak info",
            "",
            "## 🛡️ Security Measures",
            "",
            "### Environment Variables",
            "This project uses environment variables for configuration:",
            "",
            "```bash",
            "# Copy example file and customize",
            "cp .env.example .env",
            "# Edit .env with your actual values",
            "nano .env",
            "```",
            "",
            "### API Key Management",
            "- Store API keys in `.env` file only",
            "- Use vault system for production: `python3 ../systems/vault-manager.py`",
            "- Rotate keys every 90 days",
            "- Monitor API usage for anomalies",
            "",
            "### Development Security",
            "- Keep dependencies updated",
            "- Run security scans regularly",
            "- Review code for security issues",
            "- Test authentication and authorization",
            "",
            "## 🚨 Incident Response",
            "",
            "If you suspect a security issue:",
            "",
            "1. **Immediate**: Rotate compromised credentials",
            "2. **Assessment**: Check logs for suspicious activity",
            "3. **Containment**: Disable affected services if needed",
            "4. **Documentation**: Record incident details",
            "5. **Review**: Update security measures",
            "",
            "## 📞 Security Contacts",
            "",
            "- **Project Owner**: [Your Name]",
            "- **Security Lead**: [Security Contact]",
            "- **Emergency**: [Emergency Contact]",
            "",
            "## 🔄 Security Reviews",
            "",
            "- **Last Review**: [Date]",
            "- **Next Review**: [Date + 3 months]",
            "- **Review Frequency**: Quarterly",
            "",
            "---",
            "",
            "*This security document should be updated regularly and reviewed with each major release.*"
        ]
        
        # Add type-specific security notes
        if project_type == "web":
            content.extend([
                "",
                "## 🌐 Web-Specific Security",
                "",
                "- [ ] Content Security Policy (CSP) configured",
                "- [ ] Secure cookies enabled",
                "- [ ] CORS properly configured",
                "- [ ] Input sanitization on frontend",
                "- [ ] Dependency vulnerability scanning"
            ])
        
        elif project_type == "python":
            content.extend([
                "",
                "## 🐍 Python-Specific Security",
                "",
                "- [ ] Virtual environment isolated",
                "- [ ] Requirements.txt pinned versions",
                "- [ ] `bandit` security linting enabled",
                "- [ ] SQL parameterization used",
                "- [ ] Pickle usage avoided"
            ])
        
        elif project_type == "claude-project":
            content.extend([
                "",
                "## 🤖 AI Project Security",
                "",
                "- [ ] API keys for Claude/OpenAI secured",
                "- [ ] Token usage monitoring active",
                "- [ ] Input/output validation implemented",
                "- [ ] Rate limiting for API calls",
                "- [ ] Prompt injection protection"
            ])
        
        return "\n".join(content)
    
    def create_secure_project_template(self, project_path: Path, project_type: str = None) -> Dict:
        """Create complete secure template package for project"""
        if not project_path.exists():
            project_path.mkdir(parents=True)
        
        if not project_type:
            project_type = self.detect_project_type(project_path)
        
        results = {
            "project_path": str(project_path),
            "project_type": project_type,
            "generated_at": datetime.now().isoformat(),
            "files_created": [],
            "templates_used": [],
            "security_features": []
        }
        
        # Generate .env and .env.example
        env_content, env_example_content = self.generate_env_template(project_path, project_type)
        
        env_file = project_path / ".env"
        env_example_file = project_path / ".env.example"
        
        # Create .env file with secure defaults
        with open(env_file, 'w') as f:
            f.write(env_content)
        results["files_created"].append(str(env_file))
        results["templates_used"].append("env_template")
        results["security_features"].append("Secure .env file with generated secrets")
        
        # Create .env.example for documentation
        with open(env_example_file, 'w') as f:
            f.write(env_example_content)
        results["files_created"].append(str(env_example_file))
        results["security_features"].append(".env.example for documentation")
        
        # Generate .gitignore
        gitignore_content = self.generate_gitignore(project_path, project_type)
        gitignore_file = project_path / ".gitignore"
        
        with open(gitignore_file, 'w') as f:
            f.write(gitignore_content)
        results["files_created"].append(str(gitignore_file))
        results["templates_used"].append("gitignore_template")
        results["security_features"].append("Comprehensive .gitignore with security patterns")
        
        # Generate SECURITY.md
        security_content = self.generate_security_md(project_path, project_type)
        security_file = project_path / "SECURITY.md"
        
        with open(security_file, 'w') as f:
            f.write(security_content)
        results["files_created"].append(str(security_file))
        results["templates_used"].append("security_md_template")
        results["security_features"].append("Security guidelines and checklist")
        
        # Track template lineage
        template_id = f"{project_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.lineage["generated_files"][template_id] = {
            "project_path": str(project_path),
            "project_type": project_type,
            "generated_at": datetime.now().isoformat(),
            "files": results["files_created"],
            "templates": results["templates_used"],
            "generator_version": "1.0.0"
        }
        
        self.save_lineage_tracking()
        
        # Track token usage for template generation
        tracker_module.track_template_generation()
        
        self.logger.info(f"Generated secure templates for {project_path.name} ({project_type})")
        
        return results
    
    def update_existing_project_security(self, project_path: Path) -> Dict:
        """Update existing project with security templates"""
        if not project_path.exists():
            return {"error": "Project path does not exist"}
        
        project_type = self.detect_project_type(project_path)
        
        results = {
            "project_path": str(project_path),
            "project_type": project_type,
            "updated_at": datetime.now().isoformat(),
            "files_updated": [],
            "files_created": [],
            "backup_created": []
        }
        
        # Backup existing files before updating
        backup_dir = project_path / ".security-backup"
        backup_dir.mkdir(exist_ok=True)
        
        files_to_check = [".env", ".gitignore", "SECURITY.md"]
        
        for filename in files_to_check:
            file_path = project_path / filename
            if file_path.exists():
                backup_path = backup_dir / f"{filename}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path.write_text(file_path.read_text())
                results["backup_created"].append(str(backup_path))
        
        # Generate new secure templates
        template_results = self.create_secure_project_template(project_path, project_type)
        
        results["files_created"] = template_results["files_created"]
        results["security_features"] = template_results["security_features"]
        
        self.logger.info(f"Updated security templates for {project_path.name}")
        
        return results
    
    def apply_project_template(self, project_path: Path, project_type: str = None):
        """Apply appropriate template to new project folder with user interaction"""
        if not project_type:
            project_type = self.detect_project_type(project_path)
        
        # Create templates directory and load templates
        self.setup_project_templates()
        
        # Get available templates for this project type
        available_templates = self.get_available_templates(project_type)
        
        # If multiple templates available, create selection prompt file
        if len(available_templates) > 1:
            self.create_template_selection_prompt(project_path, available_templates, project_type)
        else:
            # Apply default template immediately
            template_name = available_templates[0] if available_templates else "default"
            self.apply_specific_template(project_path, template_name, project_type)
    
    def setup_project_templates(self):
        """Setup project templates directory structure"""
        templates_base = self.templates_dir
        
        # Create template categories
        template_categories = {
            "claude-projects": ["basic", "data-analysis", "web-scraper", "dashboard", "automation"],
            "development": ["nodejs", "python", "web", "api", "fullstack"],
            "documentation": ["project-docs", "api-docs", "user-guides"],
            "general": ["research", "planning", "prototype"]
        }
        
        for category, templates in template_categories.items():
            category_dir = templates_base / category
            category_dir.mkdir(exist_ok=True)
            
            for template_name in templates:
                template_dir = category_dir / template_name
                template_dir.mkdir(exist_ok=True)
                
                # Create template metadata if it doesn't exist
                metadata_file = template_dir / "template.json"
                if not metadata_file.exists():
                    metadata = {
                        "name": template_name,
                        "category": category,
                        "description": f"{template_name.title()} project template",
                        "files": ["CLAUDE.md", "TODO.md", ".gitignore", ".env.example"],
                        "created_at": datetime.now().isoformat()
                    }
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
    
    def get_available_templates(self, project_type: str) -> List[str]:
        """Get available templates for project type"""
        templates = []
        
        # Map project types to template categories
        type_mapping = {
            "nodejs": "development/nodejs",
            "python": "development/python", 
            "web": "development/web",
            "claude-project": "claude-projects/basic",
            "documentation": "documentation/project-docs",
            "general": "general/research"
        }
        
        template_path = type_mapping.get(project_type, "general/research")
        template_dir = self.templates_dir / template_path
        
        if template_dir.exists():
            templates.append(template_path.split('/')[-1])
        
        # Add related templates
        category = template_path.split('/')[0]
        category_dir = self.templates_dir / category
        if category_dir.exists():
            for template_dir in category_dir.iterdir():
                if template_dir.is_dir() and template_dir.name not in templates:
                    templates.append(template_dir.name)
        
        return templates or ["default"]
    
    def create_template_selection_prompt(self, project_path: Path, templates: List[str], project_type: str):
        """Create interactive template selection prompt"""
        prompt_file = project_path / ".template-selection-prompt.md"
        
        content = [
            f"# Template Selection for {project_path.name}",
            "",
            f"**Project Type Detected**: {project_type}",
            f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Available Templates:",
            ""
        ]
        
        for i, template in enumerate(templates, 1):
            content.append(f"{i}. **{template.title()}** - {template} template for {project_type} projects")
        
        content.extend([
            "",
            "## Instructions:",
            "1. Choose your preferred template number from above",
            "2. Run: `python3 systems/secure-template-generator.py --action apply-template --project \"{}\" --template <template_name>`".format(project_path),
            "3. Or run: `python3 systems/project-discovery-service.py --action apply-default` to use the default template",
            "",
            "## Default Template:",
            f"If no selection is made, the **{templates[0]}** template will be applied automatically.",
            "",
            "---",
            "*This file will be removed after template selection*"
        ])
        
        with open(prompt_file, 'w') as f:
            f.write('\n'.join(content))
        
        self.logger.info(f"Created template selection prompt: {prompt_file}")
        print(f"🎯 New project detected: {project_path.name}")
        print(f"📋 Template selection prompt created: {prompt_file}")
        print(f"💡 Choose from {len(templates)} available templates")
    
    def apply_specific_template(self, project_path: Path, template_name: str, project_type: str):
        """Apply specific template to project"""
        # Apply security template first
        security_results = self.create_secure_project_template(project_path, project_type)
        
        # Apply project-specific CLAUDE.md template
        claude_md_path = project_path / "CLAUDE.md"
        if not claude_md_path.exists():
            claude_content = self.generate_claude_md_template(project_path.name, project_type, template_name)
            with open(claude_md_path, 'w') as f:
                f.write(claude_content)
            
            self.logger.info(f"Applied {template_name} template to {project_path.name}")
        
        # Clean up selection prompt if it exists
        prompt_file = project_path / ".template-selection-prompt.md"
        if prompt_file.exists():
            prompt_file.unlink()
    
    def generate_claude_md_template(self, project_name: str, project_type: str, template_name: str) -> str:
        """Generate CLAUDE.md template based on project type and template"""
        content = [
            f"# {project_name} - {template_name.title()} Template",
            "",
            f"**Project Type**: {project_type}",
            f"**Template**: {template_name}",
            f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Generated by**: Personal OS Template System",
            "",
            "## Project Overview",
            "",
            f"This is a {project_type} project using the {template_name} template.",
            "Add your project description and goals here.",
            "",
            "## Claude Assistant Guidelines",
            "",
            "### Project Rules",
            "- Follow existing code patterns and conventions",
            "- Maintain security best practices (see SECURITY.md)",
            "- Keep dependencies minimal and up-to-date",
            "- Document all changes in TODO.md",
            "",
            "### Development Workflow",
            "- Use TODO.md for task tracking",
            "- Run security scans regularly",
            "- Test all changes before committing",
            "",
            "## Quick Commands",
            "",
            f"```bash",
            f"# Security scan",
            f"python3 ../systems/security-monitoring-dashboard.py --project \"{project_name}\"",
            f"",
            f"# Update project registry", 
            f"python3 ../systems/project-discovery-service.py --action scan",
            f"```",
            "",
            "---",
            "",
            "**Generated by Personal OS** - Template inheritance system"
        ]
        
        # Add type-specific guidelines
        if project_type == "nodejs":
            content.extend([
                "",
                "## Node.js Specific Guidelines",
                "- Use `npm ci` for reproducible builds",
                "- Keep package.json dependencies updated",
                "- Run `npm audit` for security checks"
            ])
        elif project_type == "python":
            content.extend([
                "",
                "## Python Specific Guidelines", 
                "- Use virtual environments",
                "- Pin exact versions in requirements.txt",
                "- Run `bandit` for security analysis"
            ])
        
        return '\n'.join(content)

def main():
    """CLI interface for secure template generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure Template Generator")
    parser.add_argument("--action", choices=["create", "update", "test", "apply-template"], required=True)
    parser.add_argument("--project", help="Project path")
    parser.add_argument("--type", choices=["development", "python", "web", "claude-project", "nodejs", "documentation"], help="Project type")
    parser.add_argument("--template", help="Template name to apply")
    
    args = parser.parse_args()
    
    generator = SecureTemplateGenerator()
    
    try:
        if args.action == "create":
            if not args.project:
                print("Error: --project required for create action")
                return
            
            project_path = Path(args.project)
            results = generator.create_secure_project_template(project_path, args.type)
            
            print(f"✅ Secure templates created for: {results['project_path']}")
            print(f"  Project type: {results['project_type']}")
            print(f"  Files created: {len(results['files_created'])}")
            print(f"  Security features: {len(results['security_features'])}")
            
            for feature in results['security_features']:
                print(f"    • {feature}")
        
        elif args.action == "update":
            if not args.project:
                print("Error: --project required for update action")
                return
            
            project_path = Path(args.project)
            results = generator.update_existing_project_security(project_path)
            
            if "error" in results:
                print(f"❌ Error: {results['error']}")
                return
            
            print(f"✅ Security templates updated for: {results['project_path']}")
            print(f"  Backups created: {len(results['backup_created'])}")
            print(f"  Files updated: {len(results['files_created'])}")
        
        elif args.action == "apply-template":
            if not args.project:
                print("Error: --project required for apply-template action")
                return
            if not args.template:
                print("Error: --template required for apply-template action")
                return
            
            project_path = Path(args.project)
            project_type = args.type or generator.detect_project_type(project_path)
            
            generator.apply_specific_template(project_path, args.template, project_type)
            
            print(f"✅ Applied {args.template} template to: {project_path.name}")
            print(f"🔍 Run project discovery to register: python3 systems/project-discovery-service.py --action scan")
        
        elif args.action == "test":
            # Test with a temporary project
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                test_path = Path(temp_dir) / "test-security-project"
                results = generator.create_secure_project_template(test_path, "claude-project")
                
                print(f"🧪 Test Results:")
                print(f"  Created {len(results['files_created'])} files")
                print(f"  Security features: {len(results['security_features'])}")
                
                # Show sample content
                env_file = test_path / ".env"
                if env_file.exists():
                    print(f"\n📄 Sample .env content (first 10 lines):")
                    lines = env_file.read_text().split('\n')[:10]
                    for line in lines:
                        print(f"    {line}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
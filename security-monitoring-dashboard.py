#!/usr/bin/env python3
"""
Security Monitoring Dashboard
Monitors security status across Personal OS projects and infrastructure
Provides security insights, alerts, and compliance tracking
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

# Token tracking integration
import sys
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("token_tracker", Path(__file__).parent / "token-tracker-integration.py")
tracker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker_module)

class SecurityMonitoringDashboard:
    def __init__(self, base_path=None, incremental=True):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        self.vault_dir = self.base_path / ".vault"
        self.incremental = incremental  # Enable incremental scanning by default

        # Security data files
        self.security_report_file = self.systems_dir / "security-report.json"
        self.security_config_file = self.systems_dir / "security-config.json"
        self.audit_log_file = self.systems_dir / "security-audit.log"
        self.scan_cache_file = self.systems_dir / "security-scan-cache.json"  # New: track scanned files
        
        # Security thresholds and rules
        self.security_rules = {
            "max_days_since_audit": 30,
            "max_exposed_secrets": 0,
            "required_security_files": [".gitignore", "SECURITY.md"],
            "forbidden_patterns": [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ],
            "vault_access_limit": 10  # Max vault accesses per day
        }
        
        # Setup logging
        self.setup_logging()

        # Load configuration
        self.load_security_config()

        # Load scan cache for incremental scanning
        self.scan_cache = self.load_scan_cache()

        mode = "incremental" if self.incremental else "full"
        self.logger.info(f"Security Monitoring Dashboard initialized ({mode} scan mode)")
    
    def setup_logging(self):
        """Setup security monitoring logging"""
        log_file = self.systems_dir / "security-monitor.log"
        
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
        """Load security monitoring configuration"""
        if self.security_config_file.exists():
            with open(self.security_config_file, 'r') as f:
                config = json.load(f)
                self.security_rules.update(config.get("rules", {}))
        else:
            # Create default security configuration
            default_config = {
                "rules": self.security_rules,
                "monitoring": {
                    "enabled": True,
                    "scan_frequency_hours": 24,
                    "alert_email": None,
                    "slack_webhook": None
                },
                "compliance": {
                    "frameworks": ["personal_security", "data_protection"],
                    "audit_requirements": ["quarterly_review", "vault_audit", "secret_rotation"]
                },
                "created_at": datetime.now().isoformat()
            }
            
            with open(self.security_config_file, 'w') as f:
                json.dump(default_config, f, indent=2)

    def load_scan_cache(self) -> Dict:
        """Load file scan cache for incremental scanning"""
        if self.scan_cache_file.exists():
            try:
                with open(self.scan_cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load scan cache: {e}")
        return {"files": {}, "last_full_scan": None}

    def save_scan_cache(self):
        """Save file scan cache"""
        try:
            with open(self.scan_cache_file, 'w') as f:
                json.dump(self.scan_cache, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save scan cache: {e}")

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None

    def should_scan_file(self, file_path: Path) -> bool:
        """Determine if file should be scanned based on cache"""
        if not self.incremental:
            return True  # Full scan mode

        file_key = str(file_path)
        current_hash = self.get_file_hash(file_path)

        if not current_hash:
            return False  # Can't read file

        cached = self.scan_cache["files"].get(file_key, {})
        cached_hash = cached.get("hash")

        # Scan if new file or modified file
        return current_hash != cached_hash

    def update_file_cache(self, file_path: Path, has_issues: bool):
        """Update cache entry for scanned file"""
        file_key = str(file_path)
        file_hash = self.get_file_hash(file_path)

        if file_hash:
            self.scan_cache["files"][file_key] = {
                "hash": file_hash,
                "last_scanned": datetime.now().isoformat(),
                "has_issues": has_issues
            }

    def get_related_files(self, file_path: Path) -> List[Path]:
        """Get files related to the one with issues (for expanded scanning)"""
        related = []
        project_path = file_path.parent

        # If it's a Python file, find files that import it or are imported by it
        if file_path.suffix == '.py':
            try:
                content = file_path.read_text()
                # Find imports
                import_pattern = r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
                imports = re.findall(import_pattern, content)

                for imp in imports:
                    potential_file = project_path / f"{imp}.py"
                    if potential_file.exists():
                        related.append(potential_file)
            except Exception:
                pass

        # Check for corresponding config files
        config_patterns = ['.env', 'config.json', 'config.yaml', 'settings.py']
        for pattern in config_patterns:
            if pattern.endswith('.py'):
                config_file = project_path / pattern
            else:
                config_file = project_path / pattern

            if config_file.exists() and config_file != file_path:
                related.append(config_file)

        return related

    def scan_project_security(self, project_path: Path) -> Dict:
        """Scan individual project for security issues"""
        security_status = {
            "project_path": str(project_path),
            "project_name": project_path.name,
            "scanned_at": datetime.now().isoformat(),
            "security_score": 100,  # Start with perfect score
            "issues": [],
            "recommendations": [],
            "compliance": {}
        }
        
        if not project_path.exists():
            security_status["issues"].append({
                "type": "critical",
                "category": "missing_project",
                "description": "Project directory not found",
                "severity": "high"
            })
            security_status["security_score"] = 0
            return security_status
        
        # Check for required security files
        for required_file in self.security_rules["required_security_files"]:
            file_path = project_path / required_file
            if not file_path.exists():
                security_status["issues"].append({
                    "type": "missing_file",
                    "category": "security_files",
                    "description": f"Missing {required_file} file",
                    "severity": "medium",
                    "file": required_file
                })
                security_status["security_score"] -= 10
        
        # Scan for exposed secrets in files
        secret_issues = self.scan_for_exposed_secrets(project_path)
        security_status["issues"].extend(secret_issues)
        security_status["security_score"] -= len(secret_issues) * 20  # Severe penalty for exposed secrets
        
        # Check .env file security
        env_issues = self.check_env_file_security(project_path)
        security_status["issues"].extend(env_issues)
        security_status["security_score"] -= len(env_issues) * 15
        
        # Check git security
        git_issues = self.check_git_security(project_path)
        security_status["issues"].extend(git_issues)
        security_status["security_score"] -= len(git_issues) * 5
        
        # Check file permissions
        permission_issues = self.check_file_permissions(project_path)
        security_status["issues"].extend(permission_issues)
        security_status["security_score"] -= len(permission_issues) * 10
        
        # Generate recommendations
        security_status["recommendations"] = self.generate_security_recommendations(security_status["issues"])
        
        # Ensure score doesn't go below 0
        security_status["security_score"] = max(0, security_status["security_score"])
        
        return security_status
    
    def scan_for_exposed_secrets(self, project_path: Path) -> List[Dict]:
        """Scan project files for exposed secrets (incremental mode supported)"""
        issues = []
        files_to_expand = []  # Files with issues that need related file scanning

        # Scan specific file types
        scan_extensions = ['.py', '.js', '.ts', '.env', '.yaml', '.yml', '.json', '.md', '.txt']

        scanned_count = 0
        skipped_count = 0

        for ext in scan_extensions:
            for file_path in project_path.glob(f"**/*{ext}"):
                if file_path.is_file() and not any(skip in str(file_path) for skip in ['.git', 'node_modules', '__pycache__']):

                    # Check if we should scan this file (incremental mode)
                    if not self.should_scan_file(file_path):
                        skipped_count += 1
                        # But check if it previously had issues that need re-checking
                        cached = self.scan_cache["files"].get(str(file_path), {})
                        if cached.get("has_issues"):
                            # Re-check files that previously had issues
                            pass
                        else:
                            continue

                    scanned_count += 1
                    file_has_issues = False

                    try:
                        content = file_path.read_text(encoding='utf-8')

                        for pattern in self.security_rules["forbidden_patterns"]:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                file_has_issues = True
                                issues.append({
                                    "type": "exposed_secret",
                                    "category": "sensitive_data",
                                    "description": f"Potential exposed secret in {file_path.name}",
                                    "severity": "critical",
                                    "file": str(file_path.relative_to(project_path)),
                                    "pattern": pattern,
                                    "line_preview": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                                })

                        # Update cache for this file
                        self.update_file_cache(file_path, file_has_issues)

                        # If issues found, mark for expanded scanning
                        if file_has_issues:
                            files_to_expand.append(file_path)

                    except Exception as e:
                        self.logger.debug(f"Could not scan {file_path}: {e}")

        # Expanded scanning: check related files when issues are found
        if files_to_expand and self.incremental:
            self.logger.info(f"🔍 Found issues in {len(files_to_expand)} files, expanding scan to related files...")
            for problem_file in files_to_expand:
                related_files = self.get_related_files(problem_file)
                for related_file in related_files:
                    if related_file.is_file():
                        try:
                            content = related_file.read_text(encoding='utf-8')
                            file_has_issues = False

                            for pattern in self.security_rules["forbidden_patterns"]:
                                matches = re.finditer(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    file_has_issues = True
                                    issues.append({
                                        "type": "exposed_secret",
                                        "category": "sensitive_data",
                                        "description": f"Potential exposed secret in {related_file.name} (related to {problem_file.name})",
                                        "severity": "critical",
                                        "file": str(related_file.relative_to(project_path)),
                                        "pattern": pattern,
                                        "line_preview": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                                    })

                            self.update_file_cache(related_file, file_has_issues)

                        except Exception as e:
                            self.logger.debug(f"Could not scan related file {related_file}: {e}")

        if self.incremental:
            self.logger.info(f"📊 Incremental scan: {scanned_count} files scanned, {skipped_count} files skipped (unchanged)")

        return issues
    
    def check_env_file_security(self, project_path: Path) -> List[Dict]:
        """Check .env file security configuration"""
        issues = []
        
        env_file = project_path / ".env"
        env_example = project_path / ".env.example"
        gitignore = project_path / ".gitignore"
        
        # Check if .env exists but not in .gitignore
        if env_file.exists():
            if not gitignore.exists():
                issues.append({
                    "type": "missing_gitignore",
                    "category": "env_security",
                    "description": ".env file exists but no .gitignore found",
                    "severity": "high"
                })
            else:
                gitignore_content = gitignore.read_text()
                if ".env" not in gitignore_content:
                    issues.append({
                        "type": "env_not_ignored",
                        "category": "env_security",
                        "description": ".env file not listed in .gitignore",
                        "severity": "critical"
                    })
        
        # Check if .env.example exists for documentation
        if env_file.exists() and not env_example.exists():
            issues.append({
                "type": "missing_env_example",
                "category": "env_security",
                "description": ".env file exists but no .env.example for documentation",
                "severity": "low"
            })
        
        return issues
    
    def check_git_security(self, project_path: Path) -> List[Dict]:
        """Check git security configuration"""
        issues = []
        
        git_dir = project_path / ".git"
        if not git_dir.exists():
            return issues  # Not a git repository
        
        gitignore = project_path / ".gitignore"
        if not gitignore.exists():
            issues.append({
                "type": "missing_gitignore",
                "category": "git_security",
                "description": "Git repository missing .gitignore file",
                "severity": "medium"
            })
        else:
            # Check for common security patterns in .gitignore
            gitignore_content = gitignore.read_text()
            required_patterns = [".env", "*.log", ".DS_Store"]
            
            for pattern in required_patterns:
                if pattern not in gitignore_content:
                    issues.append({
                        "type": "missing_gitignore_pattern",
                        "category": "git_security",
                        "description": f"Missing '{pattern}' in .gitignore",
                        "severity": "low",
                        "pattern": pattern
                    })
        
        return issues
    
    def check_file_permissions(self, project_path: Path) -> List[Dict]:
        """Check file permissions for security issues"""
        issues = []
        
        # Check for overly permissive files
        sensitive_files = [".env", "config.json", "secrets.json"]
        
        for filename in sensitive_files:
            file_path = project_path / filename
            if file_path.exists():
                try:
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]  # Last 3 digits of octal permissions
                    
                    # Check if file is readable by others (world-readable)
                    if int(mode[2]) > 0:  # Others have any permissions
                        issues.append({
                            "type": "insecure_permissions",
                            "category": "file_permissions",
                            "description": f"{filename} is readable by others ({mode})",
                            "severity": "medium",
                            "file": filename,
                            "permissions": mode
                        })
                
                except Exception as e:
                    self.logger.debug(f"Could not check permissions for {file_path}: {e}")
        
        return issues
    
    def generate_security_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate security recommendations based on identified issues"""
        recommendations = []
        
        # Group issues by category
        issue_categories = {}
        for issue in issues:
            category = issue.get("category", "general")
            if category not in issue_categories:
                issue_categories[category] = []
            issue_categories[category].append(issue)
        
        # Generate category-specific recommendations
        if "sensitive_data" in issue_categories:
            recommendations.append("Move all secrets to .env file and add to .gitignore")
            recommendations.append("Consider using the vault system: python3 systems/vault-manager.py")
        
        if "env_security" in issue_categories:
            recommendations.append("Ensure .env files are properly ignored by git")
            recommendations.append("Create .env.example files for documentation")
        
        if "security_files" in issue_categories:
            recommendations.append("Generate security templates: python3 systems/secure-template-generator.py")
        
        if "git_security" in issue_categories:
            recommendations.append("Review and update .gitignore file")
            recommendations.append("Audit git history for accidentally committed secrets")
        
        if "file_permissions" in issue_categories:
            recommendations.append("Restrict file permissions on sensitive files (chmod 600)")
        
        return recommendations
    
    def check_vault_security(self) -> Dict:
        """Check vault system security status"""
        vault_status = {
            "vault_exists": self.vault_dir.exists(),
            "encrypted_files": 0,
            "last_audit": None,
            "access_frequency": 0,
            "security_issues": []
        }
        
        if not vault_status["vault_exists"]:
            vault_status["security_issues"].append({
                "type": "missing_vault",
                "description": "Vault system not initialized",
                "severity": "low"
            })
            return vault_status
        
        # Count encrypted files
        try:
            for file_path in self.vault_dir.glob("**/*.enc"):
                vault_status["encrypted_files"] += 1
        except Exception as e:
            self.logger.debug(f"Could not scan vault: {e}")
        
        # Check vault audit log
        vault_audit_log = self.vault_dir / "audit.log"
        if vault_audit_log.exists():
            try:
                with open(vault_audit_log, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Parse last audit timestamp
                        last_line = lines[-1]
                        # Extract timestamp (assuming standard format)
                        vault_status["last_audit"] = last_line.split(" - ")[0] if " - " in last_line else None
                        
                        # Count recent access
                        today = datetime.now().date()
                        for line in lines:
                            if str(today) in line:
                                vault_status["access_frequency"] += 1
            except Exception as e:
                self.logger.debug(f"Could not read vault audit log: {e}")
        
        # Check access frequency
        if vault_status["access_frequency"] > self.security_rules["vault_access_limit"]:
            vault_status["security_issues"].append({
                "type": "high_vault_access",
                "description": f"Vault accessed {vault_status['access_frequency']} times today (limit: {self.security_rules['vault_access_limit']})",
                "severity": "medium"
            })
        
        return vault_status
    
    def generate_comprehensive_security_report(self) -> Dict:
        """Generate comprehensive security report for all projects"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "overall_security_score": 0,
            "total_projects_scanned": 0,
            "critical_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "projects": {},
            "vault_status": {},
            "system_recommendations": [],
            "compliance_status": {}
        }
        
        # Track token usage for security audit
        tracker_module.track_security_audit()
        
        # Scan all projects
        scan_dirs = [
            self.base_path / "active",
            self.base_path / "staging",
            self.base_path / "archive"
        ]
        
        total_score = 0
        
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            
            for project_dir in scan_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                
                project_security = self.scan_project_security(project_dir)
                report["projects"][project_dir.name] = project_security
                report["total_projects_scanned"] += 1
                
                total_score += project_security["security_score"]
                
                # Count issues by severity
                for issue in project_security["issues"]:
                    severity = issue.get("severity", "low")
                    if severity == "critical":
                        report["critical_issues"] += 1
                    elif severity == "high":
                        report["critical_issues"] += 1
                    elif severity == "medium":
                        report["medium_issues"] += 1
                    else:
                        report["low_issues"] += 1
        
        # Calculate overall security score
        if report["total_projects_scanned"] > 0:
            report["overall_security_score"] = round(total_score / report["total_projects_scanned"], 1)
        
        # Check vault security
        report["vault_status"] = self.check_vault_security()
        
        # Generate system-wide recommendations
        report["system_recommendations"] = self.generate_system_recommendations(report)
        
        # Check compliance status
        report["compliance_status"] = self.check_compliance_status(report)
        
        # Save report
        with open(self.security_report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Save scan cache
        if self.incremental:
            self.scan_cache["last_full_scan"] = datetime.now().isoformat() if not self.incremental else self.scan_cache.get("last_full_scan")
            self.save_scan_cache()

        self.logger.info(f"Security report generated: {report['total_projects_scanned']} projects scanned, overall score: {report['overall_security_score']}")

        return report
    
    def generate_system_recommendations(self, report: Dict) -> List[str]:
        """Generate system-wide security recommendations"""
        recommendations = []
        
        if report["overall_security_score"] < 80:
            recommendations.append("Overall security score is low - prioritize security improvements")
        
        if report["critical_issues"] > 0:
            recommendations.append(f"Address {report['critical_issues']} critical security issues immediately")
        
        if not report["vault_status"]["vault_exists"]:
            recommendations.append("Initialize vault system for secure credential storage")
        
        if report["vault_status"]["encrypted_files"] == 0:
            recommendations.append("Consider using vault system to store sensitive credentials")
        
        # Token budget recommendation
        budget_status = tracker_module.check_budget()
        if budget_status["weekly"]["percentage"] > 90:
            recommendations.append("Security monitoring approaching token budget limit")
        
        return recommendations
    
    def check_compliance_status(self, report: Dict) -> Dict:
        """Check compliance with security frameworks"""
        compliance = {
            "personal_security": {"score": 0, "requirements": []},
            "data_protection": {"score": 0, "requirements": []}
        }
        
        # Personal security compliance
        personal_score = 100
        if report["critical_issues"] > 0:
            personal_score -= 50
            compliance["personal_security"]["requirements"].append("Resolve critical security issues")
        
        if report["overall_security_score"] < 80:
            personal_score -= 20
            compliance["personal_security"]["requirements"].append("Improve overall security score")
        
        if not report["vault_status"]["vault_exists"]:
            personal_score -= 15
            compliance["personal_security"]["requirements"].append("Implement vault system")
        
        compliance["personal_security"]["score"] = max(0, personal_score)
        
        # Data protection compliance
        data_score = 100
        exposed_secrets = sum(1 for project in report["projects"].values() 
                            for issue in project["issues"] 
                            if issue.get("type") == "exposed_secret")
        
        if exposed_secrets > 0:
            data_score -= 60
            compliance["data_protection"]["requirements"].append("Remove all exposed secrets from code")
        
        env_issues = sum(1 for project in report["projects"].values() 
                        for issue in project["issues"] 
                        if issue.get("category") == "env_security")
        
        if env_issues > 0:
            data_score -= 30
            compliance["data_protection"]["requirements"].append("Secure all .env files")
        
        compliance["data_protection"]["score"] = max(0, data_score)
        
        return compliance
    
    def get_security_dashboard_data(self) -> Dict:
        """Get formatted data for security dashboard display"""
        if not self.security_report_file.exists():
            self.generate_comprehensive_security_report()
        
        with open(self.security_report_file, 'r') as f:
            report = json.load(f)
        
        # Format for dashboard display
        dashboard_data = {
            "security_overview": {
                "overall_score": report["overall_security_score"],
                "status": "excellent" if report["overall_security_score"] >= 90 else
                         "good" if report["overall_security_score"] >= 70 else
                         "needs_attention",
                "total_projects": report["total_projects_scanned"],
                "last_scan": report["generated_at"]
            },
            "issue_summary": {
                "critical": report["critical_issues"],
                "medium": report["medium_issues"],
                "low": report["low_issues"],
                "total": report["critical_issues"] + report["medium_issues"] + report["low_issues"]
            },
            "vault_status": report["vault_status"],
            "top_recommendations": report["system_recommendations"][:5],
            "compliance": report["compliance_status"],
            "recent_projects": []
        }
        
        # Add top security issue projects
        project_scores = [(name, data["security_score"]) for name, data in report["projects"].items()]
        project_scores.sort(key=lambda x: x[1])  # Sort by score (lowest first)
        
        for project_name, score in project_scores[:5]:
            project_data = report["projects"][project_name]
            dashboard_data["recent_projects"].append({
                "name": project_name,
                "score": score,
                "status": "critical" if score < 50 else "warning" if score < 80 else "good",
                "issue_count": len(project_data["issues"]),
                "critical_issues": sum(1 for issue in project_data["issues"] if issue.get("severity") in ["critical", "high"])
            })
        
        return dashboard_data

def main():
    """CLI interface for security monitoring dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Monitoring Dashboard")
    parser.add_argument("--action", choices=["scan", "report", "project", "dashboard"], required=True)
    parser.add_argument("--project", help="Project name to scan")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")
    parser.add_argument("--full", action="store_true", help="Force full scan (ignore cache)")

    args = parser.parse_args()

    # Use incremental scanning by default, unless --full is specified
    dashboard = SecurityMonitoringDashboard(incremental=not args.full)
    
    try:
        if args.action == "scan":
            report = dashboard.generate_comprehensive_security_report()
            
            if args.format == "json":
                print(json.dumps(report, indent=2))
            else:
                print("🔒 Security Scan Complete:")
                print(f"  Overall Score: {report['overall_security_score']}/100")
                print(f"  Projects Scanned: {report['total_projects_scanned']}")
                print(f"  Critical Issues: {report['critical_issues']}")
                print(f"  Medium Issues: {report['medium_issues']}")
                print(f"  Low Issues: {report['low_issues']}")
                
                if report["system_recommendations"]:
                    print("\n🔧 Recommendations:")
                    for rec in report["system_recommendations"]:
                        print(f"    • {rec}")
        
        elif args.action == "report":
            if dashboard.security_report_file.exists():
                with open(dashboard.security_report_file, 'r') as f:
                    report = json.load(f)
                
                if args.format == "json":
                    print(json.dumps(report, indent=2))
                else:
                    print(f"📊 Security Report ({report['generated_at']})")
                    print(f"  Overall Security Score: {report['overall_security_score']}/100")
                    print(f"  Compliance: Personal Security {report['compliance_status']['personal_security']['score']}/100")
                    print(f"             Data Protection {report['compliance_status']['data_protection']['score']}/100")
            else:
                print("❌ No security report found. Run --action scan first.")
        
        elif args.action == "project":
            if not args.project:
                print("❌ Error: --project required for project action")
                return
            
            # Find project in different directories
            project_paths = [
                dashboard.base_path / "active" / args.project,
                dashboard.base_path / "staging" / args.project,
                dashboard.base_path / "archive" / args.project
            ]
            
            project_path = None
            for path in project_paths:
                if path.exists():
                    project_path = path
                    break
            
            if not project_path:
                print(f"❌ Project not found: {args.project}")
                return
            
            security_status = dashboard.scan_project_security(project_path)
            
            if args.format == "json":
                print(json.dumps(security_status, indent=2))
            else:
                print(f"🔒 Security Analysis: {args.project}")
                print(f"  Security Score: {security_status['security_score']}/100")
                print(f"  Issues Found: {len(security_status['issues'])}")
                
                if security_status["issues"]:
                    print("\n⚠️  Issues:")
                    for issue in security_status["issues"]:
                        severity_icon = "🚨" if issue["severity"] in ["critical", "high"] else "⚠️" if issue["severity"] == "medium" else "ℹ️"
                        print(f"    {severity_icon} {issue['description']}")
                
                if security_status["recommendations"]:
                    print("\n🔧 Recommendations:")
                    for rec in security_status["recommendations"]:
                        print(f"    • {rec}")
        
        elif args.action == "dashboard":
            dashboard_data = dashboard.get_security_dashboard_data()
            
            if args.format == "json":
                print(json.dumps(dashboard_data, indent=2))
            else:
                print("🛡️  Security Dashboard")
                print("=" * 40)
                print(f"Overall Score: {dashboard_data['security_overview']['overall_score']}/100")
                print(f"Status: {dashboard_data['security_overview']['status'].upper()}")
                print(f"Projects: {dashboard_data['security_overview']['total_projects']}")
                
                print(f"\n📊 Issues Summary:")
                print(f"  Critical: {dashboard_data['issue_summary']['critical']}")
                print(f"  Medium: {dashboard_data['issue_summary']['medium']}")
                print(f"  Low: {dashboard_data['issue_summary']['low']}")
                
                if dashboard_data["top_recommendations"]:
                    print("\n🎯 Top Recommendations:")
                    for rec in dashboard_data["top_recommendations"]:
                        print(f"  • {rec}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
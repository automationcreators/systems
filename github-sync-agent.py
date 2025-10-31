#!/usr/bin/env python3
"""
/systems/github-sync-agent.py
GitHub Sync Agent - Automatically sync all active projects to GitHub
Ensures all projects are version controlled and backed up to private GitHub repos
RELEVANT FILES: systems/daily-morning.sh, systems/backup-manager.py, systems/lifecycle-manager.py
"""

import os
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class GitHubSyncAgent:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.active_dir = self.base_path / "active"
        self.systems_dir = self.base_path / "systems"
        self.config_file = self.systems_dir / "github-sync-config.json"

        # Load configuration
        self.load_config()

        # Setup logging
        self.setup_logging()

        # GitHub CLI check
        self.gh_available = self.check_gh_cli()

    def setup_logging(self):
        """Setup logging for the GitHub sync agent"""
        log_file = self.systems_dir / "github-sync.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load or create GitHub sync configuration"""
        default_config = {
            "enabled": True,
            "auto_create_repos": True,
            "default_visibility": "private",  # private or public
            "auto_commit": True,
            "auto_push": True,
            "commit_message_template": "Auto-sync: {timestamp}",
            "exclude_projects": [
                ".DS_Store",
                ".claude"
            ],
            "exclude_patterns": [
                "*.tmp",
                "*.cache",
                "__pycache__",
                ".DS_Store",
                "node_modules",
                "*.log",
                "*.pyc",
                ".env",
                ".env.local",
                "venv",
                ".venv",
                "dist",
                "build"
            ],
            "github_username": None,  # Will be auto-detected
            "last_sync": None,
            "sync_history": []
        }

        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
        else:
            self.config = default_config

        self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available and authenticated"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.error("GitHub CLI (gh) not found. Install with: brew install gh")
            return False

    def get_github_username(self) -> Optional[str]:
        """Get GitHub username from gh CLI"""
        if not self.gh_available:
            return None

        try:
            result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                capture_output=True,
                text=True,
                check=True
            )
            username = result.stdout.strip()
            self.config["github_username"] = username
            self.save_config()
            return username
        except subprocess.CalledProcessError:
            return None

    def is_git_repo(self, project_path: Path) -> bool:
        """Check if a directory is a git repository"""
        git_dir = project_path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def init_git_repo(self, project_path: Path) -> bool:
        """Initialize a git repository"""
        try:
            subprocess.run(
                ["git", "init"],
                cwd=project_path,
                capture_output=True,
                check=True
            )

            # Create .gitignore if it doesn't exist
            gitignore_path = project_path / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, 'w') as f:
                    f.write("\n".join(self.config["exclude_patterns"]))

            self.logger.info(f"Initialized git repo: {project_path.name}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to init git repo {project_path.name}: {e}")
            return False

    def get_remote_url(self, project_path: Path) -> Optional[str]:
        """Get the GitHub remote URL for a project"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def create_github_repo(self, project_name: str, visibility: str = None) -> Tuple[bool, Optional[str]]:
        """Create a GitHub repository using gh CLI"""
        if not self.gh_available:
            return False, "GitHub CLI not available"

        if visibility is None:
            visibility = self.config["default_visibility"]

        try:
            # Check if repo already exists
            username = self.get_github_username()
            if username:
                check_result = subprocess.run(
                    ["gh", "repo", "view", f"{username}/{project_name}"],
                    capture_output=True,
                    text=True
                )
                if check_result.returncode == 0:
                    return True, f"Repository {project_name} already exists"

            # Create the repository
            cmd = [
                "gh", "repo", "create", project_name,
                f"--{visibility}",
                "--source=.",
                "--remote=origin"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            self.logger.info(f"Created GitHub repo: {project_name} ({visibility})")
            return True, result.stdout.strip()

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            self.logger.error(f"Failed to create GitHub repo {project_name}: {error_msg}")
            return False, error_msg

    def has_changes(self, project_path: Path) -> bool:
        """Check if a project has uncommitted changes"""
        try:
            # Check for staged and unstaged changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def commit_changes(self, project_path: Path, message: str = None) -> bool:
        """Commit all changes in a project"""
        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=project_path,
                capture_output=True,
                check=True
            )

            # Create commit message
            if message is None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = self.config["commit_message_template"].format(timestamp=timestamp)

            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=project_path,
                capture_output=True,
                check=True
            )

            self.logger.info(f"Committed changes: {project_path.name}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to commit {project_path.name}: {e}")
            return False

    def push_to_github(self, project_path: Path) -> bool:
        """Push commits to GitHub"""
        try:
            # Check if we have a remote
            remote_url = self.get_remote_url(project_path)
            if not remote_url:
                return False

            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()

            # Push to remote
            subprocess.run(
                ["git", "push", "-u", "origin", branch],
                cwd=project_path,
                capture_output=True,
                check=True
            )

            self.logger.info(f"Pushed to GitHub: {project_path.name}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to push {project_path.name}: {e}")
            return False

    def sync_project(self, project_path: Path) -> Dict:
        """Sync a single project to GitHub"""
        project_name = project_path.name
        result = {
            "project": project_name,
            "success": False,
            "actions": [],
            "errors": []
        }

        try:
            # Skip excluded projects
            if project_name in self.config["exclude_projects"]:
                result["skipped"] = True
                return result

            # Check if it's a git repo, initialize if not
            if not self.is_git_repo(project_path):
                if self.init_git_repo(project_path):
                    result["actions"].append("initialized_git")
                else:
                    result["errors"].append("Failed to initialize git")
                    return result

            # Check if it has a GitHub remote
            remote_url = self.get_remote_url(project_path)
            if not remote_url and self.config["auto_create_repos"]:
                # Change to project directory for gh repo create
                os.chdir(project_path)
                success, message = self.create_github_repo(project_name)
                os.chdir(self.base_path)

                if success:
                    result["actions"].append("created_github_repo")
                else:
                    result["errors"].append(f"Failed to create repo: {message}")
                    return result

            # Commit changes if any
            if self.config["auto_commit"] and self.has_changes(project_path):
                if self.commit_changes(project_path):
                    result["actions"].append("committed_changes")
                else:
                    result["errors"].append("Failed to commit changes")
                    return result

            # Push to GitHub
            if self.config["auto_push"] and remote_url:
                if self.push_to_github(project_path):
                    result["actions"].append("pushed_to_github")
                else:
                    result["errors"].append("Failed to push to GitHub")
                    return result

            result["success"] = True

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"Error syncing {project_name}: {e}")

        return result

    def sync_all_projects(self) -> Dict:
        """Sync all projects in the active directory"""
        if not self.config["enabled"]:
            self.logger.info("GitHub sync is disabled in configuration")
            return {"enabled": False}

        if not self.gh_available:
            self.logger.error("GitHub CLI not available or not authenticated")
            return {"error": "GitHub CLI not available"}

        self.logger.info("Starting GitHub sync for all active projects...")

        sync_report = {
            "timestamp": datetime.now().isoformat(),
            "total_projects": 0,
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "projects": []
        }

        # Get all project directories
        if not self.active_dir.exists():
            self.logger.error(f"Active directory not found: {self.active_dir}")
            return {"error": "Active directory not found"}

        projects = [d for d in self.active_dir.iterdir() if d.is_dir()]
        sync_report["total_projects"] = len(projects)

        # Sync each project
        for project_path in projects:
            project_name = project_path.name

            # Skip hidden directories and excluded projects
            if project_name.startswith('.') or project_name in self.config["exclude_projects"]:
                sync_report["skipped"] += 1
                continue

            self.logger.info(f"Syncing project: {project_name}")
            result = self.sync_project(project_path)

            if result.get("skipped"):
                sync_report["skipped"] += 1
            elif result["success"]:
                sync_report["synced"] += 1
            else:
                sync_report["failed"] += 1

            sync_report["projects"].append(result)

        # Update config with last sync time
        self.config["last_sync"] = sync_report["timestamp"]
        self.config["sync_history"].append({
            "timestamp": sync_report["timestamp"],
            "synced": sync_report["synced"],
            "failed": sync_report["failed"]
        })

        # Keep only last 30 sync history entries
        self.config["sync_history"] = self.config["sync_history"][-30:]
        self.save_config()

        self.logger.info(
            f"Sync completed: {sync_report['synced']} synced, "
            f"{sync_report['failed']} failed, {sync_report['skipped']} skipped"
        )

        return sync_report

    def get_sync_status(self) -> Dict:
        """Get the current sync status"""
        status = {
            "enabled": self.config["enabled"],
            "gh_cli_available": self.gh_available,
            "github_username": self.config.get("github_username"),
            "last_sync": self.config.get("last_sync"),
            "default_visibility": self.config["default_visibility"],
            "auto_commit": self.config["auto_commit"],
            "auto_push": self.config["auto_push"],
            "recent_syncs": self.config.get("sync_history", [])[-5:]
        }

        return status

    def set_visibility(self, visibility: str):
        """Set default repository visibility"""
        if visibility not in ["private", "public"]:
            raise ValueError("Visibility must be 'private' or 'public'")

        self.config["default_visibility"] = visibility
        self.save_config()
        self.logger.info(f"Default visibility set to: {visibility}")

def main():
    """CLI interface for GitHub sync agent"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Sync Agent - Sync all active projects to GitHub")
    parser.add_argument(
        "--action",
        choices=["sync", "status", "enable", "disable", "set-visibility"],
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--visibility",
        choices=["private", "public"],
        help="Set default repository visibility"
    )
    parser.add_argument(
        "--project",
        help="Sync a specific project only"
    )

    args = parser.parse_args()

    agent = GitHubSyncAgent()

    try:
        if args.action == "sync":
            if args.project:
                # Sync specific project
                project_path = agent.active_dir / args.project
                if not project_path.exists():
                    print(f"❌ Project not found: {args.project}")
                    return

                result = agent.sync_project(project_path)
                if result["success"]:
                    print(f"✅ Synced {args.project}")
                    print(f"   Actions: {', '.join(result['actions'])}")
                else:
                    print(f"❌ Failed to sync {args.project}")
                    print(f"   Errors: {', '.join(result['errors'])}")
            else:
                # Sync all projects
                report = agent.sync_all_projects()
                if "error" in report:
                    print(f"❌ {report['error']}")
                elif not report.get("enabled"):
                    print("⚠️  GitHub sync is disabled")
                else:
                    print(f"\n📊 GitHub Sync Report:")
                    print(f"   Total projects: {report['total_projects']}")
                    print(f"   ✅ Synced: {report['synced']}")
                    print(f"   ❌ Failed: {report['failed']}")
                    print(f"   ⏭️  Skipped: {report['skipped']}")

                    if report['failed'] > 0:
                        print(f"\n❌ Failed projects:")
                        for project in report['projects']:
                            if not project['success'] and not project.get('skipped'):
                                print(f"   • {project['project']}: {', '.join(project['errors'])}")

        elif args.action == "status":
            status = agent.get_sync_status()
            print(f"\n📊 GitHub Sync Status:")
            print(f"   Enabled: {'✅' if status['enabled'] else '❌'}")
            print(f"   GitHub CLI: {'✅' if status['gh_cli_available'] else '❌'}")
            print(f"   Username: {status['github_username'] or 'Not detected'}")
            print(f"   Default visibility: {status['default_visibility']}")
            print(f"   Auto-commit: {'✅' if status['auto_commit'] else '❌'}")
            print(f"   Auto-push: {'✅' if status['auto_push'] else '❌'}")
            print(f"   Last sync: {status['last_sync'] or 'Never'}")

            if status['recent_syncs']:
                print(f"\n📈 Recent syncs:")
                for sync in status['recent_syncs']:
                    timestamp = sync['timestamp'][:19]  # Truncate to readable format
                    print(f"   • {timestamp}: {sync['synced']} synced, {sync['failed']} failed")

        elif args.action == "enable":
            agent.config["enabled"] = True
            agent.save_config()
            print("✅ GitHub sync enabled")

        elif args.action == "disable":
            agent.config["enabled"] = False
            agent.save_config()
            print("⚠️  GitHub sync disabled")

        elif args.action == "set-visibility":
            if not args.visibility:
                print("❌ --visibility required (private or public)")
                return

            agent.set_visibility(args.visibility)
            print(f"✅ Default visibility set to: {args.visibility}")

    except Exception as e:
        print(f"❌ Error: {e}")
        agent.logger.error(f"CLI error: {e}")

if __name__ == "__main__":
    main()

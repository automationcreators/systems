#!/usr/bin/env python3
"""
Personal OS Backup & Versioning Manager
Handles daily backups, cloud sync, and version management
"""

import os
import json
import shutil
import logging
import subprocess
import tarfile
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

class BackupManager:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        self.backup_dir = self.systems_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Cloud storage paths (will be configured)
        self.google_drive_path = None
        self.dropbox_path = None
        
        # Backup settings
        self.config_file = self.systems_dir / "backup-config.json"
        self.load_config()
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup backup logging"""
        log_file = self.systems_dir / "backup.log"
        
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
        """Load backup configuration"""
        default_config = {
            "enabled": True,
            "schedule": {
                "daily_backup": True,
                "weekly_full_backup": True,
                "monthly_archive": True
            },
            "retention": {
                "daily_backups": 7,
                "weekly_backups": 4,
                "monthly_archives": 12
            },
            "include_paths": [
                "active",
                "staging", 
                "systems",
                ".vault",
                "Personal-OS"
            ],
            "exclude_patterns": [
                "*.tmp",
                "*.cache",
                "__pycache__",
                ".DS_Store",
                "node_modules",
                "*.log"
            ],
            "compression": {
                "enabled": True,
                "level": 6
            },
            "cloud_sync": {
                "google_drive": {
                    "enabled": False,
                    "path": None
                },
                "dropbox": {
                    "enabled": False,
                    "path": None
                },
                "github": {
                    "enabled": False,
                    "repository": None
                }
            },
            "encryption": {
                "enabled": True,
                "encrypt_cloud_backups": True
            },
            "notifications": {
                "success": True,
                "failure": True,
                "storage_warnings": True
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
        else:
            self.config = default_config
        
        self.save_config()
    
    def save_config(self):
        """Save backup configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_backup(self, backup_type="daily") -> Optional[str]:
        """Create a backup of the Personal OS"""
        if not self.config["enabled"]:
            self.logger.info("Backups disabled in configuration")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"personal-os-{backup_type}-{timestamp}"
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        
        try:
            self.logger.info(f"Starting {backup_type} backup: {backup_name}")
            
            # Create tar archive
            with tarfile.open(backup_file, "w:gz", compresslevel=self.config["compression"]["level"]) as tar:
                for include_path in self.config["include_paths"]:
                    source_path = self.base_path / include_path
                    if source_path.exists():
                        self.logger.info(f"Backing up: {include_path}")
                        tar.add(source_path, arcname=include_path, filter=self.tar_filter)
            
            # Calculate backup size and hash
            backup_size_mb = backup_file.stat().st_size / (1024 * 1024)
            backup_hash = self.calculate_file_hash(backup_file)
            
            # Create backup metadata
            metadata = {
                "name": backup_name,
                "type": backup_type,
                "created_at": datetime.now().isoformat(),
                "size_mb": round(backup_size_mb, 2),
                "hash": backup_hash,
                "included_paths": self.config["include_paths"],
                "compressed": self.config["compression"]["enabled"],
                "encrypted": False  # Will be set if encrypted
            }
            
            # Encrypt if enabled
            if self.config["encryption"]["enabled"]:
                encrypted_file = self.encrypt_backup(backup_file)
                if encrypted_file:
                    backup_file.unlink()  # Remove unencrypted version
                    backup_file = encrypted_file
                    metadata["encrypted"] = True
            
            # Save metadata
            metadata_file = self.backup_dir / f"{backup_name}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Sync to cloud if enabled
            if self.should_sync_to_cloud(backup_type):
                self.sync_to_cloud(backup_file, metadata)
            
            # Cleanup old backups
            self.cleanup_old_backups(backup_type)
            
            self.logger.info(f"Backup completed: {backup_file} ({backup_size_mb:.1f}MB)")
            
            if self.config["notifications"]["success"]:
                self.send_notification(f"Backup successful: {backup_name}", "success")
            
            return str(backup_file)
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            if backup_file.exists():
                backup_file.unlink()
            
            if self.config["notifications"]["failure"]:
                self.send_notification(f"Backup failed: {e}", "error")
            
            return None
    
    def tar_filter(self, tarinfo):
        """Filter function for tar archive to exclude unwanted files"""
        # Skip files matching exclude patterns
        for pattern in self.config["exclude_patterns"]:
            if pattern.startswith("*"):
                if tarinfo.name.endswith(pattern[1:]):
                    return None
            elif pattern in tarinfo.name:
                return None
        
        return tarinfo
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def encrypt_backup(self, backup_file: Path) -> Optional[Path]:
        """Encrypt backup file using system encryption"""
        try:
            # For macOS, we can use built-in encryption
            encrypted_file = backup_file.with_suffix(backup_file.suffix + ".enc")
            
            # Use openssl for encryption (requires password input)
            # In production, this would use the vault system for key management
            subprocess.run([
                "openssl", "enc", "-aes-256-cbc", "-salt",
                "-in", str(backup_file),
                "-out", str(encrypted_file),
                "-pass", "pass:backup_encryption_key"  # In production, use vault
            ], check=True)
            
            return encrypted_file
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Encryption failed: {e}")
            return None
    
    def should_sync_to_cloud(self, backup_type: str) -> bool:
        """Determine if backup should be synced to cloud"""
        # Sync weekly and monthly backups to cloud
        return backup_type in ["weekly", "monthly"] and any(
            self.config["cloud_sync"][provider]["enabled"] 
            for provider in self.config["cloud_sync"]
        )
    
    def sync_to_cloud(self, backup_file: Path, metadata: Dict):
        """Sync backup to configured cloud storage"""
        try:
            # Google Drive sync
            if self.config["cloud_sync"]["google_drive"]["enabled"]:
                self.sync_to_google_drive(backup_file, metadata)
            
            # Dropbox sync
            if self.config["cloud_sync"]["dropbox"]["enabled"]:
                self.sync_to_dropbox(backup_file, metadata)
            
            # GitHub sync (for code projects only)
            if self.config["cloud_sync"]["github"]["enabled"]:
                self.sync_to_github(backup_file, metadata)
                
        except Exception as e:
            self.logger.error(f"Cloud sync failed: {e}")
    
    def sync_to_google_drive(self, backup_file: Path, metadata: Dict):
        """Sync backup to Google Drive"""
        # This would use Google Drive API
        # For now, we'll use rclone if available
        drive_path = self.config["cloud_sync"]["google_drive"]["path"]
        if not drive_path:
            drive_path = "personal-os-backups"
        
        try:
            # Check if rclone is available
            result = subprocess.run(["which", "rclone"], capture_output=True)
            if result.returncode == 0:
                subprocess.run([
                    "rclone", "copy", str(backup_file), 
                    f"gdrive:{drive_path}"
                ], check=True)
                self.logger.info(f"Synced to Google Drive: {backup_file.name}")
            else:
                self.logger.warning("rclone not available for Google Drive sync")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Google Drive sync failed: {e}")
    
    def sync_to_dropbox(self, backup_file: Path, metadata: Dict):
        """Sync backup to Dropbox"""
        # Similar to Google Drive implementation
        self.logger.info("Dropbox sync not yet implemented")
    
    def sync_to_github(self, backup_file: Path, metadata: Dict):
        """Sync backup to GitHub (for code projects)"""
        # This would create a private repository for backups
        self.logger.info("GitHub sync not yet implemented")
    
    def cleanup_old_backups(self, backup_type: str):
        """Clean up old backups based on retention policy"""
        retention_days = self.config["retention"].get(f"{backup_type}_backups", 7)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Find old backup files
        pattern = f"personal-os-{backup_type}-*"
        old_backups = []
        
        for backup_file in self.backup_dir.glob(f"{pattern}.tar.gz*"):
            # Extract timestamp from filename
            try:
                timestamp_str = backup_file.stem.split("-")[-2:]  # date_time parts
                timestamp_str = "_".join(timestamp_str)
                if backup_file.suffix == ".enc":
                    timestamp_str = timestamp_str.replace(".tar.gz", "")
                
                backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if backup_date < cutoff_date:
                    old_backups.append(backup_file)
                    
            except (ValueError, IndexError):
                # Skip files with unexpected naming
                continue
        
        # Remove old backups
        for old_backup in old_backups:
            try:
                old_backup.unlink()
                
                # Also remove metadata file
                metadata_file = old_backup.with_suffix(".json")
                if metadata_file.exists():
                    metadata_file.unlink()
                
                self.logger.info(f"Removed old backup: {old_backup.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to remove old backup {old_backup}: {e}")
    
    def restore_backup(self, backup_name: str, restore_path: Path = None) -> bool:
        """Restore from a backup"""
        if not restore_path:
            restore_path = self.base_path / "restore"
        
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        encrypted_backup = self.backup_dir / f"{backup_name}.tar.gz.enc"
        
        # Check which backup file exists
        if encrypted_backup.exists():
            # Decrypt first
            try:
                subprocess.run([
                    "openssl", "enc", "-aes-256-cbc", "-d",
                    "-in", str(encrypted_backup),
                    "-out", str(backup_file),
                    "-pass", "pass:backup_encryption_key"
                ], check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Decryption failed: {e}")
                return False
        
        if not backup_file.exists():
            self.logger.error(f"Backup file not found: {backup_name}")
            return False
        
        try:
            restore_path.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(restore_path)
            
            # Clean up decrypted file if it was encrypted
            if encrypted_backup.exists() and backup_file.exists():
                backup_file.unlink()
            
            self.logger.info(f"Backup restored to: {restore_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List available backups with metadata"""
        backups = []
        
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check if backup file still exists
                backup_name = metadata["name"]
                backup_file = self.backup_dir / f"{backup_name}.tar.gz"
                encrypted_file = self.backup_dir / f"{backup_name}.tar.gz.enc"
                
                metadata["available"] = backup_file.exists() or encrypted_file.exists()
                metadata["file_path"] = str(backup_file if backup_file.exists() else encrypted_file)
                
                backups.append(metadata)
                
            except Exception as e:
                self.logger.error(f"Could not read backup metadata {metadata_file}: {e}")
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    def get_backup_status(self) -> Dict:
        """Get backup system status"""
        backups = self.list_backups()
        
        # Calculate total backup size
        total_size = sum(backup["size_mb"] for backup in backups if backup["available"])
        
        # Check last backup time
        last_backup = None
        if backups:
            last_backup = backups[0]["created_at"]
        
        # Check if backup is overdue
        overdue = False
        if last_backup:
            last_backup_date = datetime.fromisoformat(last_backup)
            if datetime.now() - last_backup_date > timedelta(days=2):
                overdue = True
        
        status = {
            "enabled": self.config["enabled"],
            "total_backups": len(backups),
            "total_size_mb": round(total_size, 2),
            "last_backup": last_backup,
            "overdue": overdue,
            "cloud_sync_enabled": any(
                self.config["cloud_sync"][provider]["enabled"] 
                for provider in self.config["cloud_sync"]
            ),
            "encryption_enabled": self.config["encryption"]["enabled"]
        }
        
        return status
    
    def send_notification(self, message: str, notification_type: str):
        """Send backup notification"""
        # For now, just log the notification
        # In production, this would send email, Slack, or dashboard notifications
        if notification_type == "error":
            self.logger.error(f"NOTIFICATION: {message}")
        else:
            self.logger.info(f"NOTIFICATION: {message}")

def main():
    """CLI interface for backup management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Personal OS Backup & Versioning Manager")
    parser.add_argument("--action", choices=["backup", "restore", "list", "status", "cleanup"], required=True)
    parser.add_argument("--type", choices=["daily", "weekly", "monthly"], default="daily")
    parser.add_argument("--name", help="Backup name for restore")
    parser.add_argument("--restore-path", help="Path to restore backup to")
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    try:
        if args.action == "backup":
            backup_file = manager.create_backup(args.type)
            if backup_file:
                print(f"✅ Backup created: {backup_file}")
            else:
                print("❌ Backup failed")
        
        elif args.action == "restore":
            if not args.name:
                print("Error: --name required for restore action")
                return
            
            restore_path = Path(args.restore_path) if args.restore_path else None
            success = manager.restore_backup(args.name, restore_path)
            
            if success:
                print(f"✅ Backup restored")
            else:
                print("❌ Restore failed")
        
        elif args.action == "list":
            backups = manager.list_backups()
            print(f"\n💾 Available Backups ({len(backups)}):")
            for backup in backups:
                status = "✅" if backup["available"] else "❌"
                encrypted = "🔒" if backup["encrypted"] else "🔓"
                print(f"  {status} {encrypted} {backup['name']} - {backup['type']} - {backup['size_mb']}MB - {backup['created_at'][:10]}")
        
        elif args.action == "status":
            status = manager.get_backup_status()
            print(f"\n📊 Backup Status:")
            print(f"  Enabled: {'✅' if status['enabled'] else '❌'}")
            print(f"  Total backups: {status['total_backups']}")
            print(f"  Total size: {status['total_size_mb']} MB")
            print(f"  Last backup: {status['last_backup'] or 'Never'}")
            print(f"  Overdue: {'⚠️ Yes' if status['overdue'] else '✅ No'}")
            print(f"  Cloud sync: {'✅' if status['cloud_sync_enabled'] else '❌'}")
            print(f"  Encryption: {'🔒' if status['encryption_enabled'] else '🔓'}")
        
        elif args.action == "cleanup":
            for backup_type in ["daily", "weekly", "monthly"]:
                manager.cleanup_old_backups(backup_type)
            print("✅ Cleanup completed")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
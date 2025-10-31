#!/usr/bin/env python3
"""
Personal OS Storage Monitor & Cleanup Automation
Monitors storage usage, performs deduplication, compression, and cleanup
"""

import os
import json
import shutil
import hashlib
import gzip
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import tempfile

class StorageMonitor:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        self.archive_dir = self.base_path / "archive"
        
        # Storage thresholds (in GB)
        self.warning_threshold = 100  # Warn when less than 100GB free
        self.critical_threshold = 50  # Critical when less than 50GB free
        
        # File size thresholds (in MB)
        self.large_file_threshold = 100
        self.duplicate_scan_min_size = 1  # MB
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config_file = self.systems_dir / "storage-config.json"
        self.load_config()
        
        # Results storage
        self.scan_results_file = self.systems_dir / "storage-scan-results.json"
    
    def setup_logging(self):
        """Setup storage monitoring logging"""
        log_file = self.systems_dir / "storage-monitor.log"
        
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
        """Load storage monitoring configuration"""
        default_config = {
            "excluded_extensions": [".tmp", ".cache", ".log", ".pyc", "__pycache__"],
            "excluded_directories": [".git", ".DS_Store", "node_modules", ".venv", "__pycache__"],
            "compress_extensions": [".txt", ".md", ".json", ".csv", ".xml", ".log"],
            "auto_cleanup_enabled": True,
            "backup_before_cleanup": True,
            "duplicate_scan_enabled": True,
            "compression_enabled": True,
            "storage_alerts": {
                "email": None,
                "slack": None,
                "dashboard": True
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
        """Save storage monitoring configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_storage_info(self) -> Dict:
        """Get current storage information"""
        try:
            # Get disk usage
            usage = shutil.disk_usage(self.base_path)
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            
            # Get directory sizes
            directory_sizes = {}
            for directory in [self.base_path / "active", self.base_path / "staging", 
                             self.archive_dir, self.systems_dir]:
                if directory.exists():
                    directory_sizes[directory.name] = self.get_directory_size(directory)
            
            # Calculate Personal OS usage
            personal_os_size = sum(directory_sizes.values())
            
            storage_info = {
                "timestamp": datetime.now().isoformat(),
                "disk": {
                    "total_gb": round(total_gb, 2),
                    "used_gb": round(used_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "usage_percentage": round((used_gb / total_gb) * 100, 1)
                },
                "personal_os": {
                    "total_mb": round(personal_os_size, 2),
                    "by_directory": directory_sizes
                },
                "status": self.get_storage_status(free_gb),
                "recommendations": self.get_storage_recommendations(free_gb, personal_os_size)
            }
            
            return storage_info
            
        except Exception as e:
            self.logger.error(f"Error getting storage info: {e}")
            return {"error": str(e)}
    
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
    
    def get_storage_status(self, free_gb: float) -> str:
        """Determine storage status based on free space"""
        if free_gb < self.critical_threshold:
            return "critical"
        elif free_gb < self.warning_threshold:
            return "warning"
        else:
            return "healthy"
    
    def get_storage_recommendations(self, free_gb: float, personal_os_size_mb: float) -> List[str]:
        """Generate storage recommendations"""
        recommendations = []
        
        if free_gb < self.critical_threshold:
            recommendations.append("URGENT: Less than 50GB free space. Run cleanup immediately.")
            recommendations.append("Consider moving archived projects to cloud storage.")
        
        elif free_gb < self.warning_threshold:
            recommendations.append("Warning: Less than 100GB free space. Consider cleanup.")
        
        if personal_os_size_mb > 10000:  # 10GB
            recommendations.append("Personal OS using >10GB. Run duplicate scan and compression.")
        
        return recommendations
    
    def scan_for_duplicates(self, scan_paths: List[Path] = None) -> Dict:
        """Scan for duplicate files"""
        if not scan_paths:
            scan_paths = [self.base_path / "active", self.base_path / "staging", self.archive_dir]
        
        self.logger.info("Starting duplicate scan...")
        file_hashes = defaultdict(list)
        total_files = 0
        total_size = 0
        
        for scan_path in scan_paths:
            if not scan_path.exists():
                continue
                
            for file_path in scan_path.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # Skip small files and excluded types
                file_size = file_path.stat().st_size
                if file_size < self.duplicate_scan_min_size * 1024 * 1024:  # Convert MB to bytes
                    continue
                
                if any(file_path.name.endswith(ext) for ext in self.config["excluded_extensions"]):
                    continue
                
                if any(excluded in str(file_path) for excluded in self.config["excluded_directories"]):
                    continue
                
                # Calculate file hash
                try:
                    file_hash = self.calculate_file_hash(file_path)
                    file_hashes[file_hash].append({
                        "path": str(file_path),
                        "size": file_size,
                        "modified": file_path.stat().st_mtime
                    })
                    total_files += 1
                    total_size += file_size
                    
                except Exception as e:
                    self.logger.warning(f"Could not hash file {file_path}: {e}")
        
        # Find actual duplicates
        duplicates = {hash_val: files for hash_val, files in file_hashes.items() if len(files) > 1}
        
        # Calculate savings potential
        potential_savings = 0
        duplicate_groups = []
        
        for hash_val, files in duplicates.items():
            # Sort by modification time (keep newest)
            files.sort(key=lambda x: x["modified"], reverse=True)
            
            # Calculate savings (size of all but newest file)
            group_savings = sum(file["size"] for file in files[1:])
            potential_savings += group_savings
            
            duplicate_groups.append({
                "hash": hash_val,
                "files": files,
                "count": len(files),
                "size_mb": round(files[0]["size"] / (1024 * 1024), 2),
                "savings_mb": round(group_savings / (1024 * 1024), 2),
                "keep_file": files[0]["path"],
                "remove_files": [f["path"] for f in files[1:]]
            })
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "scanned_files": total_files,
            "scanned_size_mb": round(total_size / (1024 * 1024), 2),
            "duplicate_groups": len(duplicate_groups),
            "total_duplicates": sum(group["count"] - 1 for group in duplicate_groups),
            "potential_savings_mb": round(potential_savings / (1024 * 1024), 2),
            "groups": duplicate_groups
        }
        
        self.logger.info(f"Duplicate scan complete: {results['duplicate_groups']} groups, {results['potential_savings_mb']}MB potential savings")
        return results
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def remove_duplicates(self, duplicate_results: Dict, auto_remove: bool = False) -> Dict:
        """Remove duplicate files"""
        removed_count = 0
        saved_space = 0
        errors = []
        
        for group in duplicate_results["groups"]:
            if not auto_remove:
                print(f"\nDuplicate group ({group['count']} files, {group['size_mb']}MB each):")
                print(f"  Keep: {group['keep_file']}")
                for remove_file in group['remove_files']:
                    print(f"  Remove: {remove_file}")
                
                response = input("Remove duplicates from this group? (y/n/q): ").lower().strip()
                if response == 'q':
                    break
                elif response != 'y':
                    continue
            
            # Remove duplicate files
            for remove_file in group['remove_files']:
                try:
                    file_path = Path(remove_file)
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        removed_count += 1
                        saved_space += file_size
                        self.logger.info(f"Removed duplicate: {remove_file}")
                        
                except Exception as e:
                    error_msg = f"Failed to remove {remove_file}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
        
        return {
            "removed_files": removed_count,
            "saved_space_mb": round(saved_space / (1024 * 1024), 2),
            "errors": errors
        }
    
    def compress_files(self, compress_paths: List[Path] = None) -> Dict:
        """Compress eligible files to save space"""
        if not compress_paths:
            compress_paths = [self.archive_dir]
        
        compressed_count = 0
        saved_space = 0
        errors = []
        
        for compress_path in compress_paths:
            if not compress_path.exists():
                continue
            
            for file_path in compress_path.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # Check if file should be compressed
                if not any(file_path.name.endswith(ext) for ext in self.config["compress_extensions"]):
                    continue
                
                if file_path.name.endswith('.gz'):
                    continue  # Already compressed
                
                # Check file size (only compress files > 1MB)
                file_size = file_path.stat().st_size
                if file_size < 1024 * 1024:
                    continue
                
                try:
                    # Compress file
                    compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
                    
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Verify compression was beneficial
                    compressed_size = compressed_path.stat().st_size
                    if compressed_size < file_size * 0.9:  # At least 10% savings
                        file_path.unlink()  # Remove original
                        compressed_count += 1
                        saved_space += (file_size - compressed_size)
                        self.logger.info(f"Compressed: {file_path} (saved {round((file_size - compressed_size) / 1024 / 1024, 2)}MB)")
                    else:
                        compressed_path.unlink()  # Remove compressed version, keep original
                        
                except Exception as e:
                    error_msg = f"Failed to compress {file_path}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
        
        return {
            "compressed_files": compressed_count,
            "saved_space_mb": round(saved_space / (1024 * 1024), 2),
            "errors": errors
        }
    
    def find_large_files(self, scan_paths: List[Path] = None, min_size_mb: int = None) -> List[Dict]:
        """Find large files that might need attention"""
        if not scan_paths:
            scan_paths = [self.base_path / "active", self.base_path / "staging", self.archive_dir]
        
        if not min_size_mb:
            min_size_mb = self.large_file_threshold
        
        large_files = []
        
        for scan_path in scan_paths:
            if not scan_path.exists():
                continue
            
            for file_path in scan_path.rglob('*'):
                if not file_path.is_file():
                    continue
                
                file_size = file_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                
                if size_mb >= min_size_mb:
                    large_files.append({
                        "path": str(file_path),
                        "size_mb": round(size_mb, 2),
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "extension": file_path.suffix.lower()
                    })
        
        # Sort by size (largest first)
        large_files.sort(key=lambda x: x["size_mb"], reverse=True)
        
        return large_files
    
    def cleanup_temp_files(self) -> Dict:
        """Clean up temporary and cache files"""
        cleaned_count = 0
        saved_space = 0
        errors = []
        
        # Common temp/cache patterns
        temp_patterns = [
            "*.tmp", "*.temp", "*.cache", "*.log",
            "*~", ".DS_Store", "Thumbs.db", "*.pyc"
        ]
        
        temp_directories = [
            ".cache", "__pycache__", ".pytest_cache",
            "node_modules/.cache", ".npm"
        ]
        
        for scan_path in [self.base_path / "active", self.base_path / "staging"]:
            if not scan_path.exists():
                continue
            
            # Clean temp files
            for pattern in temp_patterns:
                for file_path in scan_path.rglob(pattern):
                    try:
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleaned_count += 1
                            saved_space += file_size
                            
                    except Exception as e:
                        errors.append(f"Failed to remove {file_path}: {e}")
            
            # Clean temp directories
            for temp_dir in temp_directories:
                for dir_path in scan_path.rglob(temp_dir):
                    try:
                        if dir_path.is_dir():
                            dir_size = self.get_directory_size(dir_path)
                            shutil.rmtree(dir_path)
                            saved_space += dir_size * 1024 * 1024  # Convert MB to bytes
                            
                    except Exception as e:
                        errors.append(f"Failed to remove directory {dir_path}: {e}")
        
        return {
            "cleaned_files": cleaned_count,
            "saved_space_mb": round(saved_space / (1024 * 1024), 2),
            "errors": errors
        }
    
    def run_full_storage_audit(self) -> Dict:
        """Run comprehensive storage audit"""
        self.logger.info("Starting full storage audit...")
        
        audit_results = {
            "timestamp": datetime.now().isoformat(),
            "storage_info": self.get_storage_info(),
            "duplicate_scan": self.scan_for_duplicates(),
            "large_files": self.find_large_files(),
            "recommendations": []
        }
        
        # Generate recommendations based on findings
        recommendations = []
        
        if audit_results["duplicate_scan"]["potential_savings_mb"] > 100:
            recommendations.append("High duplicate savings potential. Run deduplication.")
        
        if len(audit_results["large_files"]) > 10:
            recommendations.append("Many large files found. Review for archival or compression.")
        
        if audit_results["storage_info"]["status"] in ["warning", "critical"]:
            recommendations.append("Low storage space. Run cleanup immediately.")
        
        audit_results["recommendations"] = recommendations
        
        # Save results
        with open(self.scan_results_file, 'w') as f:
            json.dump(audit_results, f, indent=2)
        
        self.logger.info("Storage audit complete")
        return audit_results

def main():
    """CLI interface for storage monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Personal OS Storage Monitor & Cleanup")
    parser.add_argument("--action", choices=["status", "audit", "duplicates", "compress", "cleanup", "large-files"], required=True)
    parser.add_argument("--auto", action="store_true", help="Auto-execute safe operations")
    parser.add_argument("--min-size", type=int, default=100, help="Minimum file size for large file scan (MB)")
    
    args = parser.parse_args()
    
    monitor = StorageMonitor()
    
    try:
        if args.action == "status":
            info = monitor.get_storage_info()
            print(f"\n💾 Storage Status: {info['status'].upper()}")
            print(f"  Free space: {info['disk']['free_gb']} GB ({100 - info['disk']['usage_percentage']:.1f}% free)")
            print(f"  Personal OS size: {info['personal_os']['total_mb']} MB")
            print(f"  By directory: {info['personal_os']['by_directory']}")
            
            if info["recommendations"]:
                print(f"\n💡 Recommendations:")
                for rec in info["recommendations"]:
                    print(f"  • {rec}")
        
        elif args.action == "audit":
            results = monitor.run_full_storage_audit()
            print(f"\n🔍 Storage Audit Complete:")
            print(f"  Status: {results['storage_info']['status']}")
            print(f"  Duplicate groups: {results['duplicate_scan']['duplicate_groups']}")
            print(f"  Potential savings: {results['duplicate_scan']['potential_savings_mb']} MB")
            print(f"  Large files: {len(results['large_files'])}")
            
            if results["recommendations"]:
                print(f"\n💡 Recommendations:")
                for rec in results["recommendations"]:
                    print(f"  • {rec}")
        
        elif args.action == "duplicates":
            duplicates = monitor.scan_for_duplicates()
            print(f"\n🔍 Duplicate Scan Results:")
            print(f"  Groups found: {duplicates['duplicate_groups']}")
            print(f"  Potential savings: {duplicates['potential_savings_mb']} MB")
            
            if duplicates['duplicate_groups'] > 0:
                removal_results = monitor.remove_duplicates(duplicates, args.auto)
                print(f"  Removed: {removal_results['removed_files']} files")
                print(f"  Space saved: {removal_results['saved_space_mb']} MB")
        
        elif args.action == "compress":
            results = monitor.compress_files()
            print(f"\n🗜️ Compression Results:")
            print(f"  Files compressed: {results['compressed_files']}")
            print(f"  Space saved: {results['saved_space_mb']} MB")
        
        elif args.action == "cleanup":
            results = monitor.cleanup_temp_files()
            print(f"\n🧹 Cleanup Results:")
            print(f"  Files removed: {results['cleaned_files']}")
            print(f"  Space freed: {results['saved_space_mb']} MB")
        
        elif args.action == "large-files":
            large_files = monitor.find_large_files(min_size_mb=args.min_size)
            print(f"\n📁 Large Files (>{args.min_size}MB):")
            for file_info in large_files[:20]:  # Show top 20
                print(f"  • {file_info['size_mb']}MB - {file_info['path']}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Template Lineage Manager
Enhanced tracking and management of template generation and inheritance
Provides analytics, version tracking, and template evolution insights
"""

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

class TemplateLineageManager:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        
        # Lineage tracking files
        self.lineage_file = self.systems_dir / "template-lineage.json"
        self.evolution_file = self.systems_dir / "template-evolution.json"
        self.analytics_file = self.systems_dir / "template-analytics.json"
        
        # Load existing data
        self.load_lineage_data()
        self.load_evolution_data()
        
        # Setup logging
        self.setup_logging()
        
        self.logger.info("Template Lineage Manager initialized")
    
    def setup_logging(self):
        """Setup lineage tracking logging"""
        log_file = self.systems_dir / "template-lineage.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_lineage_data(self):
        """Load template lineage data"""
        if self.lineage_file.exists():
            with open(self.lineage_file, 'r') as f:
                self.lineage = json.load(f)
        else:
            self.lineage = {
                "templates": {},
                "generated_files": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def load_evolution_data(self):
        """Load template evolution tracking"""
        if self.evolution_file.exists():
            with open(self.evolution_file, 'r') as f:
                self.evolution = json.load(f)
        else:
            self.evolution = {
                "versions": {},
                "changes": [],
                "template_families": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def save_lineage_data(self):
        """Save lineage data"""
        self.lineage["last_updated"] = datetime.now().isoformat()
        with open(self.lineage_file, 'w') as f:
            json.dump(self.lineage, f, indent=2)
    
    def save_evolution_data(self):
        """Save evolution data"""
        self.evolution["last_updated"] = datetime.now().isoformat()
        with open(self.evolution_file, 'w') as f:
            json.dump(self.evolution, f, indent=2)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file for change detection"""
        if not file_path.exists():
            return ""
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""
    
    def track_template_generation(self, project_path: Path, project_type: str, 
                                 generated_files: List[str], templates_used: List[str],
                                 generator_version: str = "1.0.0") -> str:
        """Track a new template generation event"""
        
        # Create unique generation ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        generation_id = f"{project_path.name}_{timestamp}"
        
        # Calculate file hashes for generated files
        file_hashes = {}
        for file_path_str in generated_files:
            file_path = Path(file_path_str)
            if file_path.exists():
                file_hashes[file_path_str] = self.calculate_file_hash(file_path)
        
        # Track generation event
        generation_record = {
            "project_path": str(project_path),
            "project_type": project_type,
            "generated_at": datetime.now().isoformat(),
            "files": generated_files,
            "templates": templates_used,
            "generator_version": generator_version,
            "file_hashes": file_hashes,
            "parent_generation": None  # For template inheritance tracking
        }
        
        # Check if this is an update to existing templates
        existing_generations = self.find_existing_generations(project_path)
        if existing_generations:
            latest_generation = max(existing_generations, key=lambda x: x["generated_at"])
            generation_record["parent_generation"] = latest_generation["id"]
            self.track_template_evolution(generation_id, latest_generation["id"], generation_record)
        
        self.lineage["generated_files"][generation_id] = generation_record
        self.save_lineage_data()
        
        # Track token usage for lineage tracking
        tracker_module.track_operation("template_lineage_tracking", 5)
        
        self.logger.info(f"Tracked template generation: {generation_id}")
        
        return generation_id
    
    def find_existing_generations(self, project_path: Path) -> List[Dict]:
        """Find existing template generations for a project"""
        project_path_str = str(project_path)
        existing = []
        
        for gen_id, gen_data in self.lineage["generated_files"].items():
            if gen_data["project_path"] == project_path_str:
                gen_data["id"] = gen_id
                existing.append(gen_data)
        
        return existing
    
    def track_template_evolution(self, new_generation_id: str, parent_generation_id: str, new_generation: Dict):
        """Track changes between template generations"""
        if parent_generation_id not in self.lineage["generated_files"]:
            return
        
        parent_generation = self.lineage["generated_files"][parent_generation_id]
        
        # Analyze changes
        changes = {
            "generation_id": new_generation_id,
            "parent_id": parent_generation_id,
            "changed_at": datetime.now().isoformat(),
            "changes": []
        }
        
        # Check for new files
        parent_files = set(parent_generation.get("files", []))
        new_files = set(new_generation.get("files", []))
        
        added_files = new_files - parent_files
        removed_files = parent_files - new_files
        
        if added_files:
            changes["changes"].append({
                "type": "files_added",
                "details": list(added_files)
            })
        
        if removed_files:
            changes["changes"].append({
                "type": "files_removed", 
                "details": list(removed_files)
            })
        
        # Check for template changes
        parent_templates = set(parent_generation.get("templates", []))
        new_templates = set(new_generation.get("templates", []))
        
        if parent_templates != new_templates:
            changes["changes"].append({
                "type": "templates_changed",
                "added": list(new_templates - parent_templates),
                "removed": list(parent_templates - new_templates)
            })
        
        # Check for file content changes using hashes
        parent_hashes = parent_generation.get("file_hashes", {})
        new_hashes = new_generation.get("file_hashes", {})
        
        modified_files = []
        for file_path, new_hash in new_hashes.items():
            if file_path in parent_hashes and parent_hashes[file_path] != new_hash:
                modified_files.append(file_path)
        
        if modified_files:
            changes["changes"].append({
                "type": "files_modified",
                "details": modified_files
            })
        
        # Check for project type changes
        if parent_generation.get("project_type") != new_generation.get("project_type"):
            changes["changes"].append({
                "type": "project_type_changed",
                "from": parent_generation.get("project_type"),
                "to": new_generation.get("project_type")
            })
        
        if changes["changes"]:
            self.evolution["changes"].append(changes)
            self.save_evolution_data()
            self.logger.info(f"Tracked {len(changes['changes'])} template changes for {new_generation_id}")
    
    def get_project_template_history(self, project_path: Path) -> Dict:
        """Get complete template history for a project"""
        project_generations = self.find_existing_generations(project_path)
        
        if not project_generations:
            return {"error": "No template generations found for project"}
        
        # Sort by generation time
        project_generations.sort(key=lambda x: x["generated_at"])
        
        history = {
            "project_path": str(project_path),
            "total_generations": len(project_generations),
            "first_generation": project_generations[0]["generated_at"],
            "latest_generation": project_generations[-1]["generated_at"],
            "generations": project_generations,
            "evolution_summary": []
        }
        
        # Add evolution summary
        for change in self.evolution.get("changes", []):
            if any(gen["id"] == change.get("generation_id") for gen in project_generations):
                history["evolution_summary"].append({
                    "date": change["changed_at"],
                    "changes": len(change["changes"]),
                    "details": change["changes"]
                })
        
        return history
    
    def get_template_family_analytics(self) -> Dict:
        """Get analytics on template families and usage patterns"""
        analytics = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_generations": len(self.lineage["generated_files"]),
                "unique_projects": len(set(gen["project_path"] for gen in self.lineage["generated_files"].values())),
                "template_types": {},
                "project_types": {},
                "generator_versions": {}
            },
            "usage_patterns": {},
            "evolution_trends": {},
            "recommendations": []
        }
        
        # Analyze template usage
        for generation in self.lineage["generated_files"].values():
            # Count project types
            project_type = generation.get("project_type", "unknown")
            analytics["summary"]["project_types"][project_type] = analytics["summary"]["project_types"].get(project_type, 0) + 1
            
            # Count template types
            for template in generation.get("templates", []):
                analytics["summary"]["template_types"][template] = analytics["summary"]["template_types"].get(template, 0) + 1
            
            # Count generator versions
            version = generation.get("generator_version", "unknown")
            analytics["summary"]["generator_versions"][version] = analytics["summary"]["generator_versions"].get(version, 0) + 1
        
        # Analyze usage patterns
        analytics["usage_patterns"] = self.analyze_usage_patterns()
        
        # Generate recommendations
        analytics["recommendations"] = self.generate_lineage_recommendations(analytics)
        
        # Save analytics
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        return analytics
    
    def analyze_usage_patterns(self) -> Dict:
        """Analyze template usage patterns"""
        patterns = {
            "most_common_combinations": {},
            "project_type_preferences": {},
            "generation_frequency": {},
            "file_popularity": {}
        }
        
        # Analyze template combinations
        for generation in self.lineage["generated_files"].values():
            templates = sorted(generation.get("templates", []))
            combination = "_".join(templates)
            
            patterns["most_common_combinations"][combination] = patterns["most_common_combinations"].get(combination, 0) + 1
        
        # Analyze file types generated
        for generation in self.lineage["generated_files"].values():
            for file_path in generation.get("files", []):
                file_name = Path(file_path).name
                patterns["file_popularity"][file_name] = patterns["file_popularity"].get(file_name, 0) + 1
        
        # Analyze generation frequency by project type
        for generation in self.lineage["generated_files"].values():
            project_type = generation.get("project_type", "unknown")
            if project_type not in patterns["generation_frequency"]:
                patterns["generation_frequency"][project_type] = []
            patterns["generation_frequency"][project_type].append(generation["generated_at"])
        
        return patterns
    
    def generate_lineage_recommendations(self, analytics: Dict) -> List[str]:
        """Generate recommendations based on lineage analytics"""
        recommendations = []
        
        # Check for missing template types
        common_templates = ["env_template", "gitignore_template", "security_md_template"]
        template_usage = analytics["summary"]["template_types"]
        
        for template in common_templates:
            usage_count = template_usage.get(template, 0)
            if usage_count < analytics["summary"]["total_generations"] * 0.8:
                recommendations.append(f"Consider standardizing {template} across all projects")
        
        # Check project type distribution
        project_types = analytics["summary"]["project_types"]
        if len(project_types) > 1:
            most_common_type = max(project_types.items(), key=lambda x: x[1])
            if most_common_type[1] > analytics["summary"]["total_generations"] * 0.5:
                recommendations.append(f"Consider creating specialized templates for {most_common_type[0]} projects")
        
        # Check for outdated generator versions
        versions = analytics["summary"]["generator_versions"]
        if len(versions) > 1:
            recommendations.append("Multiple generator versions detected - consider updating older projects")
        
        # Token usage recommendation
        budget_status = tracker_module.check_budget()
        if budget_status["weekly"]["percentage"] > 80:
            recommendations.append("Template lineage tracking approaching token budget limit")
        
        return recommendations
    
    def get_template_inheritance_tree(self, project_path: Path) -> Dict:
        """Get inheritance tree showing template evolution for a project"""
        generations = self.find_existing_generations(project_path)
        
        if not generations:
            return {"error": "No generations found for project"}
        
        # Build inheritance tree
        tree = {
            "project_path": str(project_path),
            "root_generation": None,
            "generations": {},
            "inheritance_chain": []
        }
        
        # Index generations by ID
        gen_lookup = {}
        for gen in generations:
            gen_id = f"{project_path.name}_{gen['generated_at'].replace(':', '').replace('-', '').split('.')[0]}"
            gen["id"] = gen_id
            gen_lookup[gen_id] = gen
            tree["generations"][gen_id] = gen
        
        # Build inheritance chain
        for gen_id, gen_data in tree["generations"].items():
            parent_id = gen_data.get("parent_generation")
            
            if not parent_id:
                tree["root_generation"] = gen_id
                tree["inheritance_chain"].append({
                    "generation_id": gen_id,
                    "level": 0,
                    "parent": None,
                    "generated_at": gen_data["generated_at"]
                })
            else:
                # Find the parent's level and add 1
                parent_level = 0
                for item in tree["inheritance_chain"]:
                    if item["generation_id"] == parent_id:
                        parent_level = item["level"]
                        break
                
                tree["inheritance_chain"].append({
                    "generation_id": gen_id,
                    "level": parent_level + 1,
                    "parent": parent_id,
                    "generated_at": gen_data["generated_at"]
                })
        
        # Sort inheritance chain by level and time
        tree["inheritance_chain"].sort(key=lambda x: (x["level"], x["generated_at"]))
        
        return tree
    
    def detect_template_drift(self) -> Dict:
        """Detect projects where templates may have drifted from standards"""
        drift_report = {
            "checked_at": datetime.now().isoformat(),
            "projects_with_drift": [],
            "common_drift_patterns": {},
            "recommendations": []
        }
        
        # Find projects with multiple generations
        projects_with_history = {}
        for gen_data in self.lineage["generated_files"].values():
            project_path = gen_data["project_path"]
            if project_path not in projects_with_history:
                projects_with_history[project_path] = []
            projects_with_history[project_path].append(gen_data)
        
        # Check each project for drift
        for project_path, generations in projects_with_history.items():
            if len(generations) > 1:
                # Sort by generation time
                generations.sort(key=lambda x: x["generated_at"])
                
                # Compare first and latest generation
                first_gen = generations[0]
                latest_gen = generations[-1]
                
                drift_issues = []
                
                # Check for file differences
                first_files = set(Path(f).name for f in first_gen.get("files", []))
                latest_files = set(Path(f).name for f in latest_gen.get("files", []))
                
                if first_files != latest_files:
                    drift_issues.append({
                        "type": "file_structure_drift",
                        "description": "File structure changed between generations",
                        "details": {
                            "added": list(latest_files - first_files),
                            "removed": list(first_files - latest_files)
                        }
                    })
                
                # Check for template differences
                first_templates = set(first_gen.get("templates", []))
                latest_templates = set(latest_gen.get("templates", []))
                
                if first_templates != latest_templates:
                    drift_issues.append({
                        "type": "template_drift",
                        "description": "Template usage changed between generations",
                        "details": {
                            "added": list(latest_templates - first_templates),
                            "removed": list(first_templates - latest_templates)
                        }
                    })
                
                if drift_issues:
                    drift_report["projects_with_drift"].append({
                        "project_path": project_path,
                        "generations_count": len(generations),
                        "first_generation": first_gen["generated_at"],
                        "latest_generation": latest_gen["generated_at"],
                        "drift_issues": drift_issues
                    })
        
        # Generate recommendations based on drift patterns
        if drift_report["projects_with_drift"]:
            drift_report["recommendations"].append(f"Review {len(drift_report['projects_with_drift'])} projects with template drift")
            
            common_drifts = {}
            for project in drift_report["projects_with_drift"]:
                for issue in project["drift_issues"]:
                    issue_type = issue["type"]
                    common_drifts[issue_type] = common_drifts.get(issue_type, 0) + 1
            
            drift_report["common_drift_patterns"] = common_drifts
            
            if common_drifts.get("file_structure_drift", 0) > 2:
                drift_report["recommendations"].append("Consider standardizing file structure across projects")
            
            if common_drifts.get("template_drift", 0) > 2:
                drift_report["recommendations"].append("Review template selection rules for consistency")
        
        return drift_report
    
    def clean_stale_lineage_data(self, retention_days: int = 365):
        """Clean up old lineage data beyond retention period"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_iso = cutoff_date.isoformat()
        
        cleaned = {
            "generations_removed": 0,
            "changes_removed": 0,
            "cutoff_date": cutoff_iso
        }
        
        # Clean old generations
        original_gen_count = len(self.lineage["generated_files"])
        self.lineage["generated_files"] = {
            gen_id: gen_data for gen_id, gen_data in self.lineage["generated_files"].items()
            if gen_data.get("generated_at", "") >= cutoff_iso
        }
        cleaned["generations_removed"] = original_gen_count - len(self.lineage["generated_files"])
        
        # Clean old evolution changes
        original_change_count = len(self.evolution.get("changes", []))
        self.evolution["changes"] = [
            change for change in self.evolution.get("changes", [])
            if change.get("changed_at", "") >= cutoff_iso
        ]
        cleaned["changes_removed"] = original_change_count - len(self.evolution["changes"])
        
        if cleaned["generations_removed"] > 0 or cleaned["changes_removed"] > 0:
            self.save_lineage_data()
            self.save_evolution_data()
            self.logger.info(f"Cleaned {cleaned['generations_removed']} old generations and {cleaned['changes_removed']} old changes")
        
        return cleaned

def main():
    """CLI interface for template lineage manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Template Lineage Manager")
    parser.add_argument("--action", choices=["analytics", "history", "drift", "clean"], required=True)
    parser.add_argument("--project", help="Project path for history command")
    parser.add_argument("--retention-days", type=int, default=365, help="Retention period for cleanup")
    
    args = parser.parse_args()
    
    manager = TemplateLineageManager()
    
    try:
        if args.action == "analytics":
            analytics = manager.get_template_family_analytics()
            
            print("📊 Template Lineage Analytics:")
            print(f"  Total Generations: {analytics['summary']['total_generations']}")
            print(f"  Unique Projects: {analytics['summary']['unique_projects']}")
            print(f"  Project Types: {len(analytics['summary']['project_types'])}")
            print(f"  Template Types: {len(analytics['summary']['template_types'])}")
            
            if analytics["summary"]["template_types"]:
                print("\n🔧 Most Used Templates:")
                sorted_templates = sorted(analytics["summary"]["template_types"].items(), key=lambda x: x[1], reverse=True)
                for template, count in sorted_templates[:5]:
                    print(f"    • {template}: {count} uses")
            
            if analytics["recommendations"]:
                print("\n💡 Recommendations:")
                for rec in analytics["recommendations"]:
                    print(f"    • {rec}")
        
        elif args.action == "history":
            if not args.project:
                print("❌ Error: --project required for history action")
                return
            
            project_path = Path(args.project)
            history = manager.get_project_template_history(project_path)
            
            if "error" in history:
                print(f"❌ {history['error']}")
                return
            
            print(f"📜 Template History: {project_path.name}")
            print(f"  Total Generations: {history['total_generations']}")
            print(f"  First Generation: {history['first_generation']}")
            print(f"  Latest Generation: {history['latest_generation']}")
            
            if history["evolution_summary"]:
                print("\n🔄 Evolution Summary:")
                for evolution in history["evolution_summary"]:
                    print(f"    • {evolution['date']}: {evolution['changes']} changes")
        
        elif args.action == "drift":
            drift_report = manager.detect_template_drift()
            
            print("🔍 Template Drift Analysis:")
            print(f"  Projects with drift: {len(drift_report['projects_with_drift'])}")
            
            if drift_report["projects_with_drift"]:
                print("\n⚠️  Projects with Template Drift:")
                for project in drift_report["projects_with_drift"]:
                    print(f"    • {Path(project['project_path']).name}: {len(project['drift_issues'])} issues")
            
            if drift_report["recommendations"]:
                print("\n🔧 Recommendations:")
                for rec in drift_report["recommendations"]:
                    print(f"    • {rec}")
        
        elif args.action == "clean":
            cleaned = manager.clean_stale_lineage_data(args.retention_days)
            
            print(f"🧹 Lineage Data Cleanup (retention: {args.retention_days} days):")
            print(f"  Generations removed: {cleaned['generations_removed']}")
            print(f"  Changes removed: {cleaned['changes_removed']}")
            print(f"  Cutoff date: {cleaned['cutoff_date']}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
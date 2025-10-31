#!/usr/bin/env python3
"""
Skills Creation Agent - Daily automation to identify skill opportunities
Location: /systems/skills-creation-agent/skills_creation_agent.py
Purpose: Scan projects, identify patterns, recommend skills, manage backlog
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s (%(levelname)s): %(message)s'
)
logger = logging.getLogger("skills-creation-agent")


class SkillsCreationAgent:
    """Agent that identifies opportunities to create skills from project patterns"""

    def __init__(self, claudec_root: str = "/Users/elizabethknopf/Documents/claudec"):
        self.claudec_root = Path(claudec_root)
        self.active_dir = self.claudec_root / "active"
        self.skills_main = self.claudec_root / "systems" / "skills-main"
        self.agent_dir = self.claudec_root / "systems" / "skills-creation-agent"
        self.data_dir = self.agent_dir / "data"
        self.reports_dir = self.agent_dir / "reports"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Load state
        self.backlog = self._load_backlog()
        self.existing_skills = self._load_existing_skills()
        self.scan_history = self._load_scan_history()

        logger.info("Skills Creation Agent initialized")
        logger.info(f"Watching: {self.active_dir}")
        logger.info(f"Existing skills: {len(self.existing_skills)}")
        logger.info(f"Backlog size: {len(self.backlog)}")

    def _load_backlog(self) -> List[Dict[str, Any]]:
        """Load backlog of skill recommendations"""
        backlog_file = self.data_dir / "backlog.json"
        if backlog_file.exists():
            try:
                with open(backlog_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading backlog: {e}")
        return []

    def _save_backlog(self):
        """Save backlog to disk"""
        backlog_file = self.data_dir / "backlog.json"
        try:
            with open(backlog_file, 'w') as f:
                json.dump(self.backlog, f, indent=2)
            logger.info(f"Backlog saved: {len(self.backlog)} items")
        except Exception as e:
            logger.error(f"Error saving backlog: {e}")

    def _load_existing_skills(self) -> Dict[str, Dict[str, Any]]:
        """Load existing skills from skills-main"""
        skills = {}

        if not self.skills_main.exists():
            logger.warning(f"Skills directory not found: {self.skills_main}")
            return skills

        for skill_dir in self.skills_main.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        content = skill_md.read_text()
                        # Extract description from YAML frontmatter
                        if content.startswith('---'):
                            parts = content.split('---', 2)
                            if len(parts) >= 3:
                                import re
                                desc_match = re.search(r'description:\s*(.+)', parts[1])
                                description = desc_match.group(1).strip() if desc_match else ""

                                skills[skill_dir.name] = {
                                    "name": skill_dir.name,
                                    "description": description,
                                    "path": str(skill_dir),
                                    "created": datetime.fromtimestamp(skill_md.stat().st_ctime).isoformat()
                                }
                    except Exception as e:
                        logger.error(f"Error loading skill {skill_dir.name}: {e}")

        return skills

    def _load_scan_history(self) -> Dict[str, Any]:
        """Load previous scan results"""
        history_file = self.data_dir / "scan_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading scan history: {e}")

        return {
            "last_scan": None,
            "patterns_seen": {},
            "recommendations_made": []
        }

    def _save_scan_history(self):
        """Save scan history"""
        history_file = self.data_dir / "scan_history.json"
        try:
            with open(history_file, 'w') as f:
                json.dump(self.scan_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving scan history: {e}")

    def scan_projects(self, days_back: int = 7) -> Dict[str, Any]:
        """Scan projects for patterns"""
        logger.info(f"Scanning projects from last {days_back} days...")

        cutoff_date = datetime.now() - timedelta(days=days_back)
        patterns = {
            "file_patterns": {},      # Repeated file structures
            "code_patterns": {},      # Repeated code patterns
            "workflow_patterns": {},  # Repeated workflows from CLAUDE.md/TODO.md
            "tool_usage": {},         # Frequently used tools/libraries
            "documentation": {},      # Documentation patterns
        }

        projects_scanned = 0

        for project_dir in self.active_dir.iterdir():
            if not project_dir.is_dir() or project_dir.name.startswith('.'):
                continue

            # Check if project has recent activity
            if not self._has_recent_activity(project_dir, cutoff_date):
                continue

            projects_scanned += 1
            logger.info(f"Scanning: {project_dir.name}")

            # Scan file patterns
            self._scan_file_patterns(project_dir, patterns["file_patterns"])

            # Scan code patterns
            self._scan_code_patterns(project_dir, patterns["code_patterns"])

            # Scan workflow patterns
            self._scan_workflow_patterns(project_dir, patterns["workflow_patterns"])

            # Scan tool usage
            self._scan_tool_usage(project_dir, patterns["tool_usage"])

            # Scan documentation patterns
            self._scan_documentation_patterns(project_dir, patterns["documentation"])

        logger.info(f"Scanned {projects_scanned} active projects")

        return {
            "scan_date": datetime.now().isoformat(),
            "projects_scanned": projects_scanned,
            "patterns": patterns
        }

    def _has_recent_activity(self, project_dir: Path, cutoff_date: datetime) -> bool:
        """Check if project has recent file modifications"""
        try:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mod_time > cutoff_date:
                        return True
        except Exception as e:
            logger.warning(f"Error checking activity for {project_dir.name}: {e}")
        return False

    def _scan_file_patterns(self, project_dir: Path, file_patterns: Dict):
        """Scan for repeated file structures"""
        # Look for common file types and structures
        file_types = {}

        try:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1

            # Track file type patterns across projects
            for ext, count in file_types.items():
                if ext not in file_patterns:
                    file_patterns[ext] = {"count": 0, "projects": []}
                file_patterns[ext]["count"] += count
                if project_dir.name not in file_patterns[ext]["projects"]:
                    file_patterns[ext]["projects"].append(project_dir.name)

        except Exception as e:
            logger.warning(f"Error scanning file patterns in {project_dir.name}: {e}")

    def _scan_code_patterns(self, project_dir: Path, code_patterns: Dict):
        """Scan for repeated code patterns"""
        # Look for repeated imports, class patterns, etc.
        try:
            # Check Python files
            for py_file in project_dir.rglob("*.py"):
                if py_file.is_file():
                    content = py_file.read_text()

                    # Track common imports
                    import_lines = [line for line in content.split('\n') if line.startswith('import ') or line.startswith('from ')]
                    for imp in import_lines:
                        pattern_key = f"python_import:{imp.strip()}"
                        if pattern_key not in code_patterns:
                            code_patterns[pattern_key] = {"count": 0, "projects": []}
                        code_patterns[pattern_key]["count"] += 1
                        if project_dir.name not in code_patterns[pattern_key]["projects"]:
                            code_patterns[pattern_key]["projects"].append(project_dir.name)

        except Exception as e:
            logger.warning(f"Error scanning code patterns in {project_dir.name}: {e}")

    def _scan_workflow_patterns(self, project_dir: Path, workflow_patterns: Dict):
        """Scan CLAUDE.md and TODO.md for repeated workflows"""
        try:
            # Check CLAUDE.md
            claude_md = project_dir / "CLAUDE.md"
            if claude_md.exists():
                content = claude_md.read_text().lower()

                # Look for common workflow keywords
                keywords = [
                    "setup", "install", "deploy", "test", "build", "debug",
                    "authentication", "database", "api", "frontend", "backend"
                ]

                for keyword in keywords:
                    if keyword in content:
                        pattern_key = f"workflow:{keyword}"
                        if pattern_key not in workflow_patterns:
                            workflow_patterns[pattern_key] = {"count": 0, "projects": []}
                        workflow_patterns[pattern_key]["count"] += 1
                        if project_dir.name not in workflow_patterns[pattern_key]["projects"]:
                            workflow_patterns[pattern_key]["projects"].append(project_dir.name)

        except Exception as e:
            logger.warning(f"Error scanning workflow patterns in {project_dir.name}: {e}")

    def _scan_tool_usage(self, project_dir: Path, tool_usage: Dict):
        """Scan for frequently used tools and libraries"""
        try:
            # Check package.json
            package_json = project_dir / "package.json"
            if package_json.exists():
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                for dep in deps.keys():
                    pattern_key = f"npm:{dep}"
                    if pattern_key not in tool_usage:
                        tool_usage[pattern_key] = {"count": 0, "projects": []}
                    tool_usage[pattern_key]["count"] += 1
                    if project_dir.name not in tool_usage[pattern_key]["projects"]:
                        tool_usage[pattern_key]["projects"].append(project_dir.name)

            # Check requirements.txt
            requirements = project_dir / "requirements.txt"
            if requirements.exists():
                for line in requirements.read_text().split('\n'):
                    if line and not line.startswith('#'):
                        pkg = line.split('==')[0].split('>=')[0].strip()
                        pattern_key = f"pip:{pkg}"
                        if pattern_key not in tool_usage:
                            tool_usage[pattern_key] = {"count": 0, "projects": []}
                        tool_usage[pattern_key]["count"] += 1
                        if project_dir.name not in tool_usage[pattern_key]["projects"]:
                            tool_usage[pattern_key]["projects"].append(project_dir.name)

        except Exception as e:
            logger.warning(f"Error scanning tool usage in {project_dir.name}: {e}")

    def _scan_documentation_patterns(self, project_dir: Path, doc_patterns: Dict):
        """Scan for documentation patterns"""
        try:
            # Check for common doc files
            doc_files = ["README.md", "CLAUDE.md", "TODO.md", "ARCHITECTURE.md"]

            for doc_file in doc_files:
                doc_path = project_dir / doc_file
                if doc_path.exists():
                    pattern_key = f"doc:{doc_file}"
                    if pattern_key not in doc_patterns:
                        doc_patterns[pattern_key] = {"count": 0, "projects": []}
                    doc_patterns[pattern_key]["count"] += 1
                    if project_dir.name not in doc_patterns[pattern_key]["projects"]:
                        doc_patterns[pattern_key]["projects"].append(project_dir.name)

        except Exception as e:
            logger.warning(f"Error scanning documentation in {project_dir.name}: {e}")

    def analyze_patterns(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze patterns and generate skill recommendations"""
        logger.info("Analyzing patterns for skill opportunities...")

        recommendations = []
        patterns = scan_results["patterns"]

        # Analyze each pattern category
        for category, category_patterns in patterns.items():
            for pattern_key, pattern_data in category_patterns.items():
                # Skip if less than 3 occurrences
                project_count = len(pattern_data.get("projects", []))
                if project_count < 3:
                    continue

                # Check if already exists as skill
                if self._is_duplicate_skill(pattern_key, pattern_data):
                    continue

                # Check if already in backlog
                if self._is_in_backlog(pattern_key):
                    continue

                # Generate recommendation
                recommendation = self._generate_recommendation(
                    category, pattern_key, pattern_data, scan_results
                )

                if recommendation:
                    recommendations.append(recommendation)

        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations

    def _is_duplicate_skill(self, pattern_key: str, pattern_data: Dict) -> bool:
        """Check if pattern already exists as a skill"""
        # Simple keyword matching for now
        pattern_lower = pattern_key.lower()

        for skill_name, skill_info in self.existing_skills.items():
            desc_lower = skill_info.get("description", "").lower()
            name_lower = skill_name.lower()

            # Check for keyword overlap
            if any(word in desc_lower or word in name_lower
                   for word in pattern_lower.split(':')):
                logger.debug(f"Pattern '{pattern_key}' matches existing skill '{skill_name}'")
                return True

        return False

    def _is_in_backlog(self, pattern_key: str) -> bool:
        """Check if pattern already in backlog"""
        for item in self.backlog:
            if item.get("pattern_key") == pattern_key:
                return True
        return False

    def _generate_recommendation(self, category: str, pattern_key: str,
                                 pattern_data: Dict, scan_results: Dict) -> Optional[Dict[str, Any]]:
        """Generate a skill recommendation from pattern"""

        # Calculate priority score
        project_count = len(pattern_data.get("projects", []))
        occurrence_count = pattern_data.get("count", 0)

        # Score: frequency * reusability
        priority_score = (project_count * 0.4) + (min(occurrence_count, 20) * 0.3) + (5 * 0.3)

        # Determine if skill or agent is better
        is_skill_worthy = self._is_skill_worthy(category, pattern_key, pattern_data)

        if not is_skill_worthy:
            return None

        # Generate skill name and description
        skill_name, skill_description = self._generate_skill_metadata(
            category, pattern_key, pattern_data
        )

        return {
            "pattern_key": pattern_key,
            "category": category,
            "skill_name": skill_name,
            "description": skill_description,
            "priority_score": round(priority_score, 2),
            "frequency": project_count,
            "occurrence_count": occurrence_count,
            "projects": pattern_data.get("projects", []),
            "rationale": f"Pattern appears in {project_count} projects, {occurrence_count} total occurrences",
            "recommended_structure": {
                "SKILL.md": "Main skill instructions",
                "scripts/": "Automation scripts if needed",
                "references/": "Reference files and examples"
            },
            "created_date": datetime.now().isoformat()
        }

    def _is_skill_worthy(self, category: str, pattern_key: str, pattern_data: Dict) -> bool:
        """Determine if pattern should be a skill vs agent"""

        # Agent-better patterns (requires state, monitoring)
        agent_keywords = [
            "monitor", "watch", "schedule", "periodic", "track", "daemon",
            "continuous", "persistent", "state", "database"
        ]

        if any(keyword in pattern_key.lower() for keyword in agent_keywords):
            logger.debug(f"Pattern '{pattern_key}' better suited for agent")
            return False

        # Skill-worthy patterns (procedural, repeatable, self-contained)
        if category in ["workflow_patterns", "documentation", "tool_usage"]:
            return True

        return True

    def _generate_skill_metadata(self, category: str, pattern_key: str,
                                  pattern_data: Dict) -> tuple:
        """Generate skill name and description"""

        # Extract meaningful parts from pattern_key
        parts = pattern_key.split(':')
        pattern_type = parts[0] if len(parts) > 0 else "general"
        pattern_detail = parts[1] if len(parts) > 1 else pattern_key

        # Generate skill name (kebab-case)
        skill_name = f"{pattern_type}-{pattern_detail}".replace('_', '-').replace(' ', '-').lower()

        # Generate description
        project_count = len(pattern_data.get("projects", []))
        description = f"Automates {pattern_detail} pattern found in {project_count} projects. "

        if pattern_type == "workflow":
            description += f"Handles {pattern_detail} workflow setup and execution."
        elif pattern_type == "doc":
            description += f"Generates and maintains {pattern_detail} documentation."
        elif pattern_type == "npm" or pattern_type == "pip":
            description += f"Manages {pattern_detail} integration and configuration."
        else:
            description += f"Implements common {pattern_type} pattern."

        return skill_name, description

    def manage_backlog(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Manage backlog of skill recommendations"""
        logger.info("Managing backlog...")

        # Add new recommendations to backlog
        new_items = 0
        for rec in recommendations:
            if not self._is_in_backlog(rec["pattern_key"]):
                self.backlog.append(rec)
                new_items += 1

        # Sort backlog by priority
        self.backlog.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

        # Check if we need user approval (>10 skills this week)
        week_old = datetime.now() - timedelta(days=7)
        recent_recommendations = [
            item for item in self.backlog
            if datetime.fromisoformat(item.get("created_date", datetime.now().isoformat())) > week_old
        ]

        needs_approval = len(recent_recommendations) > 10

        self._save_backlog()

        return {
            "backlog_size": len(self.backlog),
            "new_items": new_items,
            "recent_recommendations": len(recent_recommendations),
            "needs_approval": needs_approval,
            "top_5": self.backlog[:5]
        }

    def generate_report(self, scan_results: Dict, recommendations: List[Dict],
                       backlog_status: Dict) -> str:
        """Generate daily report"""
        logger.info("Generating daily report...")

        today = datetime.now().strftime("%Y-%m-%d")
        report_path = self.reports_dir / f"skills_opportunities_{today}.md"

        report = f"""# Skills Creation Opportunities - {today}

## Scan Summary

**Projects Scanned:** {scan_results['projects_scanned']}
**New Recommendations:** {backlog_status['new_items']}
**Backlog Size:** {backlog_status['backlog_size']}
**Recent (7 days):** {backlog_status['recent_recommendations']}

"""

        if backlog_status['needs_approval']:
            report += """⚠️ **APPROVAL NEEDED:** More than 10 skills recommended this week.
Please review backlog and approve which skills to create.

"""

        # High priority recommendations
        if recommendations:
            report += "## High Priority Recommendations\n\n"

            for i, rec in enumerate(recommendations[:5], 1):
                report += f"""### {i}. {rec['skill_name']} (Score: {rec['priority_score']}/10)

**Pattern:** {rec['pattern_key']}
**Frequency:** {rec['frequency']} projects, {rec['occurrence_count']} occurrences
**Rationale:** {rec['rationale']}

**Description:** {rec['description']}

**Projects using this pattern:**
"""
                for proj in rec['projects'][:10]:  # Show max 10 projects
                    report += f"- {proj}\n"

                report += f"""
**Suggested Structure:**
- SKILL.md: {rec['recommended_structure']['SKILL.md']}
- scripts/: {rec['recommended_structure']['scripts/']}
- references/: {rec['recommended_structure']['references/']}

**Status:** Ready to create

---

"""

        # Medium priority (from backlog)
        medium_priority = backlog_status.get('top_5', [])
        if medium_priority and len(medium_priority) > len(recommendations):
            report += "## Medium Priority (From Backlog)\n\n"
            for rec in medium_priority[len(recommendations):]:
                report += f"""### {rec['skill_name']} (Score: {rec['priority_score']}/10)
**Pattern:** {rec['pattern_key']}
**Frequency:** {rec['frequency']} projects
**Added:** {rec.get('created_date', 'Unknown')[:10]}

"""

        # Pattern summary
        report += "## Pattern Analysis\n\n"

        for category, patterns in scan_results['patterns'].items():
            if patterns:
                report += f"### {category.replace('_', ' ').title()}\n\n"
                # Show top 5 patterns
                sorted_patterns = sorted(
                    patterns.items(),
                    key=lambda x: len(x[1].get('projects', [])),
                    reverse=True
                )[:5]

                for pattern_key, pattern_data in sorted_patterns:
                    report += f"- **{pattern_key}**: {len(pattern_data.get('projects', []))} projects\n"
                report += "\n"

        # Save report
        try:
            report_path.write_text(report)
            logger.info(f"Report saved: {report_path}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

        return str(report_path)

    def run(self, days_back: int = 7) -> Dict[str, Any]:
        """Run the full skills creation agent workflow"""
        logger.info("=" * 60)
        logger.info("Skills Creation Agent - Daily Run")
        logger.info("=" * 60)

        # Step 1: Scan projects
        scan_results = self.scan_projects(days_back)

        # Step 2: Analyze patterns and generate recommendations
        recommendations = self.analyze_patterns(scan_results)

        # Step 3: Manage backlog
        backlog_status = self.manage_backlog(recommendations)

        # Step 4: Generate report
        report_path = self.generate_report(scan_results, recommendations, backlog_status)

        # Step 5: Update scan history
        self.scan_history["last_scan"] = datetime.now().isoformat()
        self.scan_history["recommendations_made"].extend([r["pattern_key"] for r in recommendations])
        self._save_scan_history()

        logger.info("=" * 60)
        logger.info(f"Run complete. Report: {report_path}")
        logger.info("=" * 60)

        return {
            "scan_results": scan_results,
            "recommendations": recommendations,
            "backlog_status": backlog_status,
            "report_path": report_path
        }


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Skills Creation Agent")
    parser.add_argument("--days", type=int, default=7, help="Days back to scan for activity")
    parser.add_argument("--report-only", action="store_true", help="Only generate report from existing backlog")
    parser.add_argument("--clear-backlog", action="store_true", help="Clear backlog")

    args = parser.parse_args()

    agent = SkillsCreationAgent()

    if args.clear_backlog:
        agent.backlog = []
        agent._save_backlog()
        print("✅ Backlog cleared")
        return

    if args.report_only:
        # Generate report from existing backlog
        report_path = agent.generate_report(
            {"projects_scanned": 0, "patterns": {}},
            [],
            {
                "backlog_size": len(agent.backlog),
                "new_items": 0,
                "recent_recommendations": 0,
                "needs_approval": False,
                "top_5": agent.backlog[:5]
            }
        )
        print(f"✅ Report generated: {report_path}")
        return

    # Full run
    result = agent.run(days_back=args.days)

    print(f"\n📊 Skills Creation Agent - Summary")
    print(f"=" * 60)
    print(f"Projects scanned: {result['scan_results']['projects_scanned']}")
    print(f"New recommendations: {len(result['recommendations'])}")
    print(f"Backlog size: {result['backlog_status']['backlog_size']}")
    print(f"Report: {result['report_path']}")

    if result['backlog_status']['needs_approval']:
        print(f"\n⚠️  APPROVAL NEEDED: {result['backlog_status']['recent_recommendations']} recommendations this week")
        print(f"Review backlog and decide which skills to create.")

    print("=" * 60)


if __name__ == "__main__":
    main()

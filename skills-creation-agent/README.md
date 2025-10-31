# Skills Creation Agent

**Daily automation to identify skill creation opportunities from project patterns**

## Overview

This agent scans your claudec projects daily, identifies repeatable patterns, and recommends new skills to create. It prevents duplicates, manages a backlog, and generates detailed reports.

## Features

- **Pattern Detection:** Scans file structures, code patterns, workflows, tool usage, and documentation
- **Smart Recommendations:** Only suggests skills for patterns appearing in 3+ projects
- **Duplicate Prevention:** Checks against existing skills and backlog
- **Backlog Management:** Maintains prioritized backlog, asks approval if >10/week
- **Automated Reports:** Daily markdown reports with actionable recommendations

## Usage

### Daily Run (Automated)

```bash
python3 skills_creation_agent.py
```

Scans last 7 days of project activity and generates recommendations.

### Manual Runs

```bash
# Scan specific timeframe
python3 skills_creation_agent.py --days 14

# Generate report from existing backlog
python3 skills_creation_agent.py --report-only

# Clear backlog
python3 skills_creation_agent.py --clear-backlog
```

## How It Works

### 1. Pattern Scanning

Analyzes:
- **File Patterns:** Repeated file structures and types
- **Code Patterns:** Common imports, class structures
- **Workflow Patterns:** CLAUDE.md and TODO.md patterns
- **Tool Usage:** npm/pip dependencies
- **Documentation:** README, ARCHITECTURE patterns

### 2. Pattern Analysis

For each pattern:
- Calculates frequency (how many projects)
- Scores reusability and complexity
- Checks if skill-worthy vs. agent-worthy
- Filters out duplicates

### 3. Skill vs Agent Decision

**Recommends Skill when:**
- Pattern is procedural/repeatable
- Self-contained workflow
- Deterministic outcome
- No state management needed

**Skips (Agent Better) when:**
- Requires monitoring/state
- Needs continuous operation
- Complex decision-making
- Database/persistence required

### 4. Backlog Management

- Maintains prioritized list
- Pulls from backlog when no new recommendations
- Asks approval if >10 skills in one week
- Tracks recommendation history

### 5. Report Generation

Daily markdown reports include:
- Scan summary
- High priority recommendations
- Medium priority (from backlog)
- Pattern analysis
- Suggested skill structures

## Output Files

```
/systems/skills-creation-agent/
├── data/
│   ├── backlog.json          # Prioritized backlog
│   └── scan_history.json     # Previous scans
├── reports/
│   └── skills_opportunities_YYYY-MM-DD.md
└── skills_creation_agent.py
```

## Report Format

Each recommendation includes:
- **Skill name** (auto-generated, kebab-case)
- **Priority score** (0-10)
- **Pattern frequency** (# projects, # occurrences)
- **Rationale** (why this should be a skill)
- **Description** (what the skill does)
- **Projects using pattern** (evidence)
- **Suggested structure** (SKILL.md, scripts, references)

## Integration with Daily Scheduler

Add to `/systems/scheduler-config.json`:

```json
{
  "name": "skills-creation-agent",
  "schedule": "daily",
  "time": "18:00",
  "command": "python3 /Users/elizabethknopf/Documents/claudec/systems/skills-creation-agent/skills_creation_agent.py",
  "description": "Scan for skill creation opportunities"
}
```

Or run via cron:

```bash
# Add to crontab
0 18 * * * cd /Users/elizabethknopf/Documents/claudec/systems/skills-creation-agent && python3 skills_creation_agent.py
```

## Examples

### Example Recommendation

```markdown
### project-bootstrapper (Score: 8.7/10)

**Pattern:** workflow:setup
**Frequency:** 12 projects, 45 occurrences
**Rationale:** Pattern appears in 12 projects, 45 total occurrences

**Description:** Automates setup pattern found in 12 projects. Handles setup workflow setup and execution.

**Projects using this pattern:**
- Personal-OS
- ContentGen
- AIBrain
- dirTechStack
...

**Suggested Structure:**
- SKILL.md: Main skill instructions
- scripts/: Automation scripts if needed
- references/: Reference files and examples

**Status:** Ready to create
```

### Weekly Workflow

**Monday-Friday:**
- Agent runs at 6pm daily
- Scans day's project activity
- Adds to backlog if patterns found

**Weekend Review:**
- Review weekly report
- Approve high-priority skills
- Use `skill-creator` tools to create approved skills

## Approval Workflow

When >10 skills recommended in a week:

1. **Agent alerts:** "⚠️ APPROVAL NEEDED"
2. **Review report:** Check backlog recommendations
3. **Prioritize:** Select which skills to create
4. **Create skills:** Use skill-creator tools
5. **Clear backlog:** Run with `--clear-backlog` after creating

## Pattern Examples

**File Pattern:**
```
workflow:authentication (8 projects)
→ Recommends: "authentication-setup" skill
```

**Tool Usage:**
```
npm:express (6 projects)
→ Recommends: "express-server-setup" skill
```

**Documentation:**
```
doc:CLAUDE.md (15 projects)
→ Recommends: "claude-context-file" skill
```

## Customization

### Adjust Thresholds

Edit `skills_creation_agent.py`:

```python
# Line ~200: Minimum project frequency
if project_count < 3:  # Change to 5 for stricter
    continue
```

### Add Pattern Categories

Add to `scan_projects()` method:

```python
patterns["your_category"] = {}
self._scan_your_category(project_dir, patterns["your_category"])
```

### Modify Scoring

Edit `_generate_recommendation()`:

```python
priority_score = (
    project_count * 0.4 +          # Frequency weight
    min(occurrence_count, 20) * 0.3 +  # Occurrence weight
    complexity_score * 0.3         # Add complexity
)
```

## Troubleshooting

**No recommendations:**
- Check if projects have recent activity (default: 7 days)
- Lower `project_count` threshold
- Run with `--days 30` for broader scan

**Too many recommendations:**
- Increase minimum frequency threshold
- Review duplicate detection logic
- Check if patterns are too granular

**Duplicate skills created:**
- Review `_is_duplicate_skill()` logic
- Add keywords to existing skill descriptions
- Use skill-creator validation before creating

## Next Steps

After daily run:

1. **Read report:** `cat reports/skills_opportunities_YYYY-MM-DD.md`
2. **Review top 5:** High priority recommendations
3. **Create skills:** Use skill-creator tools
4. **Update backlog:** Mark created skills as done

## Related Tools

- **skill-creator:** `/systems/skills-main/skill-creator/` - Tools to create skills
- **social_media_content_agent:** Example agent that uses skills
- **daily-scheduler:** Automation framework for daily runs

## Future Enhancements

- [ ] Machine learning for pattern detection
- [ ] Auto-generate draft SKILL.md files
- [ ] Performance tracking (which skills are most used)
- [ ] Integration with GitHub for automatic PR creation
- [ ] Skill analytics (ROI, usage metrics)

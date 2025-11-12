#!/usr/bin/env python3
"""
Daily YouTube Script Generator

Generates YouTube script variations using proven frameworks:
- Kallaway's 4-part hook structure
- WHY-WHAT-HOW body framework
- 3 strategic variations per topic
- Authority markers and credibility building

Usage:
    python3 youtube_script_daily_generator.py
    python3 youtube_script_daily_generator.py --topic "AI automation tools"
    python3 youtube_script_daily_generator.py --count 5
"""

import argparse
from datetime import datetime
from pathlib import Path
import json
import random

class YouTubeScriptGenerator:
    """Generate YouTube script variations with proven frameworks"""

    def __init__(self):
        self.output_dir = Path.home() / "Documents/claudec/active/Social-Content-Generator/pillar_scripts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Authority markers from boring business AI
        self.authority_markers = [
            "After implementing this across 50+ client projects",
            "From analyzing $500M+ in business automation deals",
            "Working with 47 portfolio companies",
            "Seeing this work in real M&A due diligence",
            "After 87% time reduction across implementations"
        ]

        # AI/Automation topics for daily generation
        self.topic_pool = [
            "AI automation for small business owners",
            "Claude Skills vs traditional automation tools",
            "Building compound leverage with AI agents",
            "ROI-focused AI implementation strategies",
            "Avoiding the 95% AI implementation failure rate",
            "Business process automation that actually works",
            "Strategic AI vs tactical feature chasing",
            "Workflow redesign before AI implementation",
            "AI content creation without generic output",
            "Automating decision-making in SMB operations"
        ]

        # Hook patterns (inspired by Kallaway framework)
        self.hook_patterns = {
            "contrarian": {
                "template": "Everyone's doing {wrong_thing}, but {contrarian_insight}",
                "structure": ["Pattern interrupt", "Challenge assumption", "Promise alternative", "Credibility marker"]
            },
            "authority": {
                "template": "{Authority marker} taught me {key_insight}",
                "structure": ["Authority statement", "Specific experience", "Counter-intuitive finding", "What it means"]
            },
            "transformation": {
                "template": "How to go from {before_state} to {after_state} in {timeframe}",
                "structure": ["Current pain", "Desired outcome", "Specific result", "Proof point"]
            }
        }

    def generate_hook(self, topic, variation_type):
        """Generate a hook using Kallaway's 4-part structure"""

        hooks = {
            "contrarian": {
                "pattern_interrupt": f"Stop buying AI tools.",
                "challenge": f"95% of AI pilots fail because companies chase features instead of redesigning workflows first.",
                "promise": f"Here's the MIT-backed approach that doubles ROI:",
                "credibility": random.choice(self.authority_markers)
            },
            "authority": {
                "authority_statement": random.choice(self.authority_markers),
                "specific_experience": f"I've watched companies waste millions on {topic} implementations.",
                "counter_intuitive": "The ones that succeeded did the opposite of what every AI vendor recommends.",
                "meaning": "And it comes down to one simple principle..."
            },
            "transformation": {
                "current_pain": f"Most businesses struggle with {topic} because they start with the wrong question.",
                "desired_outcome": f"What if you could automate 87% of the process in under 30 days?",
                "specific_result": "$2,400/month saved, 6x time reduction, measurable ROI.",
                "proof": f"{random.choice(self.authority_markers)} - here's the exact framework."
            }
        }

        return hooks.get(variation_type, hooks["transformation"])

    def generate_body_why_what_how(self, topic):
        """Generate WHY-WHAT-HOW body structure"""

        return {
            "why": {
                "section": "WHY this matters",
                "points": [
                    f"The business case for {topic} (MIT: workflow redesign first = 2x ROI)",
                    "Why 95% of implementations fail (S&P Global: wrong sequence)",
                    f"The compound leverage opportunity most people miss"
                ],
                "pattern_break": "But here's what nobody tells you..."
            },
            "what": {
                "section": "WHAT actually works",
                "framework": [
                    "Start with ONE process (not the whole business)",
                    "Map current workflow (before touching AI)",
                    "Identify decision points vs execution steps",
                    "Automate execution, augment decisions",
                    "Measure baseline vs automated performance"
                ],
                "example": f"Real example: $500M client case study"
            },
            "how": {
                "section": "HOW to implement this week",
                "steps": [
                    "Step 1: Pick your highest-cost manual process",
                    "Step 2: Document current workflow (30 minutes)",
                    "Step 3: Identify automation candidates (pattern recognition tasks)",
                    "Step 4: Build MVP automation (focus on 80% case)",
                    "Step 5: Test, measure, iterate before scaling"
                ],
                "closer": "This is how professionals implement AI - not by chasing features, but by redesigning for leverage."
            }
        }

    def generate_script_variation(self, topic, variation_type, index):
        """Generate complete script with hook + body"""

        hook = self.generate_hook(topic, variation_type)
        body = self.generate_body_why_what_how(topic)

        script = {
            "variation": index + 1,
            "type": variation_type,
            "topic": topic,
            "title": self.generate_title(topic, variation_type),
            "hook": hook,
            "body": body,
            "visual_callouts": self.generate_visual_callouts(variation_type),
            "strategic_reasoning": self.get_strategic_reasoning(variation_type)
        }

        return script

    def generate_title(self, topic, variation_type):
        """Generate YouTube title based on variation type"""

        titles = {
            "contrarian": f"Stop Using AI Tools (Do This Instead) | {topic.title()}",
            "authority": f"$500M in Deals Taught Me This About {topic.title()}",
            "transformation": f"How I Automated 87% of {topic.title()} in 30 Days"
        }

        return titles.get(variation_type, f"{topic.title()} - The Strategic Approach")

    def generate_visual_callouts(self, variation_type):
        """Suggest visual text overlays"""

        callouts = {
            "contrarian": ["95% FAIL", "MIT Research", "2X ROI", "Workflow First"],
            "authority": ["$500M Analyzed", "47 Companies", "87% Time Saved", "Real M&A Data"],
            "transformation": ["30 Days", "87% Automated", "$2.4K/mo Saved", "6X Faster"]
        }

        return callouts.get(variation_type, ["Key Point", "Framework", "Results"])

    def get_strategic_reasoning(self, variation_type):
        """Explain when to use each variation"""

        reasoning = {
            "contrarian": "Appeals to sophisticated buyers skeptical of AI hype. Best for LinkedIn and business-focused audiences. Tests contrarian positioning.",
            "authority": "Builds credibility with specific numbers and M&A experience. Strong for establishing expertise. Works across all platforms.",
            "transformation": "Algorithm-friendly with clear before/after. Broad appeal. Best for YouTube algorithm and new audience discovery."
        }

        return reasoning.get(variation_type, "General purpose variation")

    def format_markdown_output(self, scripts, topic):
        """Format scripts as markdown for saving"""

        date_str = datetime.now().strftime("%Y-%m-%d")

        markdown = f"""# YouTube Script Variations - {topic.title()}

**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
**Topic:** {topic}
**Variations:** {len(scripts)}

---

"""

        for script in scripts:
            markdown += f"""## Variation {script['variation']}: {script['type'].title()} Angle

**Title:** {script['title']}

**Strategic Reasoning:** {script['strategic_reasoning']}

### Hook (Kallaway's 4-Part Structure)

"""
            for key, value in script['hook'].items():
                markdown += f"**{key.replace('_', ' ').title()}:** {value}\n\n"

            markdown += f"""
### Body: WHY-WHAT-HOW Framework

#### WHY {script['body']['why']['section']}

"""
            for point in script['body']['why']['points']:
                markdown += f"- {point}\n"

            markdown += f"\n**Pattern Break:** {script['body']['why']['pattern_break']}\n\n"

            markdown += f"""#### WHAT {script['body']['what']['section']}

**Framework:**
"""
            for step in script['body']['what']['framework']:
                markdown += f"1. {step}\n"

            markdown += f"\n**Example:** {script['body']['what']['example']}\n\n"

            markdown += f"""#### HOW {script['body']['how']['section']}

"""
            for step in script['body']['how']['steps']:
                markdown += f"{step}\n"

            markdown += f"\n**Closer:** {script['body']['how']['closer']}\n\n"

            markdown += f"""### Visual Callouts

Suggested text overlays for video:
"""
            for callout in script['visual_callouts']:
                markdown += f"- `{callout}`\n"

            markdown += "\n---\n\n"

        # Add recommendations section
        markdown += f"""## Recommendations

### Testing Strategy

1. **A/B Test Hooks:** Try contrarian vs transformation in thumbnails/titles
2. **Audience Match:**
   - LinkedIn → Authority or Contrarian
   - YouTube → Transformation (algorithm-friendly)
   - Twitter → Contrarian (engagement)

3. **Visual Strategy:** Use specific numbers from authority variation in all thumbnails

### Production Notes

- **Intro:** First 8 seconds = hook only (pattern interrupt)
- **Pattern Breaks:** Re-hook every 2-3 minutes
- **B-Roll:** Show specific examples during WHAT section
- **CTA:** Link to implementation guide/framework in description

### Research Citations

- MIT: Workflow redesign before AI = 2x ROI
- S&P Global: 95% AI pilot failure rate
- Stanford: 72% optimistic, 62% lack expertise
- Microsoft/IDC: $3.50 return per $1 invested

---

**Generated by:** Boring Business AI YouTube Script Generator
**Next Steps:** Select variation → Record → Edit → Upload
**Upload to:** https://drive.google.com/drive/folders/1KFTbNaKf44tyIVPknDnzshW-DsrJuxnx
"""

        return markdown

    def generate_daily_scripts(self, topic=None, count=3):
        """Generate daily YouTube script variations"""

        if topic is None:
            topic = random.choice(self.topic_pool)

        print(f"\n{'='*80}")
        print(f"📹 YouTube Script Generator")
        print(f"{'='*80}\n")
        print(f"Topic: {topic}")
        print(f"Variations: {count}\n")

        variations = ["contrarian", "authority", "transformation"]
        scripts = []

        for i in range(min(count, len(variations))):
            variation_type = variations[i]
            print(f"Generating variation {i+1}/{count}: {variation_type.title()} angle...")

            script = self.generate_script_variation(topic, variation_type, i)
            scripts.append(script)

        # Save to markdown
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_topic = topic.lower().replace(" ", "_").replace("/", "_")[:50]
        filename = f"youtube_scripts_{date_str}_{safe_topic}.md"
        output_path = self.output_dir / filename

        markdown_content = self.format_markdown_output(scripts, topic)

        with open(output_path, 'w') as f:
            f.write(markdown_content)

        print(f"\n✅ Scripts generated successfully!")
        print(f"📁 Saved to: {output_path}")
        print(f"📊 {len(scripts)} variations created")
        print(f"\n💡 Next steps:")
        print(f"   1. Review scripts in: {output_path.name}")
        print(f"   2. Select variation based on audience/platform")
        print(f"   3. Record using selected hook + body structure")
        print(f"   4. Add visual callouts during editing")
        print(f"   5. Upload to Google Drive: https://drive.google.com/drive/folders/1KFTbNaKf44tyIVPknDnzshW-DsrJuxnx")

        return output_path


def main():
    parser = argparse.ArgumentParser(description='Generate daily YouTube script variations')
    parser.add_argument('--topic', type=str, help='Specific topic to generate scripts for')
    parser.add_argument('--count', type=int, default=3, help='Number of variations (1-3)')

    args = parser.parse_args()

    generator = YouTubeScriptGenerator()
    generator.generate_daily_scripts(topic=args.topic, count=args.count)


if __name__ == "__main__":
    main()

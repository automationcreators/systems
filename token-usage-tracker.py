#!/usr/bin/env python3
"""
Token Usage Tracker
Monitors and tracks AI token consumption across Personal OS operations
Target: 500-900 tokens/week with analytics and budgeting
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import time

class TokenUsageTracker:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.systems_dir = self.base_path / "systems"
        
        # Token tracking files
        self.usage_file = self.systems_dir / "token-usage.json"
        self.budget_file = self.systems_dir / "token-budget.json"
        self.analytics_file = self.systems_dir / "token-analytics.json"
        
        # Usage tracking state
        self.prompt_counter = 0
        self.session_tokens = 0
        self.session_start = datetime.now()
        
        # Budget settings
        self.weekly_budget = 900  # Maximum tokens per week
        self.warning_threshold = 0.8  # Warn at 80% of budget
        self.daily_budget = self.weekly_budget / 7
        
        # Setup logging
        self.setup_logging()
        
        # Load existing data
        self.load_usage_data()
        self.load_budget_settings()
        
        self.logger.info("Token Usage Tracker initialized")
    
    def setup_logging(self):
        """Setup token tracker logging"""
        log_file = self.systems_dir / "token-tracker.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_usage_data(self):
        """Load historical token usage data"""
        if self.usage_file.exists():
            with open(self.usage_file, 'r') as f:
                self.usage_data = json.load(f)
        else:
            self.usage_data = {
                "sessions": [],
                "daily_totals": {},
                "weekly_totals": {},
                "total_tokens": 0,
                "last_updated": datetime.now().isoformat()
            }
    
    def save_usage_data(self):
        """Save token usage data"""
        self.usage_data["last_updated"] = datetime.now().isoformat()
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def load_budget_settings(self):
        """Load budget configuration"""
        if self.budget_file.exists():
            with open(self.budget_file, 'r') as f:
                budget_config = json.load(f)
                self.weekly_budget = budget_config.get("weekly_budget", 900)
                self.warning_threshold = budget_config.get("warning_threshold", 0.8)
                self.daily_budget = self.weekly_budget / 7
        else:
            # Create default budget settings
            budget_config = {
                "weekly_budget": 900,
                "daily_budget": 900 / 7,
                "warning_threshold": 0.8,
                "hard_limit": True,
                "budget_rules": {
                    "ai_agent_prompts": 10,  # Max tokens per AI agent call
                    "emergency_reserve": 100,  # Reserve for critical tasks
                    "weekly_rollover": True  # Unused budget carries over
                },
                "created_at": datetime.now().isoformat()
            }
            
            with open(self.budget_file, 'w') as f:
                json.dump(budget_config, f, indent=2)
    
    def record_prompt_usage(self, operation: str, estimated_tokens: int = 0, actual_tokens: int = None):
        """Record token usage for a prompt/operation"""
        self.prompt_counter += 1
        
        # Use actual tokens if provided, otherwise estimate
        tokens_used = actual_tokens if actual_tokens is not None else estimated_tokens
        
        if tokens_used == 0:
            # Default estimation based on operation type
            token_estimates = {
                "project_analysis": 50,
                "document_parsing": 20,
                "security_template": 30,
                "dashboard_sync": 10,
                "discovery_scan": 15,
                "ai_consultation": 100,  # When we do need AI
                "general": 25
            }
            tokens_used = token_estimates.get(operation, 25)
        
        self.session_tokens += tokens_used
        
        # Record usage entry
        usage_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "tokens": tokens_used,
            "prompt_number": self.prompt_counter,
            "session_id": self.session_start.isoformat()
        }
        
        # Add to session data
        if "sessions" not in self.usage_data:
            self.usage_data["sessions"] = []
        
        # Find or create current session
        current_session = None
        for session in self.usage_data["sessions"]:
            if session["session_id"] == self.session_start.isoformat():
                current_session = session
                break
        
        if not current_session:
            current_session = {
                "session_id": self.session_start.isoformat(),
                "start_time": self.session_start.isoformat(),
                "operations": [],
                "total_tokens": 0,
                "prompt_count": 0
            }
            self.usage_data["sessions"].append(current_session)
        
        current_session["operations"].append(usage_entry)
        current_session["total_tokens"] += tokens_used
        current_session["prompt_count"] += 1
        
        # Update daily totals
        today = datetime.now().date().isoformat()
        if today not in self.usage_data["daily_totals"]:
            self.usage_data["daily_totals"][today] = 0
        self.usage_data["daily_totals"][today] += tokens_used
        
        # Update weekly totals
        week_start = (datetime.now().date() - timedelta(days=datetime.now().weekday())).isoformat()
        if week_start not in self.usage_data["weekly_totals"]:
            self.usage_data["weekly_totals"][week_start] = 0
        self.usage_data["weekly_totals"][week_start] += tokens_used
        
        # Update total
        self.usage_data["total_tokens"] += tokens_used
        
        self.logger.info(f"Token usage recorded: {operation} ({tokens_used} tokens, prompt #{self.prompt_counter})")
        
        # Check budget and warn if needed
        if self.prompt_counter % 10 == 0:  # Every 10 prompts
            self.check_budget_status()
        
        # Auto-save every few operations
        if self.prompt_counter % 5 == 0:
            self.save_usage_data()
        
        return usage_entry
    
    def check_budget_status(self) -> Dict:
        """Check current budget status and generate warnings"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now().date() - timedelta(days=datetime.now().weekday())).isoformat()
        
        daily_used = self.usage_data["daily_totals"].get(today, 0)
        weekly_used = self.usage_data["weekly_totals"].get(week_start, 0)
        
        status = {
            "daily": {
                "used": daily_used,
                "budget": self.daily_budget,
                "percentage": (daily_used / self.daily_budget) * 100,
                "remaining": self.daily_budget - daily_used
            },
            "weekly": {
                "used": weekly_used,
                "budget": self.weekly_budget,
                "percentage": (weekly_used / self.weekly_budget) * 100,
                "remaining": self.weekly_budget - weekly_used
            },
            "session": {
                "tokens": self.session_tokens,
                "prompts": self.prompt_counter,
                "duration_minutes": (datetime.now() - self.session_start).total_seconds() / 60
            },
            "warnings": []
        }
        
        # Generate warnings
        if status["weekly"]["percentage"] > self.warning_threshold * 100:
            status["warnings"].append(f"⚠️  Weekly budget {status['weekly']['percentage']:.1f}% used ({weekly_used}/{self.weekly_budget} tokens)")
        
        if status["daily"]["percentage"] > 100:
            status["warnings"].append(f"🔴 Daily budget exceeded: {daily_used}/{self.daily_budget:.1f} tokens")
        
        if status["weekly"]["percentage"] > 100:
            status["warnings"].append(f"🚨 WEEKLY BUDGET EXCEEDED: {weekly_used}/{self.weekly_budget} tokens")
        
        # Log warnings
        for warning in status["warnings"]:
            self.logger.warning(warning)
        
        # Log status every 10 prompts
        self.logger.info(f"Budget Status - Daily: {daily_used:.1f}/{self.daily_budget:.1f} tokens, Weekly: {weekly_used}/{self.weekly_budget} tokens")
        
        return status
    
    def generate_analytics(self) -> Dict:
        """Generate usage analytics and trends"""
        analytics = {
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "trends": {},
            "efficiency": {},
            "recommendations": []
        }
        
        # Summary statistics
        total_sessions = len(self.usage_data.get("sessions", []))
        total_tokens = self.usage_data.get("total_tokens", 0)
        
        if total_sessions > 0:
            avg_tokens_per_session = total_tokens / total_sessions
            avg_prompts_per_session = sum(s.get("prompt_count", 0) for s in self.usage_data["sessions"]) / total_sessions
        else:
            avg_tokens_per_session = 0
            avg_prompts_per_session = 0
        
        analytics["summary"] = {
            "total_tokens": total_tokens,
            "total_sessions": total_sessions,
            "avg_tokens_per_session": round(avg_tokens_per_session, 1),
            "avg_prompts_per_session": round(avg_prompts_per_session, 1),
            "total_days_tracked": len(self.usage_data.get("daily_totals", {}))
        }
        
        # Weekly trends
        weekly_data = self.usage_data.get("weekly_totals", {})
        if len(weekly_data) >= 2:
            weeks = sorted(weekly_data.keys())
            recent_weeks = weeks[-4:]  # Last 4 weeks
            
            weekly_usage = [weekly_data[week] for week in recent_weeks]
            avg_weekly = sum(weekly_usage) / len(weekly_usage)
            
            analytics["trends"] = {
                "recent_weeks": recent_weeks,
                "weekly_usage": weekly_usage,
                "average_weekly": round(avg_weekly, 1),
                "budget_adherence": round((avg_weekly / self.weekly_budget) * 100, 1)
            }
        
        # Efficiency analysis
        if self.usage_data.get("sessions"):
            operations = []
            for session in self.usage_data["sessions"]:
                operations.extend(session.get("operations", []))
            
            # Group by operation type
            op_stats = {}
            for op in operations:
                op_type = op.get("operation", "unknown")
                if op_type not in op_stats:
                    op_stats[op_type] = {"count": 0, "total_tokens": 0}
                
                op_stats[op_type]["count"] += 1
                op_stats[op_type]["total_tokens"] += op.get("tokens", 0)
            
            # Calculate efficiency
            for op_type, stats in op_stats.items():
                stats["avg_tokens"] = round(stats["total_tokens"] / stats["count"], 1)
            
            analytics["efficiency"] = {
                "operations": op_stats,
                "most_expensive": max(op_stats.items(), key=lambda x: x[1]["avg_tokens"]) if op_stats else None,
                "most_frequent": max(op_stats.items(), key=lambda x: x[1]["count"]) if op_stats else None
            }
        
        # Generate recommendations
        if analytics["trends"].get("budget_adherence", 0) > 90:
            analytics["recommendations"].append("Consider increasing weekly token budget or optimizing operations")
        
        if analytics["efficiency"].get("most_expensive"):
            expensive_op = analytics["efficiency"]["most_expensive"]
            if expensive_op[1]["avg_tokens"] > 50:
                analytics["recommendations"].append(f"Optimize '{expensive_op[0]}' operations - using {expensive_op[1]['avg_tokens']} tokens on average")
        
        if analytics["summary"]["avg_tokens_per_session"] > 100:
            analytics["recommendations"].append("Consider breaking down complex sessions to reduce token usage")
        
        # Save analytics
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        return analytics
    
    def reset_session(self):
        """Reset session counters (call at start of new session)"""
        if self.session_tokens > 0:
            # Finalize current session
            self.save_usage_data()
        
        self.prompt_counter = 0
        self.session_tokens = 0
        self.session_start = datetime.now()
        self.logger.info("Token tracking session reset")
    
    def get_budget_status_summary(self) -> str:
        """Get a concise budget status summary"""
        status = self.check_budget_status()
        
        weekly_pct = status["weekly"]["percentage"]
        daily_tokens = status["daily"]["used"]
        
        if weekly_pct > 100:
            return f"🚨 OVER BUDGET: {weekly_pct:.0f}% of weekly limit used"
        elif weekly_pct > 80:
            return f"⚠️  Budget Warning: {weekly_pct:.0f}% of weekly limit used"
        else:
            return f"✅ Budget OK: {weekly_pct:.0f}% of weekly limit used (today: {daily_tokens:.0f} tokens)"

def main():
    """CLI interface for token usage tracker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Token Usage Tracker")
    parser.add_argument("--action", choices=["status", "analytics", "record", "reset"], required=True)
    parser.add_argument("--operation", help="Operation name for recording")
    parser.add_argument("--tokens", type=int, help="Token count for recording")
    
    args = parser.parse_args()
    
    tracker = TokenUsageTracker()
    
    try:
        if args.action == "status":
            status = tracker.check_budget_status()
            print("📊 Token Usage Status:")
            print(f"  Daily: {status['daily']['used']:.1f}/{status['daily']['budget']:.1f} tokens ({status['daily']['percentage']:.1f}%)")
            print(f"  Weekly: {status['weekly']['used']}/{status['weekly']['budget']} tokens ({status['weekly']['percentage']:.1f}%)")
            print(f"  Session: {status['session']['tokens']} tokens, {status['session']['prompts']} prompts")
            
            if status["warnings"]:
                print("\nWarnings:")
                for warning in status["warnings"]:
                    print(f"  {warning}")
        
        elif args.action == "analytics":
            analytics = tracker.generate_analytics()
            print("📈 Token Usage Analytics:")
            print(f"  Total tokens: {analytics['summary']['total_tokens']}")
            print(f"  Total sessions: {analytics['summary']['total_sessions']}")
            print(f"  Avg tokens/session: {analytics['summary']['avg_tokens_per_session']}")
            
            if analytics["recommendations"]:
                print("\nRecommendations:")
                for rec in analytics["recommendations"]:
                    print(f"  • {rec}")
        
        elif args.action == "record":
            if not args.operation:
                print("Error: --operation required for record action")
                return
            
            result = tracker.record_prompt_usage(args.operation, args.tokens or 0)
            print(f"✅ Recorded: {args.operation} ({result['tokens']} tokens)")
        
        elif args.action == "reset":
            tracker.reset_session()
            print("✅ Session counters reset")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
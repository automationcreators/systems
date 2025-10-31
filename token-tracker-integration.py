#!/usr/bin/env python3
"""
Token Tracker Integration Module
Provides easy integration for Personal OS components to track token usage
"""

import os
import sys
from pathlib import Path

# Add systems directory to path
sys.path.insert(0, str(Path(__file__).parent))

import importlib.util
spec = importlib.util.spec_from_file_location("token_usage_tracker", Path(__file__).parent / "token-usage-tracker.py")
token_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(token_module)
TokenUsageTracker = token_module.TokenUsageTracker

# Global tracker instance
_tracker_instance = None

def get_tracker():
    """Get the global token tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = TokenUsageTracker()
    return _tracker_instance

def track_operation(operation_name: str, estimated_tokens: int = 0, actual_tokens: int = None):
    """
    Track token usage for an operation
    
    Args:
        operation_name: Name of the operation (e.g., 'project_discovery', 'template_generation')
        estimated_tokens: Estimated tokens if actual not available
        actual_tokens: Actual tokens used (preferred)
    
    Returns:
        dict: Usage entry record
    """
    tracker = get_tracker()
    return tracker.record_prompt_usage(operation_name, estimated_tokens, actual_tokens)

def check_budget():
    """Check current budget status"""
    tracker = get_tracker()
    return tracker.check_budget_status()

def get_budget_summary():
    """Get concise budget status summary"""
    tracker = get_tracker()
    return tracker.get_budget_status_summary()

def should_use_ai(estimated_tokens: int = 100) -> bool:
    """
    Check if we should use AI based on current budget
    
    Args:
        estimated_tokens: Estimated tokens for the AI operation
    
    Returns:
        bool: True if within budget, False if should avoid AI
    """
    tracker = get_tracker()
    status = tracker.check_budget_status()
    
    weekly_remaining = status["weekly"]["remaining"]
    weekly_pct = status["weekly"]["percentage"]
    
    # Don't use AI if we're over budget
    if weekly_pct > 100:
        return False
    
    # Be conservative if approaching budget limit
    if weekly_pct > 90 and estimated_tokens > 50:
        return False
    
    # Check if we have enough remaining tokens
    return weekly_remaining >= estimated_tokens

def reset_session():
    """Reset session counters (call at start of new session)"""
    tracker = get_tracker()
    tracker.reset_session()

# Decorator for automatic token tracking
def track_tokens(operation_name: str, estimated_tokens: int = 25):
    """
    Decorator to automatically track token usage for functions
    
    Usage:
        @track_tokens("document_parsing", 20)
        def parse_document(file_path):
            # function implementation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)
            
            # Track token usage
            track_operation(operation_name, estimated_tokens)
            
            return result
        return wrapper
    return decorator

# Context manager for tracking operations
class TokenTracker:
    """
    Context manager for tracking token usage in operations
    
    Usage:
        with TokenTracker("project_analysis", 50) as tracker:
            # do analysis work
            tracker.update_tokens(75)  # if actual usage known
    """
    
    def __init__(self, operation_name: str, estimated_tokens: int = 25):
        self.operation_name = operation_name
        self.estimated_tokens = estimated_tokens
        self.actual_tokens = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        track_operation(self.operation_name, self.estimated_tokens, self.actual_tokens)
    
    def update_tokens(self, actual_tokens: int):
        """Update with actual token count"""
        self.actual_tokens = actual_tokens

# Quick integration functions for Personal OS components
def track_discovery_operation():
    """Track a project discovery operation"""
    return track_operation("project_discovery", 15)

def track_document_parsing():
    """Track a document parsing operation"""
    return track_operation("document_parsing", 20)

def track_template_generation():
    """Track a template generation operation"""
    return track_operation("template_generation", 30)

def track_dashboard_sync():
    """Track a dashboard sync operation"""
    return track_operation("dashboard_sync", 10)

def track_security_audit():
    """Track a security audit operation"""
    return track_operation("security_audit", 25)

def track_ai_consultation(estimated_tokens: int = 100):
    """Track when we actually need to use AI"""
    if should_use_ai(estimated_tokens):
        return track_operation("ai_consultation", estimated_tokens)
    else:
        # Log that we skipped AI due to budget
        tracker = get_tracker()
        tracker.logger.warning(f"Skipped AI consultation to preserve token budget")
        return None

def initialize_tracker():
    """Initialize tracker at system startup"""
    tracker = get_tracker()
    tracker.logger.info("Token tracker integration initialized")
    return tracker

if __name__ == "__main__":
    # Test the integration
    print("🧪 Testing Token Tracker Integration")
    
    # Test basic tracking
    track_discovery_operation()
    track_document_parsing()
    track_template_generation()
    
    print("Budget Status:", get_budget_summary())
    
    # Test decorator
    @track_tokens("test_operation", 35)
    def test_function():
        return "test result"
    
    result = test_function()
    print(f"Decorated function result: {result}")
    
    # Test context manager
    with TokenTracker("context_test", 40) as tracker:
        print("Doing work in context...")
        tracker.update_tokens(45)  # Update with actual usage
    
    print("Final Budget Status:", get_budget_summary())
    print("✅ Integration test complete")
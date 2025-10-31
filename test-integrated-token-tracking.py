#!/usr/bin/env python3
"""
Test Integrated Token Tracking System
Demonstrates token tracking across all Personal OS components
"""

import sys
from pathlib import Path

# Import token tracker integration
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("token_tracker", Path(__file__).parent / "token-tracker-integration.py")
tracker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker_module)

def test_token_tracking():
    """Test comprehensive token tracking system"""
    print("🧪 Testing Integrated Token Tracking System")
    print("=" * 50)
    
    # Reset session for clean test
    tracker_module.reset_session()
    
    # Test basic operations
    print("\n1. Testing Basic Operations:")
    tracker_module.track_discovery_operation()
    print("   ✅ Project discovery tracked")
    
    tracker_module.track_document_parsing()
    print("   ✅ Document parsing tracked")
    
    tracker_module.track_template_generation()
    print("   ✅ Template generation tracked")
    
    tracker_module.track_dashboard_sync()
    print("   ✅ Dashboard sync tracked")
    
    # Test budget checking
    print("\n2. Budget Status:")
    status = tracker_module.check_budget()
    print(f"   Daily: {status['daily']['used']:.1f}/{status['daily']['budget']:.1f} tokens ({status['daily']['percentage']:.1f}%)")
    print(f"   Weekly: {status['weekly']['used']}/{status['weekly']['budget']} tokens ({status['weekly']['percentage']:.1f}%)")
    
    # Test AI consultation check
    print("\n3. AI Budget Decisions:")
    can_use_ai_small = tracker_module.should_use_ai(50)
    can_use_ai_large = tracker_module.should_use_ai(200)
    print(f"   Small AI operation (50 tokens): {'✅ Allowed' if can_use_ai_small else '❌ Blocked'}")
    print(f"   Large AI operation (200 tokens): {'✅ Allowed' if can_use_ai_large else '❌ Blocked'}")
    
    # Test decorator
    print("\n4. Testing Decorator:")
    @tracker_module.track_tokens("test_function", 25)
    def test_function():
        return "Test completed"
    
    result = test_function()
    print(f"   Function result: {result}")
    print("   ✅ Decorator tracking completed")
    
    # Test context manager
    print("\n5. Testing Context Manager:")
    with tracker_module.TokenTracker("context_operation", 40) as ctx:
        print("   Executing operation in context...")
        ctx.update_tokens(35)  # Actual usage was lower
    print("   ✅ Context manager tracking completed")
    
    # Final budget summary
    print("\n6. Final Budget Summary:")
    summary = tracker_module.get_budget_summary()
    print(f"   {summary}")
    
    # Generate analytics
    print("\n7. Analytics Generation:")
    tracker = tracker_module.get_tracker()
    analytics = tracker.generate_analytics()
    print(f"   Total operations: {len(tracker.usage_data.get('sessions', []))}")
    print(f"   Total tokens used: {analytics['summary']['total_tokens']}")
    print(f"   Average tokens per session: {analytics['summary']['avg_tokens_per_session']}")
    
    if analytics.get('recommendations'):
        print("   Recommendations:")
        for rec in analytics['recommendations']:
            print(f"     • {rec}")
    
    print("\n✅ Token tracking integration test complete!")
    print(f"📊 Session summary: {status['session']['tokens']} tokens, {status['session']['prompts']} prompts")
    
    return analytics

def test_budget_warnings():
    """Test budget warning system"""
    print("\n🚨 Testing Budget Warning System")
    print("=" * 40)
    
    # Simulate high usage to trigger warnings
    print("Simulating high token usage...")
    
    for i in range(20):
        tracker_module.track_operation(f"simulation_{i}", 30)
    
    # Check if warnings are triggered
    status = tracker_module.check_budget()
    
    if status['warnings']:
        print("Warnings generated:")
        for warning in status['warnings']:
            print(f"   {warning}")
    else:
        print("No warnings at current usage level")
    
    return status

if __name__ == "__main__":
    # Run comprehensive tests
    analytics = test_token_tracking()
    
    print("\n" + "=" * 50)
    
    # Test budget warnings if needed
    if analytics['summary']['total_tokens'] < 500:  # Only if we haven't used too many tokens
        warning_status = test_budget_warnings()
    
    print(f"\n🎯 Test complete! Check token-usage.json for detailed tracking data.")
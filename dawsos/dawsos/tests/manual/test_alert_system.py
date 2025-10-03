#!/usr/bin/env python3
"""
Test script for Alert System
Validates core functionality of AlertManager and AlertPanel
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.alert_manager import AlertManager
from core.agent_runtime import AgentRuntime


def test_alert_creation():
    """Test creating alerts"""
    print("🧪 Testing Alert Creation...")

    alert_manager = AlertManager(storage_dir='storage/alerts_test')

    # Test 1: Create a simple alert
    alert = alert_manager.create_alert(
        name="Test Stock Price Alert",
        alert_type="pattern",
        condition={
            'field': 'AAPL.price',
            'operator': '>',
            'value': 150.0
        },
        severity="warning"
    )

    assert alert is not None
    assert alert.name == "Test Stock Price Alert"
    print(f"  ✅ Created alert: {alert.name} (ID: {alert.alert_id})")

    # Test 2: Create alert from template
    template_alert = alert_manager.create_template_alert(
        'stock_price_below',
        symbol='TSLA',
        threshold=200.0
    )

    assert template_alert is not None
    print(f"  ✅ Created template alert: {template_alert.name}")

    # Test 3: Create system health alert
    health_alert = alert_manager.create_template_alert(
        'pattern_failure',
        threshold=0.8
    )

    assert health_alert is not None
    print(f"  ✅ Created system alert: {health_alert.name}")

    print(f"  📊 Total alerts created: {len(alert_manager.alerts)}")
    print()

    return alert_manager


def test_alert_conditions():
    """Test alert condition evaluation"""
    print("🧪 Testing Alert Conditions...")

    alert_manager = AlertManager(storage_dir='storage/alerts_test')

    # Create test alert
    alert = alert_manager.create_alert(
        name="Price Threshold Test",
        alert_type="pattern",
        condition={
            'field': 'stock.price',
            'operator': '>',
            'value': 100.0
        },
        severity="info"
    )

    # Test condition evaluation
    test_data_1 = {'stock': {'price': 150.0}}
    test_data_2 = {'stock': {'price': 50.0}}

    result_1 = alert.condition.evaluate(test_data_1)
    result_2 = alert.condition.evaluate(test_data_2)

    assert result_1 == True, "Should trigger when price > 100"
    assert result_2 == False, "Should not trigger when price < 100"

    print("  ✅ Condition evaluation working correctly")
    print(f"     - Test 1 (price=150): {result_1} (expected True)")
    print(f"     - Test 2 (price=50): {result_2} (expected False)")
    print()

    return alert_manager


def test_alert_triggering():
    """Test alert triggering and events"""
    print("🧪 Testing Alert Triggering...")

    alert_manager = AlertManager(storage_dir='storage/alerts_test')

    # Create alert
    alert = alert_manager.create_alert(
        name="Trigger Test Alert",
        alert_type="pattern",
        condition={
            'field': 'value',
            'operator': '>=',
            'value': 100
        },
        severity="warning"
    )

    # Trigger alert
    test_data = {'value': 150}
    event = alert_manager.trigger_alert(alert, test_data)

    assert event is not None
    assert event.alert_name == "Trigger Test Alert"
    assert not event.acknowledged

    print("  ✅ Alert triggered successfully")
    print(f"     - Event ID: {event.event_id}")
    print(f"     - Message: {event.message}")
    print(f"     - Severity: {event.severity.value}")
    print(f"     - Acknowledged: {event.acknowledged}")

    # Test acknowledgment
    success = alert_manager.acknowledge_alert(event.event_id)
    assert success == True

    # Verify acknowledgment
    updated_event = next(e for e in alert_manager.history if e.event_id == event.event_id)
    assert updated_event.acknowledged == True

    print("  ✅ Alert acknowledged successfully")
    print()

    return alert_manager


def test_alert_persistence():
    """Test saving and loading alerts"""
    print("🧪 Testing Alert Persistence...")

    # Create manager and alerts
    alert_manager_1 = AlertManager(storage_dir='storage/alerts_test')

    alert_1 = alert_manager_1.create_alert(
        name="Persistence Test Alert 1",
        alert_type="data_quality",
        condition={'field': 'test', 'operator': '>', 'value': 0},
        severity="info"
    )

    alert_2 = alert_manager_1.create_template_alert(
        'compliance_violation',
        threshold=0
    )

    initial_count = len(alert_manager_1.alerts)
    print(f"  📝 Created {initial_count} alerts")

    # Create new manager instance (should load from disk)
    alert_manager_2 = AlertManager(storage_dir='storage/alerts_test')

    loaded_count = len(alert_manager_2.alerts)
    assert loaded_count == initial_count, f"Expected {initial_count} alerts, got {loaded_count}"

    print(f"  ✅ Successfully loaded {loaded_count} alerts from storage")

    # Verify alert details
    loaded_alert = alert_manager_2.get_alert(alert_1.alert_id)
    assert loaded_alert is not None
    assert loaded_alert.name == alert_1.name

    print("  ✅ Alert details preserved correctly")
    print()

    return alert_manager_2


def test_alert_checking():
    """Test checking alerts against runtime data"""
    print("🧪 Testing Alert Checking with Runtime...")

    alert_manager = AlertManager(storage_dir='storage/alerts_test')
    runtime = AgentRuntime()

    # Create system health alert
    alert = alert_manager.create_alert(
        name="Success Rate Monitor",
        alert_type="pattern",
        condition={
            'field': 'pattern_execution.success_rate',
            'operator': '<',
            'value': 0.5
        },
        severity="critical"
    )

    # Simulate some executions
    for i in range(10):
        runtime._log_execution(
            'test_agent',
            {'test': 'data'},
            {'result': 'success'} if i % 2 == 0 else {'error': 'failed'}
        )

    # Check alerts
    triggered = alert_manager.check_alerts(runtime)

    print(f"  📊 Runtime executions: {len(runtime.execution_history)}")
    print(f"  🔔 Triggered alerts: {len(triggered)}")

    if triggered:
        for event in triggered:
            print(f"     - {event.alert_name}: {event.message}")

    print("  ✅ Alert checking completed")
    print()

    return alert_manager


def test_alert_summary():
    """Test alert summary generation"""
    print("🧪 Testing Alert Summary...")

    alert_manager = AlertManager(storage_dir='storage/alerts_test')

    # Create various alerts
    alert_manager.create_template_alert('stock_price_above', symbol='AAPL', threshold=150)
    alert_manager.create_template_alert('pattern_failure', threshold=0.8)
    alert_manager.create_template_alert('compliance_violation', threshold=0)

    # Get summary
    summary = alert_manager.get_alert_summary()

    print("  📊 Alert Summary:")
    print(f"     - Total Alerts: {summary['total_alerts']}")
    print(f"     - Active Alerts: {summary['active_alerts']}")
    print(f"     - Triggered Alerts: {summary['triggered_alerts']}")
    print("     - Severity Breakdown:")
    print(f"       • Info: {summary['severity_counts']['info']}")
    print(f"       • Warning: {summary['severity_counts']['warning']}")
    print(f"       • Critical: {summary['severity_counts']['critical']}")
    print(f"     - Unacknowledged Events: {summary['unacknowledged_events']}")

    print("  ✅ Summary generated successfully")
    print()

    return summary


def test_all_templates():
    """Test all alert templates"""
    print("🧪 Testing All Alert Templates...")

    alert_manager = AlertManager(storage_dir='storage/alerts_test')

    templates_tested = 0

    # Stock price templates
    try:
        alert_manager.create_template_alert('stock_price_above', symbol='AAPL', threshold=150)
        print("  ✅ stock_price_above template")
        templates_tested += 1
    except Exception as e:
        print(f"  ❌ stock_price_above failed: {e}")

    try:
        alert_manager.create_template_alert('stock_price_below', symbol='TSLA', threshold=200)
        print("  ✅ stock_price_below template")
        templates_tested += 1
    except Exception as e:
        print(f"  ❌ stock_price_below failed: {e}")

    # System health templates
    try:
        alert_manager.create_template_alert('pattern_failure', threshold=0.8)
        print("  ✅ pattern_failure template")
        templates_tested += 1
    except Exception as e:
        print(f"  ❌ pattern_failure failed: {e}")

    try:
        alert_manager.create_template_alert('response_time', threshold=5.0)
        print("  ✅ response_time template")
        templates_tested += 1
    except Exception as e:
        print(f"  ❌ response_time failed: {e}")

    # Data quality templates
    try:
        alert_manager.create_template_alert('data_freshness', dataset='FRED', max_age_hours=24)
        print("  ✅ data_freshness template")
        templates_tested += 1
    except Exception as e:
        print(f"  ❌ data_freshness failed: {e}")

    # Compliance templates
    try:
        alert_manager.create_template_alert('compliance_violation', threshold=0)
        print("  ✅ compliance_violation template")
        templates_tested += 1
    except Exception as e:
        print(f"  ❌ compliance_violation failed: {e}")

    # Graph templates
    try:
        alert_manager.create_template_alert('graph_anomaly', threshold=100)
        print("  ✅ graph_anomaly template")
        templates_tested += 1
    except Exception as e:
        print(f"  ❌ graph_anomaly failed: {e}")

    print(f"\n  📊 Templates tested: {templates_tested}/7")
    print()


def cleanup_test_data():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")

    import shutil
    test_dir = Path('storage/alerts_test')

    if test_dir.exists():
        shutil.rmtree(test_dir)
        print(f"  ✅ Removed {test_dir}")
    else:
        print("  ℹ️  No test data to clean up")

    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Alert System Test Suite")
    print("=" * 60)
    print()

    try:
        # Run tests
        test_alert_creation()
        test_alert_conditions()
        test_alert_triggering()
        test_alert_persistence()
        test_alert_checking()
        test_alert_summary()
        test_all_templates()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print()

        # Cleanup
        cleanup_test_data()

        return 0

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        return 1

    except Exception as e:
        print()
        print("=" * 60)
        print(f"💥 Unexpected error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Alert Manager - Comprehensive alert and notification system for DawsOS Trinity
Monitors patterns, data quality, system health, and provides user notifications
"""

import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import re


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status states"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertType(Enum):
    """Types of alerts supported"""
    PATTERN = "pattern"
    DATA_QUALITY = "data_quality"
    SYSTEM_HEALTH = "system_health"
    TRINITY_COMPLIANCE = "trinity_compliance"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    CUSTOM = "custom"


@dataclass
class AlertCondition:
    """Represents an alert condition"""
    field: str
    operator: str  # >, <, >=, <=, ==, !=, contains, missing
    value: Any

    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate condition against data"""
        # Extract field value using dot notation (e.g., "price.current")
        field_value = self._get_nested_value(data, self.field)

        if field_value is None and self.operator != "missing":
            return False

        if self.operator == ">":
            return float(field_value) > float(self.value)
        elif self.operator == "<":
            return float(field_value) < float(self.value)
        elif self.operator == ">=":
            return float(field_value) >= float(self.value)
        elif self.operator == "<=":
            return float(field_value) <= float(self.value)
        elif self.operator == "==":
            return field_value == self.value
        elif self.operator == "!=":
            return field_value != self.value
        elif self.operator == "contains":
            return str(self.value).lower() in str(field_value).lower()
        elif self.operator == "missing":
            return field_value is None
        else:
            return False

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value


@dataclass
class Alert:
    """Represents a single alert configuration"""
    alert_id: str
    name: str
    alert_type: AlertType
    condition: AlertCondition
    severity: AlertSeverity
    enabled: bool = True
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: str = None
    last_triggered: str = None
    trigger_count: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        result = asdict(self)
        result['alert_type'] = self.alert_type.value
        result['severity'] = self.severity.value
        result['status'] = self.status.value
        result['condition'] = {
            'field': self.condition.field,
            'operator': self.condition.operator,
            'value': self.condition.value
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create alert from dictionary"""
        condition = AlertCondition(
            field=data['condition']['field'],
            operator=data['condition']['operator'],
            value=data['condition']['value']
        )

        return cls(
            alert_id=data['alert_id'],
            name=data['name'],
            alert_type=AlertType(data['alert_type']),
            condition=condition,
            severity=AlertSeverity(data['severity']),
            enabled=data.get('enabled', True),
            status=AlertStatus(data.get('status', 'active')),
            created_at=data.get('created_at'),
            last_triggered=data.get('last_triggered'),
            trigger_count=data.get('trigger_count', 0),
            metadata=data.get('metadata', {})
        )


@dataclass
class AlertEvent:
    """Represents a triggered alert event"""
    event_id: str
    alert_id: str
    alert_name: str
    severity: AlertSeverity
    timestamp: str
    message: str
    details: Dict[str, Any]
    acknowledged: bool = False
    acknowledged_at: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        result = asdict(self)
        result['severity'] = self.severity.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertEvent':
        """Create event from dictionary"""
        return cls(
            event_id=data['event_id'],
            alert_id=data['alert_id'],
            alert_name=data['alert_name'],
            severity=AlertSeverity(data['severity']),
            timestamp=data['timestamp'],
            message=data['message'],
            details=data.get('details', {}),
            acknowledged=data.get('acknowledged', False),
            acknowledged_at=data.get('acknowledged_at')
        )


class AlertManager:
    """Manages all alerts and notifications for DawsOS Trinity"""

    def __init__(self, storage_dir: str = "storage/alerts"):
        """Initialize AlertManager"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.alerts_file = self.storage_dir / "alerts.json"
        self.history_file = self.storage_dir / "history.json"

        self.alerts: Dict[str, Alert] = {}
        self.history: List[AlertEvent] = []
        self.callbacks: Dict[str, List[Callable]] = {}

        self._load_alerts()
        self._load_history()

    def create_alert(self, name: str, alert_type: str, condition: Dict[str, Any],
                     severity: str, metadata: Dict[str, Any] = None) -> Alert:
        """Create a new alert"""
        alert_id = self._generate_alert_id(name)

        alert_condition = AlertCondition(
            field=condition['field'],
            operator=condition['operator'],
            value=condition['value']
        )

        alert = Alert(
            alert_id=alert_id,
            name=name,
            alert_type=AlertType(alert_type),
            condition=alert_condition,
            severity=AlertSeverity(severity),
            metadata=metadata or {}
        )

        self.alerts[alert_id] = alert
        self._save_alerts()

        return alert

    def update_alert(self, alert_id: str, **kwargs) -> Optional[Alert]:
        """Update an existing alert"""
        if alert_id not in self.alerts:
            return None

        alert = self.alerts[alert_id]

        for key, value in kwargs.items():
            if hasattr(alert, key):
                setattr(alert, key, value)

        self._save_alerts()
        return alert

    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self._save_alerts()
            return True
        return False

    def check_alerts(self, runtime) -> List[AlertEvent]:
        """Check all active alerts and trigger if conditions are met"""
        triggered_events = []

        for alert in self.alerts.values():
            if not alert.enabled or alert.status != AlertStatus.ACTIVE:
                continue

            # Get data based on alert type
            data = self._get_alert_data(alert.alert_type, runtime)

            # Check condition
            if alert.condition.evaluate(data):
                event = self.trigger_alert(alert, data)
                triggered_events.append(event)

        return triggered_events

    def trigger_alert(self, alert: Alert, details: Dict[str, Any]) -> AlertEvent:
        """Trigger an alert and create event"""
        event_id = self._generate_event_id()

        # Create alert event
        event = AlertEvent(
            event_id=event_id,
            alert_id=alert.alert_id,
            alert_name=alert.name,
            severity=alert.severity,
            timestamp=datetime.now().isoformat(),
            message=self._generate_alert_message(alert, details),
            details=details
        )

        # Update alert status
        alert.status = AlertStatus.TRIGGERED
        alert.last_triggered = event.timestamp
        alert.trigger_count += 1

        # Add to history
        self.history.append(event)

        # Save updates
        self._save_alerts()
        self._save_history()

        # Execute callbacks
        self._execute_callbacks(alert.alert_type.value, event)

        return event

    def acknowledge_alert(self, event_id: str) -> bool:
        """Acknowledge a triggered alert event"""
        for event in self.history:
            if event.event_id == event_id:
                event.acknowledged = True
                event.acknowledged_at = datetime.now().isoformat()

                # Update alert status
                if event.alert_id in self.alerts:
                    self.alerts[event.alert_id].status = AlertStatus.ACKNOWLEDGED

                self._save_history()
                self._save_alerts()
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert (mark as resolved)"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.RESOLVED
            self._save_alerts()
            return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (enabled) alerts"""
        return [a for a in self.alerts.values() if a.enabled and a.status == AlertStatus.ACTIVE]

    def get_triggered_alerts(self) -> List[Alert]:
        """Get all triggered alerts"""
        return [a for a in self.alerts.values() if a.status == AlertStatus.TRIGGERED]

    def get_alert_history(self, limit: int = 50, severity: str = None) -> List[AlertEvent]:
        """Get alert history with optional filtering"""
        history = self.history[-limit:]

        if severity:
            history = [e for e in history if e.severity.value == severity]

        return sorted(history, key=lambda x: x.timestamp, reverse=True)

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get specific alert by ID"""
        return self.alerts.get(alert_id)

    def register_callback(self, alert_type: str, callback: Callable):
        """Register a callback function for alert type"""
        if alert_type not in self.callbacks:
            self.callbacks[alert_type] = []
        self.callbacks[alert_type].append(callback)

    def create_template_alert(self, template_name: str, **params) -> Alert:
        """Create alert from predefined template"""
        # Template builders - only construct when called
        if template_name == 'stock_price_above':
            return self.create_alert(
                name=f"{params['symbol']} Price Above ${params['threshold']}",
                alert_type='pattern',
                condition={
                    'field': f"{params['symbol']}.price",
                    'operator': '>',
                    'value': params['threshold']
                },
                severity='warning',
                metadata={'symbol': params['symbol'], 'template': 'stock_price_above'}
            )

        elif template_name == 'stock_price_below':
            return self.create_alert(
                name=f"{params['symbol']} Price Below ${params['threshold']}",
                alert_type='pattern',
                condition={
                    'field': f"{params['symbol']}.price",
                    'operator': '<',
                    'value': params['threshold']
                },
                severity='warning',
                metadata={'symbol': params['symbol'], 'template': 'stock_price_below'}
            )

        elif template_name == 'pattern_failure':
            return self.create_alert(
                name="Pattern Execution Failure Alert",
                alert_type='system_health',
                condition={
                    'field': 'pattern_execution.success_rate',
                    'operator': '<',
                    'value': params.get('threshold', 0.8)
                },
                severity='critical',
                metadata={'template': 'pattern_failure'}
            )

        elif template_name == 'data_freshness':
            return self.create_alert(
                name=f"{params['dataset']} Data Freshness Alert",
                alert_type='data_quality',
                condition={
                    'field': f"{params['dataset']}.age_hours",
                    'operator': '>',
                    'value': params.get('max_age_hours', 24)
                },
                severity='warning',
                metadata={'dataset': params['dataset'], 'template': 'data_freshness'}
            )

        elif template_name == 'response_time':
            return self.create_alert(
                name='System Response Time Alert',
                alert_type='system_health',
                condition={
                    'field': 'system.avg_response_time',
                    'operator': '>',
                    'value': params.get('threshold', 5.0)
                },
                severity='warning',
                metadata={'template': 'response_time'}
            )

        elif template_name == 'compliance_violation':
            return self.create_alert(
                name='Trinity Compliance Violation Alert',
                alert_type='trinity_compliance',
                condition={
                    'field': 'compliance.bypass_warnings',
                    'operator': '>',
                    'value': params.get('threshold', 0)
                },
                severity='critical',
                metadata={'template': 'compliance_violation'}
            )

        elif template_name == 'graph_anomaly':
            return self.create_alert(
                name='Knowledge Graph Anomaly Alert',
                alert_type='knowledge_graph',
                condition={
                    'field': 'graph.growth_rate',
                    'operator': '>',
                    'value': params.get('threshold', 100)
                },
                severity='info',
                metadata={'template': 'graph_anomaly'}
            )

        else:
            raise ValueError(f"Unknown template: {template_name}")

    def _get_alert_data(self, alert_type: AlertType, runtime) -> Dict[str, Any]:
        """Get data for alert evaluation based on alert type"""
        data = {}

        if alert_type == AlertType.PATTERN:
            # Get pattern execution data
            if runtime and hasattr(runtime, 'execution_history'):
                exec_history = runtime.execution_history[-100:]  # Last 100
                success_count = sum(1 for e in exec_history if 'error' not in e.get('result', {}))
                data['pattern_execution'] = {
                    'success_rate': success_count / len(exec_history) if exec_history else 1.0,
                    'total_executions': len(exec_history)
                }

        elif alert_type == AlertType.DATA_QUALITY:
            # Get data quality metrics
            data_age = self._check_data_freshness(runtime)
            data.update(data_age)

        elif alert_type == AlertType.SYSTEM_HEALTH:
            # Get system health metrics
            if runtime:
                exec_history = runtime.execution_history[-50:] if hasattr(runtime, 'execution_history') else []
                data['system'] = {
                    'avg_response_time': 0.5,  # Estimated
                    'active_agents': len(runtime.agent_registry.agents) if hasattr(runtime, 'agent_registry') else 0
                }

        elif alert_type == AlertType.TRINITY_COMPLIANCE:
            # Get compliance metrics
            if runtime and hasattr(runtime, 'agent_registry'):
                bypass_warnings = runtime.agent_registry.get_bypass_warnings()
                data['compliance'] = {
                    'bypass_warnings': len(bypass_warnings),
                    'violations': len([b for b in bypass_warnings if 'BYPASS' in b.get('message', '')])
                }

        elif alert_type == AlertType.KNOWLEDGE_GRAPH:
            # Get graph metrics
            if runtime and hasattr(runtime, 'pattern_engine'):
                graph = runtime.pattern_engine.graph if hasattr(runtime.pattern_engine, 'graph') else None
                if graph and hasattr(graph, 'nodes'):
                    data['graph'] = {
                        'total_nodes': len(graph.nodes),
                        'growth_rate': 0  # Would track growth over time
                    }

        return data

    def _check_data_freshness(self, runtime) -> Dict[str, Any]:
        """Check freshness of various datasets"""
        freshness = {}

        # Check FRED data
        fred_file = Path('storage/knowledge/fred_economic_data.json')
        if fred_file.exists():
            age = (datetime.now() - datetime.fromtimestamp(fred_file.stat().st_mtime)).total_seconds() / 3600
            freshness['FRED'] = {'age_hours': age}

        # Check enriched data
        enriched_files = ['market_sectors.json', 'economic_cycles.json', 'sector_correlations.json']
        for filename in enriched_files:
            filepath = Path(f'storage/knowledge/{filename}')
            if filepath.exists():
                age = (datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)).total_seconds() / 3600
                dataset_name = filename.replace('.json', '').replace('_', ' ').title()
                freshness[dataset_name] = {'age_hours': age}

        return freshness

    def _generate_alert_message(self, alert: Alert, details: Dict[str, Any]) -> str:
        """Generate human-readable alert message"""
        condition = alert.condition

        # Extract actual value from details
        actual_value = condition._get_nested_value(details, condition.field)

        messages = {
            '>': f"{condition.field} ({actual_value}) exceeded threshold ({condition.value})",
            '<': f"{condition.field} ({actual_value}) fell below threshold ({condition.value})",
            '>=': f"{condition.field} ({actual_value}) is at or above threshold ({condition.value})",
            '<=': f"{condition.field} ({actual_value}) is at or below threshold ({condition.value})",
            '==': f"{condition.field} equals {condition.value}",
            '!=': f"{condition.field} ({actual_value}) differs from expected ({condition.value})",
            'contains': f"{condition.field} contains '{condition.value}'",
            'missing': f"{condition.field} is missing or unavailable"
        }

        base_message = messages.get(condition.operator, f"{condition.field} {condition.operator} {condition.value}")
        return f"{alert.name}: {base_message}"

    def _generate_alert_id(self, name: str) -> str:
        """Generate unique alert ID"""
        # Create ID from name and timestamp
        clean_name = re.sub(r'[^a-z0-9]', '_', name.lower())
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"alert_{clean_name}_{timestamp}"

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"event_{timestamp}"

    def _execute_callbacks(self, alert_type: str, event: AlertEvent):
        """Execute registered callbacks for alert type"""
        if alert_type in self.callbacks:
            for callback in self.callbacks[alert_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error executing callback for {alert_type}: {e}")

    def _load_alerts(self):
        """Load alerts from storage"""
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r') as f:
                    data = json.load(f)
                    self.alerts = {
                        alert_id: Alert.from_dict(alert_data)
                        for alert_id, alert_data in data.items()
                    }
            except Exception as e:
                print(f"Error loading alerts: {e}")
                self.alerts = {}

    def _save_alerts(self):
        """Save alerts to storage"""
        try:
            data = {
                alert_id: alert.to_dict()
                for alert_id, alert in self.alerts.items()
            }
            with open(self.alerts_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving alerts: {e}")

    def _load_history(self):
        """Load alert history from storage"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.history = [AlertEvent.from_dict(event_data) for event_data in data]
            except Exception as e:
                print(f"Error loading history: {e}")
                self.history = []

    def _save_history(self):
        """Save alert history to storage (keep last 1000)"""
        try:
            # Keep only last 1000 events
            history_to_save = self.history[-1000:]
            data = [event.to_dict() for event in history_to_save]

            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.history = history_to_save
        except Exception as e:
            print(f"Error saving history: {e}")

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts and recent activity"""
        active_alerts = self.get_active_alerts()
        triggered_alerts = self.get_triggered_alerts()
        recent_events = self.get_alert_history(limit=10)

        # Count by severity
        severity_counts = {
            'info': 0,
            'warning': 0,
            'critical': 0
        }

        for alert in self.alerts.values():
            severity_counts[alert.severity.value] += 1

        return {
            'total_alerts': len(self.alerts),
            'active_alerts': len(active_alerts),
            'triggered_alerts': len(triggered_alerts),
            'severity_counts': severity_counts,
            'recent_events': [e.to_dict() for e in recent_events],
            'unacknowledged_events': len([e for e in self.history if not e.acknowledged])
        }

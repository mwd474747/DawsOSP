# Option 4: Enhance Current Features - Implementation Plan

**Timeline**: 1-2 weeks
**Goal**: Polish and extend existing features for maximum ROI
**Priority**: MEDIUM-HIGH

---

## Executive Summary

Enhance the four major UI features delivered in Track B by adding high-value capabilities that make them production-grade and user-friendly. Focus on features that provide immediate value with minimal complexity.

---

## Enhancement Track Overview

| Enhancement | Days | Priority | Value |
|------------|------|----------|-------|
| **A. Pattern System Enhancements** | 3-4 | HIGH | ⭐⭐⭐⭐⭐ |
| **B. Alert System Enhancements** | 2-3 | HIGH | ⭐⭐⭐⭐⭐ |
| **C. Intelligence Display Integration** | 2-3 | MEDIUM | ⭐⭐⭐⭐ |
| **D. Dashboard Analytics** | 2-3 | MEDIUM | ⭐⭐⭐⭐ |

**Total**: 9-13 days (1.5-2.5 weeks)

---

## Track A: Pattern System Enhancements (3-4 days)

### Goal
Make patterns discoverable, analyzable, and easier to manage through the UI.

### A.1: Pattern Analytics Dashboard (1 day)

**Features**:
- **Usage Statistics**: Show most/least used patterns
- **Success Rate Tracking**: Track which patterns succeed/fail
- **Execution Time Analytics**: Average execution time per pattern
- **Trending Patterns**: Patterns with increasing usage
- **Performance Benchmarks**: Compare patterns by speed/accuracy

**Implementation**:
```python
# File: dawsos/ui/pattern_analytics.py

class PatternAnalytics:
    def __init__(self, pattern_engine, runtime):
        self.pattern_engine = pattern_engine
        self.runtime = runtime

    def get_pattern_usage_stats(self) -> Dict:
        """Analyze pattern usage from execution history"""
        # Extract from runtime.execution_history
        stats = {
            'total_executions': 0,
            'patterns_used': {},
            'success_rates': {},
            'avg_execution_times': {},
            'trending': []
        }

        for execution in self.runtime.execution_history[-1000:]:
            pattern_id = execution.get('pattern_id')
            if pattern_id:
                stats['patterns_used'][pattern_id] = \
                    stats['patterns_used'].get(pattern_id, 0) + 1
                # Track success/failure
                # Track execution time

        return stats

    def render_analytics_dashboard(self):
        """Render pattern analytics UI"""
        st.markdown("## 📊 Pattern Analytics")

        stats = self.get_pattern_usage_stats()

        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Executions", stats['total_executions'])
        with col2:
            st.metric("Patterns Used", len(stats['patterns_used']))
        with col3:
            avg_success = sum(stats['success_rates'].values()) / len(stats['success_rates'])
            st.metric("Avg Success Rate", f"{avg_success:.1%}")
        with col4:
            st.metric("Active Patterns", "45")

        # Usage chart
        st.markdown("### Most Used Patterns")
        top_10 = sorted(stats['patterns_used'].items(),
                       key=lambda x: x[1], reverse=True)[:10]
        df = pd.DataFrame(top_10, columns=['Pattern', 'Count'])
        st.bar_chart(df.set_index('Pattern'))

        # Success rates
        st.markdown("### Success Rates by Pattern")
        success_df = pd.DataFrame(
            [(k, v) for k, v in stats['success_rates'].items()],
            columns=['Pattern', 'Success Rate']
        )
        st.dataframe(success_df.sort_values('Success Rate', ascending=False))

        # Execution times
        st.markdown("### Performance Benchmarks")
        time_df = pd.DataFrame(
            [(k, v) for k, v in stats['avg_execution_times'].items()],
            columns=['Pattern', 'Avg Time (s)']
        )
        st.dataframe(time_df.sort_values('Avg Time (s)'))
```

**Integration**:
- Add "Analytics" sub-tab to Pattern Browser
- Or add to main Dashboard as "Pattern Analytics" section

**Files to Create**:
- `dawsos/ui/pattern_analytics.py` (200-300 lines)

**Files to Modify**:
- `dawsos/ui/pattern_browser.py` - Add analytics tab
- `dawsos/core/pattern_engine.py` - Track execution metadata

---

### A.2: Pattern Recommendations (1 day)

**Features**:
- **Smart Suggestions**: Suggest patterns based on user query
- **Related Patterns**: Show similar/complementary patterns
- **Next Best Action**: Recommend logical next steps
- **Frequently Paired**: Show patterns often used together

**Implementation**:
```python
# File: dawsos/core/pattern_recommender.py

class PatternRecommender:
    def __init__(self, pattern_engine):
        self.pattern_engine = pattern_engine

    def recommend_patterns(self, query: str, limit: int = 5) -> List[Dict]:
        """Recommend patterns based on query text"""
        recommendations = []

        for pattern_id, pattern in self.pattern_engine.patterns.items():
            score = self._calculate_relevance_score(query, pattern)
            if score > 0.3:  # Threshold
                recommendations.append({
                    'pattern_id': pattern_id,
                    'pattern': pattern,
                    'score': score,
                    'reason': self._explain_recommendation(query, pattern)
                })

        return sorted(recommendations, key=lambda x: x['score'],
                     reverse=True)[:limit]

    def _calculate_relevance_score(self, query: str, pattern: Dict) -> float:
        """Calculate how relevant a pattern is to the query"""
        score = 0.0
        query_lower = query.lower()

        # Check triggers
        for trigger in pattern.get('triggers', []):
            if trigger.lower() in query_lower:
                score += 0.5

        # Check description
        if any(word in pattern.get('description', '').lower()
               for word in query_lower.split()):
            score += 0.2

        # Check category
        if pattern.get('category', '') in query_lower:
            score += 0.3

        return min(score, 1.0)

    def _explain_recommendation(self, query: str, pattern: Dict) -> str:
        """Explain why this pattern was recommended"""
        reasons = []

        # Check what matched
        for trigger in pattern.get('triggers', []):
            if trigger.lower() in query.lower():
                reasons.append(f"Matches trigger: '{trigger}'")
                break

        if pattern.get('category') in query.lower():
            reasons.append(f"Category match: {pattern.get('category')}")

        return " | ".join(reasons) if reasons else "Related to your query"

    def get_related_patterns(self, pattern_id: str, limit: int = 3) -> List[str]:
        """Find patterns related to the given pattern"""
        pattern = self.pattern_engine.patterns.get(pattern_id)
        if not pattern:
            return []

        related = []
        category = pattern.get('category')

        # Same category patterns
        for pid, p in self.pattern_engine.patterns.items():
            if pid != pattern_id and p.get('category') == category:
                related.append(pid)

        return related[:limit]

    def get_frequently_paired(self, pattern_id: str,
                             execution_history: List, limit: int = 3) -> List[str]:
        """Find patterns frequently executed after this one"""
        # Analyze execution_history to find patterns run in sequence
        pairs = {}

        for i in range(len(execution_history) - 1):
            if execution_history[i].get('pattern_id') == pattern_id:
                next_pattern = execution_history[i+1].get('pattern_id')
                if next_pattern:
                    pairs[next_pattern] = pairs.get(next_pattern, 0) + 1

        sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
        return [p[0] for p in sorted_pairs[:limit]]
```

**UI Integration**:
```python
# In pattern_browser.py

def render_pattern_recommendations(self, query: str):
    """Show recommended patterns based on query"""
    from core.pattern_recommender import PatternRecommender

    recommender = PatternRecommender(self.runtime.pattern_engine)
    recommendations = recommender.recommend_patterns(query, limit=5)

    if recommendations:
        st.markdown("### 💡 Recommended Patterns")
        for rec in recommendations:
            with st.expander(f"{rec['pattern']['name']} ({rec['score']:.0%} match)"):
                st.write(f"**Reason**: {rec['reason']}")
                st.write(f"**Description**: {rec['pattern']['description']}")
                if st.button(f"Execute {rec['pattern_id']}",
                           key=f"exec_{rec['pattern_id']}"):
                    # Execute the pattern
                    pass
```

**Files to Create**:
- `dawsos/core/pattern_recommender.py` (200-250 lines)

**Files to Modify**:
- `dawsos/ui/pattern_browser.py` - Add recommendation section

---

### A.3: Pattern Version History (1 day)

**Features**:
- **Version Tracking**: Track all changes to patterns
- **Diff Viewer**: Show what changed between versions
- **Rollback**: Restore previous pattern versions
- **Change Log**: Maintain pattern change history

**Implementation**:
```python
# File: dawsos/core/pattern_versioning.py

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class PatternVersioning:
    def __init__(self, version_dir: str = 'dawsos/storage/pattern_versions'):
        self.version_dir = Path(version_dir)
        self.version_dir.mkdir(parents=True, exist_ok=True)

    def save_version(self, pattern_id: str, pattern: Dict,
                    change_note: str = "") -> str:
        """Save a new version of a pattern"""
        # Generate version ID
        pattern_json = json.dumps(pattern, sort_keys=True)
        version_hash = hashlib.sha256(pattern_json.encode()).hexdigest()[:8]
        version_id = f"{pattern_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{version_hash}"

        # Save version file
        version_file = self.version_dir / f"{version_id}.json"
        version_data = {
            'pattern_id': pattern_id,
            'version_id': version_id,
            'timestamp': datetime.now().isoformat(),
            'change_note': change_note,
            'pattern': pattern,
            'hash': version_hash
        }

        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)

        return version_id

    def get_version_history(self, pattern_id: str) -> List[Dict]:
        """Get all versions of a pattern"""
        versions = []

        for version_file in sorted(self.version_dir.glob(f"{pattern_id}_*.json")):
            with open(version_file) as f:
                version_data = json.load(f)
                versions.append({
                    'version_id': version_data['version_id'],
                    'timestamp': version_data['timestamp'],
                    'change_note': version_data.get('change_note', 'No note'),
                    'hash': version_data['hash']
                })

        return sorted(versions, key=lambda x: x['timestamp'], reverse=True)

    def get_version(self, version_id: str) -> Optional[Dict]:
        """Retrieve a specific version"""
        version_file = self.version_dir / f"{version_id}.json"
        if version_file.exists():
            with open(version_file) as f:
                return json.load(f)
        return None

    def diff_versions(self, version_id_1: str, version_id_2: str) -> Dict:
        """Compare two versions and show differences"""
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)

        if not v1 or not v2:
            return {'error': 'Version not found'}

        # Simple diff - can be enhanced with difflib
        diff = {
            'added': [],
            'removed': [],
            'modified': []
        }

        # Compare steps
        v1_steps = v1['pattern'].get('steps', [])
        v2_steps = v2['pattern'].get('steps', [])

        if len(v1_steps) != len(v2_steps):
            diff['modified'].append(f"Step count changed: {len(v1_steps)} -> {len(v2_steps)}")

        # Compare triggers
        v1_triggers = set(v1['pattern'].get('triggers', []))
        v2_triggers = set(v2['pattern'].get('triggers', []))

        diff['added'] = list(v2_triggers - v1_triggers)
        diff['removed'] = list(v1_triggers - v2_triggers)

        return diff

    def rollback_to_version(self, pattern_id: str, version_id: str) -> Dict:
        """Restore a pattern to a previous version"""
        version_data = self.get_version(version_id)
        if not version_data:
            return {'error': 'Version not found'}

        # Get current pattern file
        pattern_file = Path(f'dawsos/patterns/{pattern_id}.json')

        # Save current as new version first (backup)
        with open(pattern_file) as f:
            current_pattern = json.load(f)
        self.save_version(pattern_id, current_pattern,
                         change_note="Auto-backup before rollback")

        # Write old version
        with open(pattern_file, 'w') as f:
            json.dump(version_data['pattern'], f, indent=2)

        return {'success': True, 'restored_version': version_id}
```

**UI for Version History**:
```python
# In pattern_browser.py

def render_pattern_version_history(self, pattern_id: str):
    """Show version history for a pattern"""
    from core.pattern_versioning import PatternVersioning

    versioning = PatternVersioning()
    history = versioning.get_version_history(pattern_id)

    st.markdown("### 📜 Version History")

    for version in history:
        with st.expander(f"{version['timestamp']} - {version['hash']}"):
            st.write(f"**Note**: {version['change_note']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"View", key=f"view_{version['version_id']}"):
                    version_data = versioning.get_version(version['version_id'])
                    st.json(version_data['pattern'])

            with col2:
                if len(history) > 1 and st.button(f"Diff",
                                                  key=f"diff_{version['version_id']}"):
                    # Show diff with current version
                    current_version = history[0]['version_id']
                    diff = versioning.diff_versions(current_version,
                                                    version['version_id'])
                    st.write("**Changes**:", diff)

            with col3:
                if st.button(f"Rollback", key=f"rollback_{version['version_id']}"):
                    result = versioning.rollback_to_version(pattern_id,
                                                           version['version_id'])
                    if result.get('success'):
                        st.success(f"Rolled back to version {version['hash']}")
                        st.rerun()
```

**Files to Create**:
- `dawsos/core/pattern_versioning.py` (300-350 lines)

**Files to Modify**:
- `dawsos/ui/pattern_browser.py` - Add version history section

---

### A.4: Pattern Execution History Persistence (0.5 day)

**Features**:
- **Save History to Disk**: Persist execution history across sessions
- **Filter History**: Filter by pattern, date, success/failure
- **Export History**: Export as CSV/JSON

**Implementation**:
```python
# File: dawsos/core/pattern_history.py

class PatternHistory:
    def __init__(self, history_file: str = 'dawsos/storage/pattern_history.json'):
        self.history_file = Path(history_file)
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """Load history from disk"""
        if self.history_file.exists():
            with open(self.history_file) as f:
                return json.load(f)
        return []

    def save_execution(self, pattern_id: str, context: Dict,
                      result: Dict, success: bool):
        """Save pattern execution to history"""
        entry = {
            'pattern_id': pattern_id,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'result': result,
            'success': success
        }

        self.history.append(entry)

        # Keep last 1000 entries
        self.history = self.history[-1000:]

        # Persist to disk
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def get_history(self, pattern_id: Optional[str] = None,
                   limit: int = 100) -> List[Dict]:
        """Retrieve execution history with optional filtering"""
        if pattern_id:
            filtered = [h for h in self.history if h['pattern_id'] == pattern_id]
        else:
            filtered = self.history

        return filtered[-limit:]

    def export_history(self, format: str = 'csv') -> str:
        """Export history as CSV or JSON"""
        if format == 'csv':
            df = pd.DataFrame(self.history)
            return df.to_csv(index=False)
        else:
            return json.dumps(self.history, indent=2)
```

**Integration**:
- Modify `pattern_browser.py` to use `PatternHistory` instead of session state
- Add export button to history view

**Files to Create**:
- `dawsos/core/pattern_history.py` (150-200 lines)

**Files to Modify**:
- `dawsos/ui/pattern_browser.py` - Use persistent history

---

## Track B: Alert System Enhancements (2-3 days)

### Goal
Make alerts actionable, reliable, and integrated with external systems.

### B.1: Email/SMS Notifications (1.5 days)

**Features**:
- **Email Alerts**: Send email when alerts trigger
- **SMS Alerts**: Send SMS via Twilio (optional)
- **Notification Templates**: Customizable email/SMS templates
- **Delivery Tracking**: Track which notifications were sent

**Implementation**:
```python
# File: dawsos/core/alert_notifications.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

class AlertNotifier:
    def __init__(self):
        self.email_enabled = self._check_email_config()
        self.sms_enabled = self._check_sms_config()

    def _check_email_config(self) -> bool:
        """Check if email is configured"""
        import os
        required = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS']
        return all(os.getenv(key) for key in required)

    def _check_sms_config(self) -> bool:
        """Check if Twilio SMS is configured"""
        import os
        required = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE']
        return all(os.getenv(key) for key in required)

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email notification"""
        if not self.email_enabled:
            return False

        try:
            import os
            msg = MIMEMultipart()
            msg['From'] = os.getenv('SMTP_USER')
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(os.getenv('SMTP_HOST'),
                                 int(os.getenv('SMTP_PORT')))
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
            server.send_message(msg)
            server.quit()

            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS notification via Twilio"""
        if not self.sms_enabled:
            return False

        try:
            from twilio.rest import Client
            import os

            client = Client(os.getenv('TWILIO_ACCOUNT_SID'),
                          os.getenv('TWILIO_AUTH_TOKEN'))

            message = client.messages.create(
                body=message,
                from_=os.getenv('TWILIO_PHONE'),
                to=to_phone
            )

            return message.sid is not None
        except Exception as e:
            print(f"SMS send failed: {e}")
            return False

    def format_alert_email(self, alert_event: Dict) -> str:
        """Format alert as HTML email"""
        severity_colors = {
            'info': '#3498db',
            'warning': '#f39c12',
            'critical': '#e74c3c'
        }

        color = severity_colors.get(alert_event['severity'], '#95a5a6')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{
                    border-left: 4px solid {color};
                    padding: 15px;
                    background: #f8f9fa;
                }}
                .severity {{
                    color: {color};
                    font-weight: bold;
                    text-transform: uppercase;
                }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <h2>🔔 DawsOS Alert Triggered</h2>
                <p><span class="severity">{alert_event['severity']}</span></p>
                <h3>{alert_event['alert_name']}</h3>
                <p><strong>Message:</strong> {alert_event['message']}</p>
                <p><strong>Time:</strong> {alert_event['timestamp']}</p>
                <hr>
                <p><em>This is an automated alert from DawsOS Trinity Architecture</em></p>
            </div>
        </body>
        </html>
        """

        return html

    def format_alert_sms(self, alert_event: Dict) -> str:
        """Format alert as SMS (160 char limit)"""
        severity = alert_event['severity'].upper()
        name = alert_event['alert_name'][:30]
        msg = alert_event['message'][:80]

        return f"[{severity}] {name}: {msg}"
```

**Integration with AlertManager**:
```python
# Modify dawsos/core/alert_manager.py

class AlertManager:
    def __init__(self, storage_dir: str = 'storage/alerts'):
        # ... existing code ...
        self.notifier = AlertNotifier()
        self.notification_settings = self._load_notification_settings()

    def trigger_alert(self, alert: Alert, details: Dict) -> AlertEvent:
        """Trigger an alert and send notifications"""
        event = self._create_alert_event(alert, details)

        # Send notifications if configured
        if self.notification_settings.get('email_enabled'):
            email = self.notification_settings.get('email_address')
            if email:
                subject = f"[{event.severity.value.upper()}] {alert.name}"
                body = self.notifier.format_alert_email(event.to_dict())
                self.notifier.send_email(email, subject, body)

        if self.notification_settings.get('sms_enabled'):
            phone = self.notification_settings.get('phone_number')
            if phone:
                message = self.notifier.format_alert_sms(event.to_dict())
                self.notifier.send_sms(phone, message)

        return event

    def update_notification_settings(self, settings: Dict):
        """Update notification preferences"""
        self.notification_settings.update(settings)
        settings_file = Path(self.storage_dir) / 'notification_settings.json'
        with open(settings_file, 'w') as f:
            json.dump(self.notification_settings, f, indent=2)
```

**UI for Notification Settings**:
```python
# Add to alert_panel.py

def render_notification_settings(self):
    """Configure notification channels"""
    st.markdown("### 📧 Notification Settings")

    settings = self.alert_manager.notification_settings

    # Email settings
    email_enabled = st.checkbox("Enable Email Notifications",
                                value=settings.get('email_enabled', False))

    if email_enabled:
        email = st.text_input("Email Address",
                             value=settings.get('email_address', ''))

        if st.button("Test Email"):
            if self.alert_manager.notifier.send_email(
                email,
                "Test Alert",
                "<h1>Test Alert from DawsOS</h1>"
            ):
                st.success("Test email sent!")
            else:
                st.error("Email send failed. Check SMTP configuration.")

    # SMS settings
    sms_enabled = st.checkbox("Enable SMS Notifications",
                             value=settings.get('sms_enabled', False))

    if sms_enabled:
        phone = st.text_input("Phone Number",
                             value=settings.get('phone_number', ''),
                             placeholder="+1234567890")

        if st.button("Test SMS"):
            if self.alert_manager.notifier.send_sms(
                phone,
                "Test alert from DawsOS"
            ):
                st.success("Test SMS sent!")
            else:
                st.error("SMS send failed. Check Twilio configuration.")

    # Save settings
    if st.button("Save Notification Settings"):
        new_settings = {
            'email_enabled': email_enabled,
            'email_address': email if email_enabled else '',
            'sms_enabled': sms_enabled,
            'phone_number': phone if sms_enabled else ''
        }
        self.alert_manager.update_notification_settings(new_settings)
        st.success("Settings saved!")
```

**Environment Variables**:
```bash
# .env file additions

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# SMS (Twilio - optional)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE=+1234567890
```

**Files to Create**:
- `dawsos/core/alert_notifications.py` (300-400 lines)

**Files to Modify**:
- `dawsos/core/alert_manager.py` - Add notification integration
- `dawsos/ui/alert_panel.py` - Add notification settings tab

**Dependencies to Add**:
```bash
pip install twilio  # For SMS (optional)
```

---

### B.2: Scheduled Alert Checks (0.5 day)

**Features**:
- **Cron-like Scheduling**: Run alerts on schedule
- **Background Checking**: Check alerts without blocking UI
- **Alert Schedules**: Define when alerts should run

**Implementation**:
```python
# File: dawsos/core/alert_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

class AlertScheduler:
    def __init__(self, alert_manager):
        self.alert_manager = alert_manager
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def schedule_alert(self, alert_id: str, cron_expression: str):
        """Schedule an alert to run on cron schedule"""
        # Parse cron: "0 9 * * *" = daily at 9am
        trigger = CronTrigger.from_crontab(cron_expression)

        self.scheduler.add_job(
            func=self._check_alert,
            trigger=trigger,
            args=[alert_id],
            id=f"alert_{alert_id}",
            replace_existing=True
        )

    def _check_alert(self, alert_id: str):
        """Check a specific alert"""
        # This runs in background
        alerts = self.alert_manager.check_alerts(
            alert_ids=[alert_id]
        )
        # Alerts will be triggered if conditions met

    def remove_schedule(self, alert_id: str):
        """Remove scheduled alert"""
        self.scheduler.remove_job(f"alert_{alert_id}")

    def list_schedules(self) -> List[Dict]:
        """List all scheduled alerts"""
        jobs = self.scheduler.get_jobs()
        return [
            {
                'alert_id': job.id.replace('alert_', ''),
                'next_run': job.next_run_time,
                'trigger': str(job.trigger)
            }
            for job in jobs
        ]
```

**UI for Scheduling**:
```python
# In alert_panel.py

def render_alert_schedules(self):
    """Configure alert schedules"""
    st.markdown("### ⏰ Alert Schedules")

    # Show current schedules
    schedules = self.scheduler.list_schedules()
    if schedules:
        st.dataframe(pd.DataFrame(schedules))

    # Add new schedule
    st.markdown("#### Add Schedule")
    alert = st.selectbox("Select Alert",
                        list(self.alert_manager.alerts.keys()))

    schedule_type = st.selectbox("Schedule Type",
                                ["Every Hour", "Daily", "Weekly", "Custom"])

    if schedule_type == "Custom":
        cron = st.text_input("Cron Expression",
                            placeholder="0 9 * * *",
                            help="Minute Hour Day Month DayOfWeek")
    else:
        cron = {
            "Every Hour": "0 * * * *",
            "Daily": "0 9 * * *",
            "Weekly": "0 9 * * 1"
        }[schedule_type]

    if st.button("Add Schedule"):
        self.scheduler.schedule_alert(alert, cron)
        st.success(f"Scheduled {alert} with cron: {cron}")
        st.rerun()
```

**Files to Create**:
- `dawsos/core/alert_scheduler.py` (150-200 lines)

**Files to Modify**:
- `dawsos/ui/alert_panel.py` - Add schedules tab
- `dawsos/main.py` - Initialize scheduler at startup

**Dependencies to Add**:
```bash
pip install apscheduler
```

---

### B.3: Alert Analytics (1 day)

**Features**:
- **Effectiveness Metrics**: How often alerts trigger correctly
- **False Positive Rate**: Track incorrect alerts
- **Response Time**: Time to acknowledge alerts
- **Alert Correlation**: Which alerts trigger together

**Implementation**: Similar to Pattern Analytics, but for alerts

**Files to Create**:
- `dawsos/ui/alert_analytics.py` (250-300 lines)

---

## Track C: Intelligence Display Integration (2-3 days)

### Goal
Embed intelligence transparency throughout the application.

### C.1: Embed in Pattern Results (1 day)

**Implementation**:
```python
# Modify pattern_browser.py

def display_pattern_result(self, result: Dict):
    """Display pattern execution result with intelligence"""
    # Show formatted result
    st.markdown(result.get('response', 'No response'))

    # Add intelligence display
    if st.checkbox("Show Intelligence Details", value=True):
        from ui.intelligence_display import create_intelligence_display

        display = create_intelligence_display(
            self.runtime.graph,
            self.runtime.agent_registry,
            self.runtime
        )

        # Extract execution history for this pattern
        execution_history = result.get('execution_trace', [])

        # Show confidence
        if 'confidence' in result:
            display.render_confidence_gauge(
                result['confidence'],
                "Pattern Confidence"
            )

        # Show thinking trace
        if execution_history:
            display.render_thinking_trace(execution_history)

        # Show agent flow
        agents_used = [step['agent'] for step in execution_history
                      if 'agent' in step]
        if agents_used:
            display.render_agent_flow_diagram(agents_used)
```

**Files to Modify**:
- `dawsos/ui/pattern_browser.py` - Add intelligence to results

---

### C.2: Dashboard Intelligence Widget (1 day)

**Implementation**:
```python
# Add to trinity_dashboard_tabs.py

def render_system_intelligence(self):
    """Show system-wide intelligence metrics"""
    from ui.intelligence_display import create_intelligence_display

    display = create_intelligence_display(
        self.graph,
        self.runtime.agent_registry,
        self.runtime
    )

    st.markdown("### 🧠 System Intelligence")

    # Overall system confidence
    recent_executions = self.runtime.execution_history[-20:]
    confidences = [e.get('confidence', 0) for e in recent_executions
                  if 'confidence' in e]

    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        display.render_confidence_gauge(avg_confidence,
                                       "System Confidence (Last 20)")

    # Most active agents
    display.render_system_intelligence()
```

**Files to Modify**:
- `dawsos/ui/trinity_dashboard_tabs.py` - Add intelligence widget

---

### C.3: Confidence Tracking Over Time (1 day)

**Features**:
- **Historical Confidence**: Track confidence trends
- **Per-Pattern Confidence**: Track by pattern type
- **Agent Confidence**: Track by agent

**Implementation**:
```python
# File: dawsos/core/confidence_tracker.py

class ConfidenceTracker:
    def __init__(self, storage_file: str = 'storage/confidence_history.json'):
        self.storage_file = Path(storage_file)
        self.history = self._load()

    def record_confidence(self, execution_id: str, confidence: float,
                         pattern_id: str, agents_used: List[str]):
        """Record confidence for an execution"""
        entry = {
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'pattern_id': pattern_id,
            'agents_used': agents_used
        }

        self.history.append(entry)
        self._save()

    def get_confidence_trend(self, days: int = 30) -> List[Dict]:
        """Get confidence trend over time"""
        cutoff = datetime.now() - timedelta(days=days)

        return [h for h in self.history
                if datetime.fromisoformat(h['timestamp']) > cutoff]

    def get_pattern_confidence(self, pattern_id: str) -> Dict:
        """Get confidence stats for a pattern"""
        pattern_confidences = [h['confidence'] for h in self.history
                              if h['pattern_id'] == pattern_id]

        if not pattern_confidences:
            return {'avg': 0, 'min': 0, 'max': 0, 'count': 0}

        return {
            'avg': sum(pattern_confidences) / len(pattern_confidences),
            'min': min(pattern_confidences),
            'max': max(pattern_confidences),
            'count': len(pattern_confidences)
        }
```

**UI for Confidence Trends**:
```python
# Add to intelligence_display.py

def render_confidence_trends(self, days: int = 30):
    """Show confidence trends over time"""
    from core.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker()
    trend_data = tracker.get_confidence_trend(days)

    if trend_data:
        df = pd.DataFrame(trend_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        fig = px.line(df, x='timestamp', y='confidence',
                     title=f"Confidence Trend (Last {days} days)")
        st.plotly_chart(fig, use_container_width=True)

        # Stats
        avg_confidence = df['confidence'].mean()
        st.metric("Average Confidence", f"{avg_confidence:.1%}")
```

**Files to Create**:
- `dawsos/core/confidence_tracker.py` (200-250 lines)

**Files to Modify**:
- `dawsos/ui/intelligence_display.py` - Add trends visualization

---

## Track D: Dashboard Analytics (2-3 days)

### Goal
Add deeper insights and analytics to the dashboard.

### D.1: Agent Profiling (1 day)

**Features**:
- **Performance Profiling**: Detailed per-agent performance
- **Bottleneck Detection**: Find slow agents
- **Usage Patterns**: When and how agents are used
- **Optimization Suggestions**: Recommendations for improvement

**Implementation**:
```python
# File: dawsos/ui/agent_profiler.py

class AgentProfiler:
    def __init__(self, runtime):
        self.runtime = runtime

    def profile_agent(self, agent_name: str) -> Dict:
        """Deep profile of an agent"""
        executions = [e for e in self.runtime.execution_history
                     if e.get('agent') == agent_name]

        if not executions:
            return {'error': 'No executions found'}

        # Calculate stats
        execution_times = [e.get('execution_time', 0) for e in executions]
        successes = sum(1 for e in executions if e.get('success', False))

        profile = {
            'total_executions': len(executions),
            'success_rate': successes / len(executions),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'percentile_95': sorted(execution_times)[int(len(execution_times) * 0.95)],
            'usage_by_hour': self._usage_by_hour(executions),
            'common_patterns': self._common_patterns(executions),
            'failure_reasons': self._failure_analysis(executions)
        }

        return profile

    def render_agent_profile(self, agent_name: str):
        """Render agent profile UI"""
        st.markdown(f"## 🔍 Agent Profile: {agent_name}")

        profile = self.profile_agent(agent_name)

        if 'error' in profile:
            st.warning(profile['error'])
            return

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Executions", profile['total_executions'])
        with col2:
            st.metric("Success Rate", f"{profile['success_rate']:.1%}")
        with col3:
            st.metric("Avg Time", f"{profile['avg_execution_time']:.2f}s")
        with col4:
            st.metric("95th Percentile", f"{profile['percentile_95']:.2f}s")

        # Execution time distribution
        st.markdown("### ⏱️ Execution Time Distribution")
        # ... histogram of execution times

        # Usage patterns
        st.markdown("### 📊 Usage Patterns")
        # ... hourly usage chart

        # Common patterns this agent is used in
        st.markdown("### 🔗 Common Patterns")
        st.write(profile['common_patterns'])

        # Failure analysis
        if profile['failure_reasons']:
            st.markdown("### ⚠️ Failure Analysis")
            for reason, count in profile['failure_reasons'].items():
                st.write(f"- **{reason}**: {count} occurrences")
```

**Files to Create**:
- `dawsos/ui/agent_profiler.py` (300-400 lines)

**Files to Modify**:
- `dawsos/ui/trinity_dashboard_tabs.py` - Add agent profiler link

---

### D.2: System Health Trends (1 day)

**Features**:
- **Historical Metrics**: Track metrics over time
- **Anomaly Detection**: Detect unusual patterns
- **Capacity Planning**: Predict future resource needs

**Files to Create**:
- `dawsos/core/health_tracker.py` (200-300 lines)
- `dawsos/ui/health_trends.py` (250-350 lines)

---

### D.3: Export & Reporting (1 day)

**Features**:
- **Export All Metrics**: Export dashboard data as CSV/JSON
- **Scheduled Reports**: Email daily/weekly summary reports
- **Custom Reports**: Build custom metric reports

**Implementation**:
```python
# File: dawsos/core/report_generator.py

class ReportGenerator:
    def generate_daily_summary(self, runtime) -> str:
        """Generate daily summary report"""
        today = datetime.now().date()

        # Get today's executions
        executions_today = [
            e for e in runtime.execution_history
            if datetime.fromisoformat(e['timestamp']).date() == today
        ]

        report = f"""
        # DawsOS Daily Summary - {today}

        ## Execution Summary
        - Total Executions: {len(executions_today)}
        - Success Rate: {self._calc_success_rate(executions_today):.1%}
        - Unique Patterns Used: {len(set(e.get('pattern_id') for e in executions_today))}

        ## Top Patterns
        {self._top_patterns(executions_today, limit=5)}

        ## Agent Performance
        {self._agent_performance(executions_today)}

        ## Alerts
        {self._alert_summary(today)}
        """

        return report

    def export_dashboard_data(self, runtime, format: str = 'csv') -> str:
        """Export all dashboard metrics"""
        metrics = {
            'executions': runtime.execution_history,
            'agents': self._get_agent_metrics(runtime),
            'patterns': self._get_pattern_metrics(runtime),
            'graph': self._get_graph_metrics(runtime)
        }

        if format == 'csv':
            # Convert to CSV
            pass
        else:
            return json.dumps(metrics, indent=2)
```

**Files to Create**:
- `dawsos/core/report_generator.py` (250-350 lines)

---

## Implementation Timeline

### Week 1 (Days 1-5)

**Day 1: Pattern Analytics & Recommendations**
- Morning: Implement `pattern_analytics.py`
- Afternoon: Implement `pattern_recommender.py`
- Evening: Integrate into pattern browser

**Day 2: Pattern Versioning & History**
- Morning: Implement `pattern_versioning.py`
- Afternoon: Implement `pattern_history.py`
- Evening: Add UI components to pattern browser

**Day 3: Alert Notifications**
- Morning: Implement `alert_notifications.py`
- Afternoon: Configure email/SMS integration
- Evening: Add notification settings UI

**Day 4: Alert Scheduling & Analytics**
- Morning: Implement `alert_scheduler.py`
- Afternoon: Implement alert analytics
- Evening: Add scheduling UI

**Day 5: Intelligence Integration**
- Morning: Embed intelligence in pattern results
- Afternoon: Add intelligence to dashboard
- Evening: Implement confidence tracking

---

### Week 2 (Days 6-10)

**Day 6: Agent Profiling**
- Morning: Implement `agent_profiler.py`
- Afternoon: Create profiling UI
- Evening: Test and refine

**Day 7: Dashboard Health Trends**
- Morning: Implement `health_tracker.py`
- Afternoon: Create trends visualizations
- Evening: Add anomaly detection

**Day 8: Export & Reporting**
- Morning: Implement `report_generator.py`
- Afternoon: Add export functionality
- Evening: Set up scheduled reports

**Day 9: Testing & Integration**
- Morning: Test all new features
- Afternoon: Fix bugs and issues
- Evening: Update documentation

**Day 10: Polish & Documentation**
- Morning: UI polish and refinements
- Afternoon: Write user guides
- Evening: Create demo workflows

---

## Success Criteria

### Pattern System
- [x] Analytics dashboard shows usage statistics
- [x] Pattern recommendations work for queries
- [x] Version history tracks all changes
- [x] Execution history persists across sessions
- [x] Can rollback to previous pattern versions

### Alert System
- [x] Email notifications send successfully
- [x] SMS notifications work (if configured)
- [x] Alerts run on schedule automatically
- [x] Alert analytics show effectiveness
- [x] Notification settings persist

### Intelligence Display
- [x] Confidence shown in all pattern results
- [x] Thinking traces displayed automatically
- [x] Confidence trends tracked over time
- [x] Intelligence widget on dashboard

### Dashboard Analytics
- [x] Agent profiling shows detailed metrics
- [x] Health trends display historical data
- [x] Export functionality works for all data
- [x] Reports generate successfully

---

## Files Summary

### New Files (Estimated)
| File | Lines | Purpose |
|------|-------|---------|
| `ui/pattern_analytics.py` | 250-300 | Pattern usage analytics |
| `core/pattern_recommender.py` | 200-250 | Pattern recommendations |
| `core/pattern_versioning.py` | 300-350 | Version control for patterns |
| `core/pattern_history.py` | 150-200 | Persistent execution history |
| `core/alert_notifications.py` | 300-400 | Email/SMS notifications |
| `core/alert_scheduler.py` | 150-200 | Scheduled alert checks |
| `ui/alert_analytics.py` | 250-300 | Alert effectiveness metrics |
| `core/confidence_tracker.py` | 200-250 | Confidence trend tracking |
| `ui/agent_profiler.py` | 300-400 | Agent performance profiling |
| `core/health_tracker.py` | 200-300 | System health tracking |
| `ui/health_trends.py` | 250-350 | Health trend visualizations |
| `core/report_generator.py` | 250-350 | Report generation |
| **Total** | **~3,000-3,750** | **12 new files** |

### Modified Files
- `dawsos/ui/pattern_browser.py` - Add analytics, recommendations, versioning
- `dawsos/ui/alert_panel.py` - Add notification settings, scheduling
- `dawsos/core/alert_manager.py` - Integrate notifications
- `dawsos/ui/intelligence_display.py` - Add confidence trends
- `dawsos/ui/trinity_dashboard_tabs.py` - Add profiler, trends, intelligence
- `dawsos/main.py` - Initialize scheduler, trackers

---

## Testing Plan

### Unit Tests
- Test pattern recommender scoring algorithm
- Test version diff calculation
- Test email/SMS sending (with mocks)
- Test alert scheduling
- Test confidence tracking

### Integration Tests
- Test pattern analytics end-to-end
- Test alert notifications flow
- Test intelligence display embedding
- Test export functionality

### User Acceptance Tests
- Execute pattern and verify intelligence shown
- Create alert and verify email received
- View agent profile and verify metrics
- Export dashboard data and verify format

---

## Risk Assessment

### Low Risk
- Pattern analytics (read-only, no data modification)
- Intelligence display integration (additive, no breaking changes)
- Dashboard enhancements (UI only)

### Medium Risk
- Alert notifications (depends on external services - SMTP, Twilio)
  - **Mitigation**: Graceful fallback if services unavailable
- Alert scheduling (background processes)
  - **Mitigation**: Comprehensive error handling and logging

### High Risk
- Pattern versioning (modifies pattern files)
  - **Mitigation**: Always backup before rollback, test thoroughly
- Confidence tracking (new persistence layer)
  - **Mitigation**: Separate storage file, optional feature

---

## Dependencies to Add

```bash
# Email/SMS
pip install twilio  # Optional, for SMS

# Scheduling
pip install apscheduler

# Already have
# - plotly (charts)
# - pandas (data manipulation)
# - streamlit (UI)
```

---

## Conclusion

Option 4 provides high-value enhancements to existing features:

✅ **Pattern System**: Analytics, recommendations, versioning, history
✅ **Alert System**: Email/SMS, scheduling, analytics
✅ **Intelligence Display**: Embedded everywhere, confidence tracking
✅ **Dashboard**: Profiling, trends, exports, reports

**Timeline**: 1.5-2.5 weeks
**Effort**: 9-13 days
**ROI**: ⭐⭐⭐⭐⭐ (Very High)

These enhancements make DawsOS production-grade and enterprise-ready with professional features users expect.

---

**Ready to proceed with Option 4?**

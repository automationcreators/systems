# Dashboard & Notification Setup Guide

## Quick Start (5 minutes)

###  1. Load the launchd Job

```bash
# Load the daily morning job
launchctl load ~/Library/LaunchAgents/com.user.dailymorning.plist

# Verify it's loaded
launchctl list | grep dailymorning

# Test it now (don't wait until 9am)
launchctl start com.user.dailymorning

# Check the logs
tail -f /tmp/daily-morning.log
```

### 2. Set Up Telegram Bot (2 minutes)

```bash
python3 systems/notification-wrapper.py --setup-telegram
```

Follow the prompts:
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Give it a name like "Personal-OS Monitor"
4. Copy the token
5. Start chat with your bot
6. Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
7. Copy the `chat_id` from response

### 3. Set Up Healthchecks.io (1 minute)

```bash
python3 systems/notification-wrapper.py --setup-healthchecks
```

1. Go to https://healthchecks.io
2. Create free account
3. Click "Add Check"
4. Name it "Daily Morning Sync"
5. Set schedule to "Daily"
6. Copy the ping URL

### 4. Test Notifications

```bash
# Send test notifications
python3 systems/notification-wrapper.py --test

# Should see notifications in:
# - Telegram
# - systems/notifications.log
```

### 5. Update Dashboard Backend

Add to `active/Project Management/dashboard/file-server.py` after line 28:

```python
elif parsed_url.path == '/systems-agent-status':
    self.handle_systems_agent_status()
elif parsed_url.path == '/run-agent':
    self.handle_run_agent(query_params)
```

Add these methods before the `is_safe_path` method:

```python
def handle_systems_agent_status(self):
    """Get real-time status of system agents"""
    try:
        result = subprocess.run(
            ['python3', 'systems/agent-status-api.py', '--save'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd='/Users/elizabethknopf/Documents/claudec'
        )

        # Read the generated file
        data_file = Path('/Users/elizabethknopf/Documents/claudec/active/Project Management/dashboard/data/systems-agent-data.json')
        with open(data_file, 'r') as f:
            data = f.read()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data.encode('utf-8'))
    except Exception as e:
        print(f"Error getting systems agent status: {e}")
        self.send_error(500, f"Error: {str(e)}")

def handle_run_agent(self, query_params):
    """Run a specific agent"""
    if 'agent' not in query_params:
        self.send_error(400, "Missing 'agent' parameter")
        return

    agent_id = query_params['agent'][0]

    # Map agent IDs to scripts
    agent_scripts = {
        "github-sync": "github-sync-agent.py --action sync",
        "project-discovery": "project-discovery-service.py --action scan",
        "security-monitor": "security-monitoring-dashboard.py --action scan",
        "backup-manager": "backup-manager.py --action backup --type daily",
        "todo-aggregation": "todo-aggregation-engine.py",
        "run-all": "daily-morning.sh"
    }

    if agent_id not in agent_scripts:
        self.send_error(404, f"Agent '{agent_id}' not found")
        return

    try:
        script = agent_scripts[agent_id]
        result = subprocess.run(
            script.split(),
            capture_output=True,
            text=True,
            timeout=300,
            cwd='/Users/elizabethknopf/Documents/claudec/systems'
        )

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    except subprocess.TimeoutExpired:
        self.send_error(408, "Agent execution timed out")
    except Exception as e:
        print(f"Error running agent {agent_id}: {e}")
        self.send_error(500, f"Error: {str(e)}")
```

### 6. Add System Agents Tab to Dashboard

Create `active/Project Management/dashboard/systems-agents-tab.html`:

```html
<!-- System Agents Tab -->
<div id="systems-agents-tab" class="tab-content" style="display: none;">
    <div class="agents-container">
        <div class="summary-cards">
            <div class="summary-card healthy">
                <div class="card-icon">✅</div>
                <div class="card-content">
                    <h3 id="sys-healthy-count">0</h3>
                    <p>Healthy Agents</p>
                </div>
            </div>
            <div class="summary-card warning">
                <div class="card-icon">⚠️</div>
                <div class="card-content">
                    <h3 id="sys-warning-count">0</h3>
                    <p>Need Attention</p>
                </div>
            </div>
            <div class="summary-card critical">
                <div class="card-icon">🔴</div>
                <div class="card-content">
                    <h3 id="sys-critical-count">0</h3>
                    <p>Critical Issues</p>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions-section">
            <h3>🚀 Quick Actions</h3>
            <div class="quick-actions-grid">
                <button class="action-btn" onclick="runAgent('run-all')">
                    <span class="btn-icon">🔄</span>
                    <span class="btn-text">Run All Agents</span>
                </button>
                <button class="action-btn" onclick="runAgent('github-sync')">
                    <span class="btn-icon">📦</span>
                    <span class="btn-text">Sync GitHub</span>
                </button>
                <button class="action-btn" onclick="runAgent('backup-manager')">
                    <span class="btn-icon">💾</span>
                    <span class="btn-text">Create Backup</span>
                </button>
                <button class="action-btn" onclick="refreshSystemAgents()">
                    <span class="btn-icon">🔍</span>
                    <span class="btn-text">Refresh Status</span>
                </button>
            </div>
        </div>

        <!-- Agent List -->
        <div class="agents-list" id="systems-agents-list"></div>
    </div>
</div>

<script>
async function refreshSystemAgents() {
    try {
        const response = await fetch('http://localhost:8080/systems-agent-status');
        const data = await response.json();

        document.getElementById('sys-healthy-count').textContent = data.summary.healthy_agents;
        document.getElementById('sys-warning-count').textContent = data.summary.warning_agents;
        document.getElementById('sys-critical-count').textContent = data.summary.critical_agents;

        const listDiv = document.getElementById('systems-agents-list');
        listDiv.innerHTML = '';

        data.agents.forEach(agent => {
            const healthIcon = agent.health.status === 'healthy' ? '✅' :
                             agent.health.status === 'warning' ? '⚠️' : '🔴';

            const card = `
                <div class="agent-card ${agent.health.status}">
                    <div class="agent-header">
                        <div class="agent-title">
                            <h4>${agent.name}</h4>
                            <span class="agent-type">${agent.type}</span>
                        </div>
                        <div class="agent-health">
                            <span class="health-icon">${healthIcon}</span>
                            <span class="health-score">${agent.health.score}/100</span>
                        </div>
                    </div>
                    <div class="agent-description">
                        <p>${agent.description}</p>
                    </div>
                    ${agent.health.issues.length > 0 ? `
                        <div class="agent-issues">
                            ${agent.health.issues.map(issue => `<span class="issue">⚠️ ${issue}</span>`).join('')}
                        </div>
                    ` : ''}
                    ${agent.commands.length > 0 ? `
                        <div class="agent-commands">
                            <h5>Commands:</h5>
                            <div class="command-tags">
                                ${agent.commands.map(cmd => `<span class="command-tag" onclick="runAgentCommand('${agent.id}', '${cmd}')">${cmd}</span>`).join(' ')}
                            </div>
                        </div>
                    ` : ''}
                    <div class="agent-meta">
                        <span class="file-info">📄 ${agent.file_name}</span>
                        ${agent.last_run ? `<span class="modified-info">🕒 Last run: ${new Date(agent.last_run).toLocaleString()}</span>` : ''}
                    </div>
                </div>
            `;
            listDiv.innerHTML += card;
        });
    } catch (error) {
        console.error('Failed to refresh system agents:', error);
    }
}

async function runAgent(agentId) {
    if (!confirm(`Run ${agentId}?`)) return;

    try {
        const response = await fetch(`http://localhost:8080/run-agent?agent=${agentId}`);
        const result = await response.json();

        if (result.success) {
            alert(`✅ ${agentId} completed successfully!\n\n${result.output}`);
            refreshSystemAgents();
        } else {
            alert(`❌ ${agentId} failed:\n\n${result.error}`);
        }
    } catch (error) {
        alert(`Error running agent: ${error}`);
    }
}

// Auto-refresh every 60 seconds
setInterval(refreshSystemAgents, 60000);

// Load on page load
if (document.getElementById('systems-agents-tab')) {
    refreshSystemAgents();
}
</script>
```

## Testing Everything

### 1. Start the Dashboard Server

```bash
cd "active/Project Management/dashboard"
python3 file-server.py
```

Open http://localhost:8080 in your browser

### 2. Run the Daily Morning Script Manually

```bash
./systems/daily-morning.sh
```

You should get notifications via:
- Telegram (if configured)
- Healthchecks.io ping (if configured)
- Local log file

### 3. Check Agent Status

```bash
python3 systems/agent-status-api.py
```

## Troubleshooting

### launchd not running?

```bash
# Check if loaded
launchctl list | grep dailymorning

# View logs
cat /tmp/daily-morning.log
cat /tmp/daily-morning-error.log

# Manually trigger
launchctl start com.user.dailymorning
```

### Telegram not working?

```bash
# Test directly
python3 systems/notification-wrapper.py --message "Test" --type success
```

### Dashboard not showing agents?

```bash
# Regenerate data
python3 systems/agent-status-api.py --save

# Check if file exists
cat "active/Project Management/dashboard/data/systems-agent-data.json"
```

## Summary

**No Conflicts! All 4 recommendations work together:**

1. ✅ **Telegram Bot** - Real-time notifications to phone
2. ✅ **Healthchecks.io** - Monitors job runs (backup if Telegram fails)
3. ✅ **Local Logs** - Always available for debugging
4. ✅ **launchd** - Reliable daily scheduler

**Next:** Run the setup commands above and you'll have a fully monitored agent system with phone notifications!

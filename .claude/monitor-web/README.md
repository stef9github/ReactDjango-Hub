# Agent Monitor Web Interface

A lightweight Django web application for monitoring and controlling development agents in the ReactDjango Hub project.

## Features

### Dashboard
- Real-time system metrics (CPU, Memory, Disk usage)
- Agent status overview with health indicators
- Task queue statistics
- Recent alerts and notifications
- Live log streaming
- Performance metrics visualization using Chart.js

### Agent Management
- View all agents with their current status
- Start/Stop/Restart agent controls
- Agent detail views with:
  - Resource usage monitoring
  - Task execution history
  - Communication logs
  - Performance metrics
- Inter-agent communication tracking
- Conflict detection and resolution interface

### Task Queue Management
- Create and manage tasks
- Task assignment to agents (manual or automatic)
- Task templates for common operations
- Priority-based queue management
- Task dependencies tracking
- Execution history and results

### Log Viewer
- Real-time log streaming
- Multi-level filtering (debug, info, warning, error, critical)
- Search functionality
- Agent-specific log filtering
- Time-based filtering
- Context data viewing

### Additional Features
- Git commit history viewer
- Workflow execution tracking
- Performance metrics and analysis
- Alert management system
- Auto-refresh capabilities
- Responsive Bootstrap UI

## Quick Start

### Installation

1. Navigate to the monitor directory:
```bash
cd .claude/monitor-web
```

2. Run the startup script:
```bash
./start-monitor.sh
```

This will:
- Create a virtual environment
- Install dependencies
- Run database migrations
- Create an admin user (admin/admin123)
- Initialize agents from configuration
- Start the development server on port 8888

### Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize agents
python manage.py init_agents

# Start server
python manage.py runserver 0.0.0.0:8888
```

## Access

- **Main Dashboard**: http://localhost:8888
- **Admin Interface**: http://localhost:8888/admin
- **Default Credentials**: admin / admin123

## Management Commands

### Initialize Agents
```bash
python manage.py init_agents
```
Loads agents from `.claude/agents.yaml` configuration file.

### Monitor Agents
```bash
python manage.py monitor_agents --interval 5
```
Continuously monitors agent processes and updates their status.

### Simulate Activity (Testing)
```bash
python manage.py simulate_activity --duration 60
```
Simulates agent activity for testing the interface.

## API Endpoints

### Metrics
- `/api/metrics/` - Current system metrics
- `/api/metrics/history/` - Historical metrics data
- `/api/alerts/` - Alert management

### Agents
- `/agents/api/{id}/status/` - Agent status
- `/agents/api/{id}/logs/` - Agent logs

### Tasks
- `/tasks/api/queue/` - Task queue status
- `/tasks/api/create/` - Create new task

### Logs
- `/logs/api/stream/` - Live log streaming
- `/logs/api/stats/` - Log statistics

## Architecture

### Models

#### Dashboard App
- `SystemMetric` - System-wide performance metrics
- `Alert` - System alerts and notifications

#### Agents App
- `Agent` - Agent configuration and status
- `AgentStatus` - Status history tracking
- `AgentCommunication` - Inter-agent messages
- `AgentConflict` - Conflict detection

#### Tasks App
- `Task` - Task queue items
- `TaskExecution` - Execution history
- `TaskTemplate` - Reusable templates

#### Logs App
- `LogEntry` - General system logs
- `GitCommit` - Git history tracking
- `WorkflowLog` - Workflow execution
- `PerformanceLog` - Performance metrics

### Technologies Used

- **Backend**: Django 5.0+
- **Database**: SQLite (default)
- **Frontend**: Bootstrap 5, jQuery
- **Charts**: Chart.js
- **Tables**: DataTables
- **Icons**: Bootstrap Icons

## Configuration

### Settings
Edit `monitor/settings.py` for:
- Database configuration
- Agent configuration path
- Refresh intervals
- Logging settings

### Customization
- Templates in `templates/` directory
- Static files in `static/` directory
- Custom CSS in `static/css/monitor.css`

## Development

### Adding New Features

1. Create new Django app:
```bash
python manage.py startapp feature_name
```

2. Add to `INSTALLED_APPS` in settings

3. Create models, views, and templates

4. Add URL patterns

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Testing

Run the simulation command to generate test data:
```bash
python manage.py simulate_activity --duration 300
```

## Troubleshooting

### Port Already in Use
If port 8888 is taken, use a different port:
```bash
python manage.py runserver 0.0.0.0:9999
```

### Database Issues
Reset the database:
```bash
rm db.sqlite3
python manage.py migrate
python manage.py init_agents
```

### Agent Connection Issues
Ensure the agent configuration file exists:
```bash
ls ../.claude/agents.yaml
```

## Security Notes

- Change default admin credentials in production
- Use environment variables for sensitive settings
- Enable HTTPS for production deployment
- Implement proper authentication for API endpoints

## License

Part of the ReactDjango Hub project.
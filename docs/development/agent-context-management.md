# Agent Context Management

Advanced context management system for Claude Code agents working with ReactDjango Hub, ensuring optimal context utilization, persistent state, and efficient cross-agent collaboration.

## 🧠 **Context Management Overview**

### **Context Challenges**
- **Context Window Limits**: Managing large codebases within token constraints
- **State Persistence**: Maintaining project knowledge across sessions
- **Agent Coordination**: Sharing context between backend and frontend agents
- **Project Comprehension**: Understanding complex full-stack relationships

### **Solution Architecture**
```yaml
context_management:
  project_snapshots:
    - codebase_structure
    - key_relationships
    - configuration_summary
    - active_development_areas
  
  agent_memory:
    - session_state
    - completed_tasks
    - code_patterns
    - user_preferences
  
  cross_agent_sync:
    - shared_context_files
    - communication_protocols
    - state_synchronization
```

## 📊 **Project State Snapshots**

### **Automated Snapshot Generation**

#### **Codebase Structure Snapshot**
```python
# Context generator for project structure
class ProjectSnapshotGenerator:
    def generate_structure_snapshot(self):
        """Generate comprehensive project structure overview."""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'project_type': 'fullstack_saas',
            'tech_stack': {
                'backend': 'Django + PostgreSQL + Redis',
                'frontend': 'React + TypeScript + Vite + Tailwind',
                'infrastructure': 'Docker + Kubernetes'
            },
            'key_directories': self.analyze_directory_structure(),
            'important_files': self.identify_key_files(),
            'dependencies': self.extract_dependencies(),
            'configuration': self.summarize_config()
        }
        return snapshot
    
    def analyze_directory_structure(self):
        """Analyze and summarize directory structure."""
        return {
            'backend/': {
                'apps/': 'Django applications and business logic',
                'config/': 'Django settings and configuration',
                'tests/': 'Backend test suites',
                'requirements.txt': 'Python dependencies'
            },
            'frontend/': {
                'src/components/': 'React components library',
                'src/pages/': 'Page-level components',
                'src/api/': 'API client functions',
                'src/types/': 'TypeScript type definitions'
            },
            'docs/': {
                'development/': 'Development guides and workflows',
                'api/': 'API documentation',
                'deployment/': 'Deployment guides'
            }
        }
```

#### **Key Relationships Mapping**
```python
def map_project_relationships():
    """Map key relationships across the full-stack application."""
    relationships = {
        'api_endpoints': {
            'backend_views': 'apps/api/views.py',
            'frontend_clients': 'src/api/clients/',
            'type_definitions': 'src/types/api.ts'
        },
        'data_models': {
            'django_models': 'apps/*/models.py',
            'frontend_types': 'src/types/models.ts',
            'database_schema': 'backend/migrations/'
        },
        'authentication': {
            'backend_auth': 'apps/authentication/',
            'frontend_auth': 'src/contexts/AuthContext.tsx',
            'routing': 'src/components/ProtectedRoute.tsx'
        },
        'internationalization': {
            'django_i18n': 'apps/*/locale/',
            'react_i18n': 'src/locales/',
            'configuration': 'src/i18n/config.ts'
        }
    }
    return relationships
```

### **Configuration Summary**
```python
def generate_config_summary():
    """Generate summary of key configuration files."""
    return {
        'django_settings': {
            'file': 'backend/config/settings.py',
            'key_settings': [
                'DATABASE_URL', 'SECRET_KEY', 'ALLOWED_HOSTS',
                'LANGUAGE_CODE', 'TIME_ZONE', 'INSTALLED_APPS'
            ],
            'security': ['FIELD_ENCRYPTION_KEY', 'SESSION_COOKIE_SECURE'],
            'i18n': ['LANGUAGES', 'USE_I18N', 'LOCALE_PATHS']
        },
        'frontend_config': {
            'vite_config': 'frontend/vite.config.ts',
            'env_vars': ['VITE_API_URL', 'VITE_DEFAULT_LANGUAGE'],
            'package_json': 'frontend/package.json'
        },
        'infrastructure': {
            'docker_compose': 'docker-compose.yml',
            'dockerfile_backend': 'backend/Dockerfile',
            'dockerfile_frontend': 'frontend/Dockerfile'
        }
    }
```

## 💾 **Agent Memory System**

### **Session State Persistence**

#### **Agent State Storage**
```typescript
// Agent state management
interface AgentState {
  sessionId: string;
  agentType: 'backend' | 'frontend' | 'full-stack';
  currentTasks: Task[];
  completedTasks: Task[];
  codebaseKnowledge: CodebaseKnowledge;
  userPreferences: UserPreferences;
  lastActivity: Date;
}

interface CodebaseKnowledge {
  recentlyModifiedFiles: string[];
  identifiedPatterns: CodePattern[];
  knownIssues: Issue[];
  dependencyRelationships: Relationship[];
}

interface UserPreferences {
  preferredLanguage: 'fr' | 'de' | 'en';
  codeStyle: 'django-standard' | 'custom';
  testingApproach: 'tdd' | 'after-implementation';
  commitStyle: 'conventional' | 'descriptive';
}
```

#### **Context Persistence Commands**
```bash
# Save current agent context
make context-save

# Restore agent context from previous session  
make context-restore

# Sync context between agents
make context-sync

# Generate project snapshot
make context-snapshot
```

### **Knowledge Base Updates**
```python
class AgentKnowledgeManager:
    def update_knowledge(self, action_type, details):
        """Update agent knowledge based on actions taken."""
        knowledge_updates = {
            'file_modified': self.track_file_changes,
            'pattern_identified': self.record_code_pattern,
            'issue_resolved': self.update_issue_status,
            'dependency_added': self.track_dependency_change
        }
        
        if action_type in knowledge_updates:
            knowledge_updates[action_type](details)
    
    def track_file_changes(self, file_details):
        """Track modifications to files for context awareness."""
        return {
            'file_path': file_details['path'],
            'modification_type': file_details['type'],
            'timestamp': datetime.now().isoformat(),
            'related_files': self.find_related_files(file_details['path']),
            'impact_analysis': self.analyze_change_impact(file_details)
        }
```

## 🔄 **Cross-Agent Synchronization**

### **Shared Context Files**

#### **Context Sharing Structure**
```
.claude/context/
├── project-snapshot.json          # Current project state
├── agent-states/
│   ├── backend-agent-state.json   # Backend agent context
│   ├── frontend-agent-state.json  # Frontend agent context
│   └── shared-knowledge.json      # Cross-agent knowledge
├── communication/
│   ├── agent-messages.json        # Inter-agent messages
│   └── coordination-log.json      # Coordination history
└── snapshots/
    ├── daily/                     # Daily project snapshots
    └── milestone/                 # Milestone snapshots
```

#### **Agent Communication Protocol**
```python
class AgentCommunication:
    def send_message(self, from_agent, to_agent, message_type, content):
        """Send message between agents."""
        message = {
            'id': self.generate_message_id(),
            'timestamp': datetime.now().isoformat(),
            'from': from_agent,
            'to': to_agent,
            'type': message_type,
            'content': content,
            'status': 'pending'
        }
        
        self.store_message(message)
        return message['id']
    
    def get_messages(self, agent_id, status='pending'):
        """Retrieve messages for an agent."""
        return self.message_store.filter(
            to=agent_id, 
            status=status
        )
    
    def mark_message_processed(self, message_id):
        """Mark message as processed."""
        self.message_store.update(
            message_id, 
            {'status': 'processed', 'processed_at': datetime.now()}
        )
```

### **State Synchronization**
```python
def sync_agent_states():
    """Synchronize state between backend and frontend agents."""
    backend_state = load_agent_state('backend')
    frontend_state = load_agent_state('frontend')
    
    # Identify synchronization needs
    sync_items = {
        'api_changes': compare_api_definitions(backend_state, frontend_state),
        'model_updates': compare_data_models(backend_state, frontend_state),
        'shared_types': identify_shared_types(backend_state, frontend_state)
    }
    
    # Generate synchronization tasks
    sync_tasks = []
    for category, items in sync_items.items():
        for item in items:
            sync_tasks.append(create_sync_task(category, item))
    
    return sync_tasks
```

## 🎯 **Context Optimization Strategies**

### **Context Compression Techniques**

#### **Selective Context Loading**
```python
class ContextManager:
    def load_relevant_context(self, current_task):
        """Load only relevant context for current task."""
        context_priority = {
            'high': ['current_files', 'related_dependencies', 'active_tests'],
            'medium': ['project_structure', 'configuration', 'recent_changes'],
            'low': ['historical_data', 'archived_tasks', 'old_snapshots']
        }
        
        # Load high priority context first
        context = {}
        remaining_tokens = self.calculate_available_tokens()
        
        for priority in ['high', 'medium', 'low']:
            if remaining_tokens > 1000:  # Keep buffer
                priority_context = self.load_priority_context(
                    context_priority[priority], 
                    current_task
                )
                context.update(priority_context)
                remaining_tokens -= self.estimate_token_usage(priority_context)
            else:
                break
        
        return context
```

#### **Dynamic Context Summarization**
```python
def summarize_large_files(file_path, target_length=500):
    """Summarize large files for context efficiency."""
    content = read_file(file_path)
    
    if len(content.split()) <= target_length:
        return content
    
    # Extract key information
    summary = {
        'file_type': detect_file_type(file_path),
        'main_classes': extract_class_definitions(content),
        'key_functions': extract_function_signatures(content),
        'imports': extract_imports(content),
        'configuration': extract_config_values(content),
        'comments': extract_important_comments(content)
    }
    
    return format_summary(summary)
```

### **Context Refresh Strategies**
```bash
# Automated context refresh triggers
context_refresh_triggers:
  file_changes: "Refresh when >10 files modified"
  time_based: "Refresh every 4 hours of active development"
  task_completion: "Refresh after completing major tasks"
  error_patterns: "Refresh when encountering repeated errors"
  dependency_changes: "Refresh after package updates"
```

## 📋 **Context Management Commands**

### **Project Snapshot Commands**
```bash
# Generate comprehensive project snapshot
make context-project-snapshot

# Generate focused snapshot for current development area
make context-focused-snapshot --area=authentication

# Compare snapshots to identify changes
make context-compare-snapshots --from=yesterday --to=now

# Generate context for specific feature development
make context-feature-snapshot --feature=user-management
```

### **Agent Context Commands**
```bash
# Save current agent working context
make context-agent-save --agent=backend

# Restore agent context from previous session
make context-agent-restore --agent=frontend --session=last

# Merge contexts from multiple agents
make context-agent-merge --agents=backend,frontend

# Generate agent handoff context
make context-agent-handoff --from=backend --to=frontend
```

### **Context Synchronization Commands**
```bash
# Sync context between all agents
make context-sync-all

# Sync specific context categories
make context-sync --categories=api,models,types

# Validate context consistency
make context-validate

# Clean outdated context data
make context-cleanup --older-than=7days
```

## 🔧 **Context Configuration**

### **Context Management Configuration**
```yaml
# .claude/context-config.yml
context_management:
  compression:
    enable_summarization: true
    target_summary_length: 500
    preserve_critical_sections: true
  
  persistence:
    save_interval: 300  # seconds
    max_history_items: 100
    compression_threshold: 10000  # tokens
  
  synchronization:
    auto_sync: true
    sync_interval: 600  # seconds
    conflict_resolution: 'latest_wins'
  
  optimization:
    context_loading_strategy: 'selective'
    token_budget_management: true
    background_context_updates: true
```

### **Agent-Specific Context Settings**
```yaml
# Agent context preferences
agents:
  backend:
    priority_context:
      - django_models
      - api_endpoints
      - database_migrations
      - authentication_system
    
    summary_targets:
      models: 200
      views: 300
      tests: 150
  
  frontend:
    priority_context:
      - react_components
      - api_clients
      - routing_configuration
      - state_management
    
    summary_targets:
      components: 250
      hooks: 150
      types: 100
```

## 📊 **Context Analytics**

### **Context Usage Metrics**
```python
def generate_context_analytics():
    """Generate analytics on context usage and efficiency."""
    return {
        'context_utilization': {
            'average_tokens_used': 8500,
            'peak_usage': 12000,
            'compression_ratio': 0.65,
            'cache_hit_rate': 0.78
        },
        'agent_efficiency': {
            'context_load_time': '1.2s',
            'sync_frequency': '4x per session',
            'knowledge_retention': 0.85
        },
        'optimization_opportunities': [
            'Increase compression for historical data',
            'Improve context cache efficiency',
            'Optimize cross-agent sync frequency'
        ]
    }
```

---

🧠 **This agent context management system ensures optimal Claude Code performance by intelligently managing context, maintaining project knowledge, and enabling efficient cross-agent collaboration while staying within token limits.**
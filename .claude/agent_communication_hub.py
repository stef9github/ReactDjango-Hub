#!/usr/bin/env python3
"""
Agent Communication Hub for ReactDjango-Hub
Central coordination system for all Claude agents with message routing,
task delegation, context sharing, and conflict resolution.
"""

import os
import json
import yaml
import asyncio
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
import pickle
import shutil
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels for task queue"""
    CRITICAL = 1  # System errors, conflicts
    HIGH = 2      # User requests, deadlines
    NORMAL = 3    # Regular tasks
    LOW = 4       # Background tasks, maintenance


class TaskStatus(Enum):
    """Task lifecycle status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(Enum):
    """Agent availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MessageType(Enum):
    """Types of inter-agent messages"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    CONTEXT_SHARE = "context_share"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    CONFLICT_ALERT = "conflict_alert"
    HANDOFF = "handoff"
    QUERY = "query"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    id: str
    type: MessageType
    sender: str
    recipient: str
    priority: MessagePriority
    timestamp: datetime
    payload: Dict[str, Any]
    requires_response: bool = False
    response_timeout: int = 300  # seconds
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary"""
        data = asdict(self)
        data['type'] = self.type.value
        data['priority'] = self.priority.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentMessage':
        """Create message from dictionary"""
        data['type'] = MessageType(data['type'])
        data['priority'] = MessagePriority(data['priority'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Task:
    """Task representation for work queue"""
    id: str
    title: str
    description: str
    agent: str
    status: TaskStatus
    priority: MessagePriority
    created_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    parent_task: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        if self.assigned_at:
            data['assigned_at'] = self.assigned_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


@dataclass
class AgentProfile:
    """Agent capability and status profile"""
    name: str
    type: str
    status: AgentStatus
    capabilities: List[str]
    working_directory: str
    current_task: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    boundaries: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def is_available(self) -> bool:
        """Check if agent is available for tasks"""
        return self.status == AgentStatus.AVAILABLE and self.current_task is None
    
    def can_handle(self, task_type: str) -> bool:
        """Check if agent can handle a specific task type"""
        return task_type in self.capabilities


class SharedContext:
    """Manages shared context between agents"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.context_dir = base_path / ".claude" / "shared_context"
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def set_context(self, key: str, value: Any, agent: str, ttl: Optional[int] = None):
        """Set shared context value"""
        with self.lock:
            context_data = {
                'value': value,
                'agent': agent,
                'timestamp': datetime.now(),
                'ttl': ttl,
                'expires_at': datetime.now() + timedelta(seconds=ttl) if ttl else None
            }
            self.contexts[key] = context_data
            
            # Persist to file
            context_file = self.context_dir / f"{key}.json"
            with open(context_file, 'w') as f:
                json.dump({
                    'value': value,
                    'agent': agent,
                    'timestamp': context_data['timestamp'].isoformat(),
                    'ttl': ttl,
                    'expires_at': context_data['expires_at'].isoformat() if context_data['expires_at'] else None
                }, f, indent=2)
    
    def get_context(self, key: str) -> Optional[Any]:
        """Get shared context value"""
        with self.lock:
            # Check in-memory cache first
            if key in self.contexts:
                context_data = self.contexts[key]
                if context_data['expires_at'] and context_data['expires_at'] < datetime.now():
                    del self.contexts[key]
                    return None
                return context_data['value']
            
            # Check persistent storage
            context_file = self.context_dir / f"{key}.json"
            if context_file.exists():
                with open(context_file, 'r') as f:
                    data = json.load(f)
                    if data['expires_at']:
                        expires_at = datetime.fromisoformat(data['expires_at'])
                        if expires_at < datetime.now():
                            context_file.unlink()
                            return None
                    return data['value']
            
            return None
    
    def list_contexts(self, agent: Optional[str] = None) -> List[str]:
        """List all context keys, optionally filtered by agent"""
        with self.lock:
            if agent:
                return [k for k, v in self.contexts.items() if v['agent'] == agent]
            return list(self.contexts.keys())
    
    def clear_expired(self):
        """Clear expired context entries"""
        with self.lock:
            expired_keys = []
            for key, data in self.contexts.items():
                if data['expires_at'] and data['expires_at'] < datetime.now():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.contexts[key]
                context_file = self.context_dir / f"{key}.json"
                if context_file.exists():
                    context_file.unlink()


class ConflictResolver:
    """Handles conflicts between agents"""
    
    def __init__(self):
        self.conflict_history: List[Dict[str, Any]] = []
        self.resolution_strategies = {
            'file_conflict': self._resolve_file_conflict,
            'resource_conflict': self._resolve_resource_conflict,
            'dependency_conflict': self._resolve_dependency_conflict,
            'boundary_violation': self._resolve_boundary_violation
        }
    
    def detect_conflict(self, agent1: str, agent2: str, resource: str, operation: str) -> Optional[Dict]:
        """Detect potential conflicts between agents"""
        conflict = None
        
        # Check for file conflicts
        if operation in ['write', 'delete', 'modify']:
            if self._is_shared_resource(resource):
                conflict = {
                    'type': 'file_conflict',
                    'agents': [agent1, agent2],
                    'resource': resource,
                    'operation': operation,
                    'timestamp': datetime.now()
                }
        
        # Check for boundary violations
        if self._crosses_boundary(agent1, resource):
            conflict = {
                'type': 'boundary_violation',
                'agent': agent1,
                'resource': resource,
                'operation': operation,
                'timestamp': datetime.now()
            }
        
        if conflict:
            self.conflict_history.append(conflict)
            logger.warning(f"Conflict detected: {conflict}")
        
        return conflict
    
    def resolve_conflict(self, conflict: Dict) -> Dict[str, Any]:
        """Resolve a detected conflict"""
        conflict_type = conflict['type']
        
        if conflict_type in self.resolution_strategies:
            return self.resolution_strategies[conflict_type](conflict)
        
        # Default resolution
        return {
            'resolution': 'defer',
            'message': f"Conflict of type {conflict_type} requires manual intervention",
            'suggested_action': 'Review and coordinate with team lead'
        }
    
    def _resolve_file_conflict(self, conflict: Dict) -> Dict:
        """Resolve file access conflicts"""
        return {
            'resolution': 'queue',
            'message': f"File {conflict['resource']} access queued for sequential processing",
            'action': 'create_file_lock',
            'priority': MessagePriority.HIGH.value
        }
    
    def _resolve_resource_conflict(self, conflict: Dict) -> Dict:
        """Resolve resource access conflicts"""
        return {
            'resolution': 'coordinate',
            'message': "Resource access will be coordinated through coordinator agent",
            'action': 'delegate_to_coordinator'
        }
    
    def _resolve_dependency_conflict(self, conflict: Dict) -> Dict:
        """Resolve dependency conflicts"""
        return {
            'resolution': 'wait',
            'message': "Waiting for dependency resolution",
            'action': 'add_to_wait_queue'
        }
    
    def _resolve_boundary_violation(self, conflict: Dict) -> Dict:
        """Resolve boundary violation conflicts"""
        return {
            'resolution': 'reject',
            'message': f"Agent {conflict['agent']} cannot access {conflict['resource']} - outside boundaries",
            'action': 'reject_operation'
        }
    
    def _is_shared_resource(self, resource: str) -> bool:
        """Check if a resource is shared between agents"""
        shared_resources = [
            'docker-compose.yml',
            'Makefile',
            '.github/workflows',
            'package.json',
            'requirements.txt',
            'settings.py',
            'config.yaml'
        ]
        return any(shared in resource for shared in shared_resources)
    
    def _crosses_boundary(self, agent: str, resource: str) -> bool:
        """Check if an agent is crossing its boundaries"""
        agent_boundaries = {
            'backend': ['backend/', 'docs/backend/'],
            'frontend': ['frontend/', 'docs/frontend/'],
            'identity': ['services/identity-service/'],
            'communication': ['services/communication-service/'],
            'content': ['services/content-service/'],
            'workflow': ['services/workflow-service/']
        }
        
        if agent not in agent_boundaries:
            return False
        
        allowed_paths = agent_boundaries[agent]
        return not any(resource.startswith(path) for path in allowed_paths)


class TaskRouter:
    """Routes tasks to appropriate agents"""
    
    def __init__(self):
        self.routing_rules = self._initialize_routing_rules()
        self.routing_history: List[Dict] = []
    
    def _initialize_routing_rules(self) -> Dict[str, List[str]]:
        """Initialize task routing rules"""
        return {
            'django_model': ['backend'],
            'react_component': ['frontend'],
            'authentication': ['identity'],
            'notification': ['communication'],
            'file_processing': ['content'],
            'workflow_automation': ['workflow'],
            'docker_config': ['infrastructure'],
            'api_integration': ['coordinator', 'backend'],
            'security_audit': ['security'],
            'code_review': ['reviewer'],
            'architecture_decision': ['techlead'],
            'test_creation': ['backend', 'frontend'],
            'database_migration': ['backend'],
            'ui_design': ['frontend'],
            'deployment': ['infrastructure'],
            'performance_optimization': ['techlead', 'backend', 'frontend']
        }
    
    def route_task(self, task_type: str, context: Dict[str, Any]) -> str:
        """Route a task to the appropriate agent"""
        # Check routing rules
        if task_type in self.routing_rules:
            candidates = self.routing_rules[task_type]
            
            # Apply context-based routing logic
            if 'preferred_agent' in context and context['preferred_agent'] in candidates:
                selected = context['preferred_agent']
            elif 'file_path' in context:
                selected = self._route_by_file_path(context['file_path'], candidates)
            else:
                # Default to first candidate
                selected = candidates[0]
            
            # Log routing decision
            self.routing_history.append({
                'task_type': task_type,
                'selected_agent': selected,
                'candidates': candidates,
                'context': context,
                'timestamp': datetime.now().isoformat()
            })
            
            return selected
        
        # Default routing based on keywords
        return self._keyword_based_routing(task_type, context)
    
    def _route_by_file_path(self, file_path: str, candidates: List[str]) -> str:
        """Route based on file path"""
        path_mapping = {
            'backend/': 'backend',
            'frontend/': 'frontend',
            'services/identity-service/': 'identity',
            'services/communication-service/': 'communication',
            'services/content-service/': 'content',
            'services/workflow-service/': 'workflow',
            'infrastructure/': 'infrastructure',
            'docker/': 'infrastructure',
            '.github/': 'infrastructure',
            'docs/': 'documentation'
        }
        
        for path_prefix, agent in path_mapping.items():
            if file_path.startswith(path_prefix) and agent in candidates:
                return agent
        
        return candidates[0]
    
    def _keyword_based_routing(self, task_type: str, context: Dict) -> str:
        """Route based on keywords in task type"""
        keyword_mapping = {
            'api': 'backend',
            'ui': 'frontend',
            'auth': 'identity',
            'email': 'communication',
            'file': 'content',
            'process': 'workflow',
            'deploy': 'infrastructure',
            'test': 'backend',
            'security': 'security',
            'review': 'reviewer',
            'design': 'techlead'
        }
        
        task_lower = task_type.lower()
        for keyword, agent in keyword_mapping.items():
            if keyword in task_lower:
                return agent
        
        # Default to coordinator for unknown tasks
        return 'coordinator'
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        if not self.routing_history:
            return {'total_routed': 0}
        
        agent_counts = defaultdict(int)
        for entry in self.routing_history:
            agent_counts[entry['selected_agent']] += 1
        
        return {
            'total_routed': len(self.routing_history),
            'by_agent': dict(agent_counts),
            'recent_routes': self.routing_history[-10:]
        }


class AgentCommunicationHub:
    """Central hub for agent communication and coordination"""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path.cwd()
        self.hub_dir = self.base_path / ".claude" / "communication_hub"
        self.hub_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.agents: Dict[str, AgentProfile] = {}
        self.message_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.task_queue: deque = deque()
        self.shared_context = SharedContext(self.base_path)
        self.conflict_resolver = ConflictResolver()
        self.task_router = TaskRouter()
        
        # Initialize storage
        self.db_path = self.hub_dir / "hub.db"
        self._initialize_database()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Message handlers
        self.message_handlers = {
            MessageType.TASK_REQUEST: self._handle_task_request,
            MessageType.TASK_RESPONSE: self._handle_task_response,
            MessageType.CONTEXT_SHARE: self._handle_context_share,
            MessageType.STATUS_UPDATE: self._handle_status_update,
            MessageType.ERROR_REPORT: self._handle_error_report,
            MessageType.CONFLICT_ALERT: self._handle_conflict_alert,
            MessageType.HANDOFF: self._handle_handoff,
            MessageType.QUERY: self._handle_query,
            MessageType.NOTIFICATION: self._handle_notification,
            MessageType.HEARTBEAT: self._handle_heartbeat
        }
        
        # Load agent configurations
        self._load_agent_configurations()
        
        logger.info("Agent Communication Hub initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for persistent storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                priority INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                response TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                agent TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                assigned_at TEXT,
                completed_at TEXT,
                dependencies TEXT,
                context TEXT,
                result TEXT,
                error TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_status (
                agent_name TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_task TEXT,
                last_heartbeat TEXT,
                performance_metrics TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                agents TEXT NOT NULL,
                resource TEXT,
                resolution TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_agent_configurations(self):
        """Load agent configurations from YAML files"""
        agents_yaml = self.base_path / ".claude" / "agents.yaml"
        if agents_yaml.exists():
            with open(agents_yaml, 'r') as f:
                config = yaml.safe_load(f)
                
                for agent_key, agent_config in config.get('agents', {}).items():
                    agent_name = agent_key.replace('ag-', '')
                    
                    # Extract capabilities from responsibilities
                    capabilities = []
                    if 'responsibilities' in agent_config:
                        for resp in agent_config['responsibilities']:
                            # Extract key capability keywords
                            if 'Django' in resp:
                                capabilities.append('django_model')
                            if 'React' in resp or 'component' in resp:
                                capabilities.append('react_component')
                            if 'auth' in resp.lower():
                                capabilities.append('authentication')
                            if 'notification' in resp or 'email' in resp:
                                capabilities.append('notification')
                            if 'file' in resp or 'document' in resp:
                                capabilities.append('file_processing')
                            if 'workflow' in resp or 'automation' in resp:
                                capabilities.append('workflow_automation')
                            if 'Docker' in resp or 'Kubernetes' in resp:
                                capabilities.append('docker_config')
                            if 'API' in resp:
                                capabilities.append('api_integration')
                    
                    profile = AgentProfile(
                        name=agent_name,
                        type=agent_key,
                        status=AgentStatus.OFFLINE,
                        capabilities=capabilities,
                        working_directory=agent_config.get('working_dir', '.'),
                        boundaries=self._extract_boundaries(agent_config)
                    )
                    
                    self.agents[agent_name] = profile
    
    def _extract_boundaries(self, agent_config: Dict) -> List[str]:
        """Extract agent boundaries from configuration"""
        boundaries = []
        working_dir = agent_config.get('working_dir', '')
        
        if working_dir and working_dir != '.':
            boundaries.append(f"{working_dir}/")
        
        # Add from responsibilities if they contain path information
        for resp in agent_config.get('responsibilities', []):
            if '/' in resp:
                # Extract path patterns from responsibilities
                import re
                paths = re.findall(r'[\w\-/]+/', resp)
                boundaries.extend(paths)
        
        return boundaries
    
    def register_agent(self, agent_name: str, profile: AgentProfile):
        """Register an agent with the hub"""
        self.agents[agent_name] = profile
        profile.status = AgentStatus.AVAILABLE
        profile.last_heartbeat = datetime.now()
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO agent_status (agent_name, status, last_heartbeat)
            VALUES (?, ?, ?)
        ''', (agent_name, profile.status.value, profile.last_heartbeat.isoformat()))
        conn.commit()
        conn.close()
        
        logger.info(f"Agent {agent_name} registered")
    
    def send_message(self, message: AgentMessage):
        """Send a message to an agent"""
        # Add to message queue
        priority_value = message.priority.value
        self.message_queue.put((priority_value, message.timestamp, message))
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (id, type, sender, recipient, priority, timestamp, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            message.id,
            message.type.value,
            message.sender,
            message.recipient,
            message.priority.value,
            message.timestamp.isoformat(),
            json.dumps(message.payload)
        ))
        conn.commit()
        conn.close()
        
        # Process message asynchronously
        self.executor.submit(self._process_message, message)
    
    def _process_message(self, message: AgentMessage):
        """Process a message"""
        try:
            handler = self.message_handlers.get(message.type)
            if handler:
                response = handler(message)
                
                if message.requires_response and response:
                    # Send response back
                    response_msg = AgentMessage(
                        id=f"resp-{message.id}",
                        type=MessageType.TASK_RESPONSE,
                        sender=message.recipient,
                        recipient=message.sender,
                        priority=message.priority,
                        timestamp=datetime.now(),
                        payload=response,
                        correlation_id=message.id
                    )
                    self.send_message(response_msg)
            
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            self._handle_message_error(message, str(e))
    
    def create_task(self, title: str, description: str, agent: Optional[str] = None,
                   priority: MessagePriority = MessagePriority.NORMAL,
                   context: Optional[Dict] = None) -> Task:
        """Create a new task"""
        task_id = hashlib.md5(f"{title}{datetime.now()}".encode()).hexdigest()[:8]
        
        # Route task if no agent specified
        if not agent:
            agent = self.task_router.route_task(title, context or {})
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            agent=agent,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=datetime.now(),
            context=context or {}
        )
        
        # Add to task queue
        self.task_queue.append(task)
        
        # Store in database
        self._store_task(task)
        
        # Notify agent
        message = AgentMessage(
            id=f"task-{task_id}",
            type=MessageType.TASK_REQUEST,
            sender="hub",
            recipient=agent,
            priority=priority,
            timestamp=datetime.now(),
            payload={'task': task.to_dict()}
        )
        self.send_message(message)
        
        logger.info(f"Task {task_id} created for agent {agent}")
        return task
    
    def delegate_task(self, task_id: str, from_agent: str, to_agent: str,
                     reason: str = ""):
        """Delegate a task from one agent to another"""
        task = self._get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        # Create handoff message
        handoff_msg = AgentMessage(
            id=f"handoff-{task_id}",
            type=MessageType.HANDOFF,
            sender=from_agent,
            recipient=to_agent,
            priority=task.priority,
            timestamp=datetime.now(),
            payload={
                'task': task.to_dict(),
                'reason': reason,
                'previous_agent': from_agent
            }
        )
        
        # Update task assignment
        task.agent = to_agent
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now()
        
        self._store_task(task)
        self.send_message(handoff_msg)
        
        logger.info(f"Task {task_id} delegated from {from_agent} to {to_agent}")
    
    def share_context(self, key: str, value: Any, agent: str, ttl: Optional[int] = None):
        """Share context between agents"""
        self.shared_context.set_context(key, value, agent, ttl)
        
        # Notify interested agents
        notification = AgentMessage(
            id=f"context-{key}",
            type=MessageType.CONTEXT_SHARE,
            sender=agent,
            recipient="all",
            priority=MessagePriority.LOW,
            timestamp=datetime.now(),
            payload={'key': key, 'value': value}
        )
        self.send_message(notification)
    
    def report_conflict(self, agent1: str, agent2: str, resource: str, operation: str):
        """Report a conflict between agents"""
        conflict = self.conflict_resolver.detect_conflict(agent1, agent2, resource, operation)
        
        if conflict:
            resolution = self.conflict_resolver.resolve_conflict(conflict)
            
            # Store conflict in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conflict_log (type, agents, resource, resolution, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                conflict['type'],
                json.dumps(conflict.get('agents', [conflict.get('agent')])),
                resource,
                json.dumps(resolution),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            
            # Notify involved agents
            for agent in conflict.get('agents', [conflict.get('agent')]):
                alert = AgentMessage(
                    id=f"conflict-{datetime.now().timestamp()}",
                    type=MessageType.CONFLICT_ALERT,
                    sender="hub",
                    recipient=agent,
                    priority=MessagePriority.HIGH,
                    timestamp=datetime.now(),
                    payload={'conflict': conflict, 'resolution': resolution}
                )
                self.send_message(alert)
            
            return resolution
        
        return None
    
    def get_agent_status(self, agent_name: str) -> Optional[AgentProfile]:
        """Get current status of an agent"""
        return self.agents.get(agent_name)
    
    def get_all_agents_status(self) -> Dict[str, Dict]:
        """Get status of all agents"""
        return {
            name: {
                'status': profile.status.value,
                'current_task': profile.current_task,
                'last_heartbeat': profile.last_heartbeat.isoformat() if profile.last_heartbeat else None,
                'is_available': profile.is_available()
            }
            for name, profile in self.agents.items()
        }
    
    def get_task_queue_status(self) -> Dict[str, Any]:
        """Get current task queue status"""
        pending_tasks = [t for t in self.task_queue if t.status == TaskStatus.PENDING]
        in_progress = [t for t in self.task_queue if t.status == TaskStatus.IN_PROGRESS]
        blocked = [t for t in self.task_queue if t.status == TaskStatus.BLOCKED]
        
        return {
            'total_tasks': len(self.task_queue),
            'pending': len(pending_tasks),
            'in_progress': len(in_progress),
            'blocked': len(blocked),
            'by_agent': self._group_tasks_by_agent(),
            'by_priority': self._group_tasks_by_priority()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        metrics = {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get task completion rates
        cursor.execute('''
            SELECT agent, status, COUNT(*) as count
            FROM tasks
            GROUP BY agent, status
        ''')
        
        task_stats = defaultdict(lambda: defaultdict(int))
        for agent, status, count in cursor.fetchall():
            task_stats[agent][status] = count
        
        # Calculate metrics
        for agent in self.agents:
            stats = task_stats[agent]
            total = sum(stats.values())
            completed = stats.get('completed', 0)
            failed = stats.get('failed', 0)
            
            metrics[agent] = {
                'total_tasks': total,
                'completed': completed,
                'failed': failed,
                'success_rate': (completed / total * 100) if total > 0 else 0,
                'average_completion_time': self._calculate_avg_completion_time(agent)
            }
        
        conn.close()
        return metrics
    
    def _handle_task_request(self, message: AgentMessage) -> Dict:
        """Handle task request message"""
        task_data = message.payload.get('task')
        if not task_data:
            return {'error': 'No task data provided'}
        
        # Check if agent is available
        agent = self.agents.get(message.recipient)
        if not agent or not agent.is_available():
            # Try to delegate to another agent
            alternative = self._find_alternative_agent(task_data.get('title', ''))
            if alternative:
                self.delegate_task(task_data['id'], message.recipient, alternative,
                                 "Original agent unavailable")
                return {'status': 'delegated', 'new_agent': alternative}
            return {'error': 'Agent not available'}
        
        # Assign task to agent
        agent.current_task = task_data['id']
        agent.status = AgentStatus.BUSY
        
        return {'status': 'accepted', 'task_id': task_data['id']}
    
    def _handle_task_response(self, message: AgentMessage) -> None:
        """Handle task response message"""
        task_id = message.payload.get('task_id')
        status = message.payload.get('status')
        result = message.payload.get('result')
        
        # Update task status
        task = self._get_task(task_id)
        if task:
            task.status = TaskStatus(status) if status else TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            self._store_task(task)
        
        # Update agent status
        agent = self.agents.get(message.sender)
        if agent:
            agent.current_task = None
            agent.status = AgentStatus.AVAILABLE
    
    def _handle_context_share(self, message: AgentMessage) -> None:
        """Handle context sharing message"""
        key = message.payload.get('key')
        value = message.payload.get('value')
        ttl = message.payload.get('ttl')
        
        if key and value is not None:
            self.shared_context.set_context(key, value, message.sender, ttl)
    
    def _handle_status_update(self, message: AgentMessage) -> None:
        """Handle agent status update"""
        agent = self.agents.get(message.sender)
        if agent:
            new_status = message.payload.get('status')
            if new_status:
                agent.status = AgentStatus(new_status)
            
            current_task = message.payload.get('current_task')
            if current_task is not None:
                agent.current_task = current_task
    
    def _handle_error_report(self, message: AgentMessage) -> None:
        """Handle error report from agent"""
        error_type = message.payload.get('error_type')
        error_message = message.payload.get('message')
        task_id = message.payload.get('task_id')
        
        logger.error(f"Error from {message.sender}: {error_type} - {error_message}")
        
        # Update task if applicable
        if task_id:
            task = self._get_task(task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error = error_message
                self._store_task(task)
        
        # Update agent status
        agent = self.agents.get(message.sender)
        if agent:
            agent.status = AgentStatus.ERROR
    
    def _handle_conflict_alert(self, message: AgentMessage) -> Dict:
        """Handle conflict alert"""
        conflict = message.payload.get('conflict')
        if conflict:
            resolution = self.conflict_resolver.resolve_conflict(conflict)
            return {'resolution': resolution}
        return {'error': 'No conflict data provided'}
    
    def _handle_handoff(self, message: AgentMessage) -> Dict:
        """Handle task handoff between agents"""
        task_data = message.payload.get('task')
        if not task_data:
            return {'error': 'No task data provided'}
        
        # Accept handoff
        agent = self.agents.get(message.recipient)
        if agent and agent.is_available():
            agent.current_task = task_data['id']
            agent.status = AgentStatus.BUSY
            return {'status': 'accepted', 'task_id': task_data['id']}
        
        return {'error': 'Cannot accept handoff - agent not available'}
    
    def _handle_query(self, message: AgentMessage) -> Dict:
        """Handle query from agent"""
        query_type = message.payload.get('query_type')
        
        if query_type == 'context':
            key = message.payload.get('key')
            value = self.shared_context.get_context(key) if key else None
            return {'value': value}
        
        elif query_type == 'agent_status':
            agent_name = message.payload.get('agent')
            status = self.get_agent_status(agent_name) if agent_name else self.get_all_agents_status()
            return {'status': status}
        
        elif query_type == 'task_queue':
            return self.get_task_queue_status()
        
        return {'error': f'Unknown query type: {query_type}'}
    
    def _handle_notification(self, message: AgentMessage) -> None:
        """Handle notification message"""
        # Log notification
        logger.info(f"Notification from {message.sender}: {message.payload.get('message', '')}")
        
        # Store important notifications
        if message.priority in [MessagePriority.CRITICAL, MessagePriority.HIGH]:
            notification_file = self.hub_dir / "notifications.log"
            with open(notification_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {message.sender}: {json.dumps(message.payload)}\n")
    
    def _handle_heartbeat(self, message: AgentMessage) -> Dict:
        """Handle agent heartbeat"""
        agent = self.agents.get(message.sender)
        if agent:
            agent.last_heartbeat = datetime.now()
            metrics = message.payload.get('metrics', {})
            if metrics:
                agent.performance_metrics.update(metrics)
            return {'status': 'acknowledged'}
        return {'error': 'Unknown agent'}
    
    def _handle_message_error(self, message: AgentMessage, error: str):
        """Handle message processing error"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE messages SET status = 'failed', response = ?
            WHERE id = ?
        ''', (json.dumps({'error': error}), message.id))
        conn.commit()
        conn.close()
    
    def _store_task(self, task: Task):
        """Store task in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tasks 
            (id, title, description, agent, status, priority, created_at, 
             assigned_at, completed_at, dependencies, context, result, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.id,
            task.title,
            task.description,
            task.agent,
            task.status.value,
            task.priority.value,
            task.created_at.isoformat(),
            task.assigned_at.isoformat() if task.assigned_at else None,
            task.completed_at.isoformat() if task.completed_at else None,
            json.dumps(task.dependencies),
            json.dumps(task.context),
            json.dumps(task.result) if task.result else None,
            task.error
        ))
        conn.commit()
        conn.close()
    
    def _get_task(self, task_id: str) -> Optional[Task]:
        """Get task from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Task(
                id=row[0],
                title=row[1],
                description=row[2],
                agent=row[3],
                status=TaskStatus(row[4]),
                priority=MessagePriority(row[5]),
                created_at=datetime.fromisoformat(row[6]),
                assigned_at=datetime.fromisoformat(row[7]) if row[7] else None,
                completed_at=datetime.fromisoformat(row[8]) if row[8] else None,
                dependencies=json.loads(row[9]) if row[9] else [],
                context=json.loads(row[10]) if row[10] else {},
                result=json.loads(row[11]) if row[11] else None,
                error=row[12]
            )
        return None
    
    def _find_alternative_agent(self, task_type: str) -> Optional[str]:
        """Find an alternative agent for a task"""
        candidates = self.task_router.routing_rules.get(task_type, [])
        
        for candidate in candidates:
            agent = self.agents.get(candidate)
            if agent and agent.is_available():
                return candidate
        
        return None
    
    def _group_tasks_by_agent(self) -> Dict[str, int]:
        """Group tasks by agent"""
        agent_tasks = defaultdict(int)
        for task in self.task_queue:
            agent_tasks[task.agent] += 1
        return dict(agent_tasks)
    
    def _group_tasks_by_priority(self) -> Dict[str, int]:
        """Group tasks by priority"""
        priority_tasks = defaultdict(int)
        for task in self.task_queue:
            priority_tasks[task.priority.name] += 1
        return dict(priority_tasks)
    
    def _calculate_avg_completion_time(self, agent: str) -> float:
        """Calculate average task completion time for an agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT AVG(julianday(completed_at) - julianday(created_at)) * 24 * 60
            FROM tasks
            WHERE agent = ? AND status = 'completed' AND completed_at IS NOT NULL
        ''', (agent,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else 0.0
    
    def shutdown(self):
        """Shutdown the communication hub"""
        logger.info("Shutting down Agent Communication Hub")
        
        # Save current state
        self.shared_context.clear_expired()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Close database connections
        conn = sqlite3.connect(self.db_path)
        conn.close()
        
        logger.info("Agent Communication Hub shutdown complete")


# CLI Interface
def main():
    """CLI interface for the Agent Communication Hub"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Agent Communication Hub for ReactDjango-Hub')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start hub
    start_parser = subparsers.add_parser('start', help='Start the communication hub')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get hub status')
    status_parser.add_argument('--agent', help='Get status for specific agent')
    
    # Create task
    task_parser = subparsers.add_parser('task', help='Create a new task')
    task_parser.add_argument('title', help='Task title')
    task_parser.add_argument('--description', help='Task description')
    task_parser.add_argument('--agent', help='Target agent')
    task_parser.add_argument('--priority', choices=['critical', 'high', 'normal', 'low'],
                            default='normal', help='Task priority')
    
    # Share context
    context_parser = subparsers.add_parser('context', help='Share context between agents')
    context_parser.add_argument('key', help='Context key')
    context_parser.add_argument('value', help='Context value')
    context_parser.add_argument('--agent', required=True, help='Agent sharing the context')
    context_parser.add_argument('--ttl', type=int, help='Time to live in seconds')
    
    # Performance metrics
    metrics_parser = subparsers.add_parser('metrics', help='Get performance metrics')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        hub = AgentCommunicationHub()
        print("Agent Communication Hub started")
        print(f"Database: {hub.db_path}")
        print(f"Agents registered: {len(hub.agents)}")
        
        # Keep hub running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            hub.shutdown()
    
    elif args.command == 'status':
        hub = AgentCommunicationHub()
        
        if args.agent:
            status = hub.get_agent_status(args.agent)
            if status:
                print(f"Agent: {args.agent}")
                print(f"Status: {status.status.value}")
                print(f"Current Task: {status.current_task or 'None'}")
                print(f"Last Heartbeat: {status.last_heartbeat}")
            else:
                print(f"Agent {args.agent} not found")
        else:
            all_status = hub.get_all_agents_status()
            print("All Agents Status:")
            for agent, status in all_status.items():
                print(f"  {agent}: {status['status']}")
    
    elif args.command == 'task':
        hub = AgentCommunicationHub()
        
        priority_map = {
            'critical': MessagePriority.CRITICAL,
            'high': MessagePriority.HIGH,
            'normal': MessagePriority.NORMAL,
            'low': MessagePriority.LOW
        }
        
        task = hub.create_task(
            title=args.title,
            description=args.description or args.title,
            agent=args.agent,
            priority=priority_map[args.priority]
        )
        
        print(f"Task created: {task.id}")
        print(f"Assigned to: {task.agent}")
    
    elif args.command == 'context':
        hub = AgentCommunicationHub()
        hub.share_context(args.key, args.value, args.agent, args.ttl)
        print(f"Context shared: {args.key} = {args.value}")
    
    elif args.command == 'metrics':
        hub = AgentCommunicationHub()
        metrics = hub.get_performance_metrics()
        
        print("Performance Metrics:")
        for agent, data in metrics.items():
            print(f"\n{agent}:")
            print(f"  Total Tasks: {data['total_tasks']}")
            print(f"  Completed: {data['completed']}")
            print(f"  Failed: {data['failed']}")
            print(f"  Success Rate: {data['success_rate']:.1f}%")
            print(f"  Avg Completion: {data['average_completion_time']:.1f} minutes")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
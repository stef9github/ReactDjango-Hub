"""
Workflow Engine - State machine implementation for business process automation
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from statemachine import StateMachine, State
from statemachine.exceptions import TransitionNotAllowed

from models import WorkflowDefinition, WorkflowInstance, WorkflowHistory
from database import get_database_session

import logging
logger = logging.getLogger(__name__)

class DynamicWorkflowStateMachine(StateMachine):
    """
    Dynamic state machine that can be configured from database definitions
    """
    
    def __init__(self, definition: WorkflowDefinition, instance: WorkflowInstance, **kwargs):
        self.definition = definition
        self.instance = instance
        
        # Create states dynamically from definition
        self._create_states_from_definition()
        
        # Set initial state
        self.current_state = getattr(self, instance.current_state)
        
        super().__init__(**kwargs)
    
    def _create_states_from_definition(self):
        """Create state machine states from workflow definition"""
        if not self.definition.states:
            raise ValueError("Workflow definition must have states defined")
        
        # Create State objects and attach to class
        for state_config in self.definition.states:
            state_name = state_config.get('name')
            if not state_name:
                continue
                
            state_obj = State(
                name=state_name,
                initial=state_name == self.definition.initial_state
            )
            setattr(self, state_name, state_obj)
        
        # Create transitions from definition
        self._create_transitions_from_definition()
    
    def _create_transitions_from_definition(self):
        """Create transitions between states"""
        if not self.definition.transitions:
            return
        
        for transition_config in self.definition.transitions:
            from_state_name = transition_config.get('from')
            to_state_name = transition_config.get('to')
            action_name = transition_config.get('action', 'transition')
            
            if not from_state_name or not to_state_name:
                continue
            
            from_state = getattr(self, from_state_name, None)
            to_state = getattr(self, to_state_name, None)
            
            if from_state and to_state:
                # Create transition method dynamically
                transition_method = self._create_transition_method(
                    from_state, to_state, action_name, transition_config
                )
                setattr(self, action_name, transition_method)
    
    def _create_transition_method(self, from_state: State, to_state: State, 
                                action_name: str, config: Dict):
        """Create a transition method for a specific state change"""
        def transition_method(self, **kwargs):
            # Pre-transition validation
            if not self._validate_transition(from_state.name, to_state.name, action_name, **kwargs):
                raise TransitionNotAllowed(
                    f"Transition from {from_state.name} to {to_state.name} not allowed"
                )
            
            # Execute transition
            self._execute_transition(from_state.name, to_state.name, action_name, config, **kwargs)
            
            # Update current state
            self.current_state = to_state
        
        # Decorate the method to make it a proper transition
        from statemachine import transition
        return transition(from_state, to_state)(transition_method)
    
    def _validate_transition(self, from_state: str, to_state: str, action: str, **kwargs) -> bool:
        """Validate if transition is allowed based on business rules"""
        # Check definition validation
        if not self.definition.validate_transition(from_state, to_state, action):
            return False
        
        # Check business rules if defined
        business_rules = self.definition.business_rules or {}
        transition_rules = business_rules.get('transitions', {})
        rule_key = f"{from_state}_{to_state}"
        
        if rule_key in transition_rules:
            rule = transition_rules[rule_key]
            # TODO: Implement business rule validation logic
            pass
        
        return True
    
    def _execute_transition(self, from_state: str, to_state: str, action: str, 
                          config: Dict, **kwargs):
        """Execute the state transition and record history"""
        start_time = datetime.utcnow()
        
        try:
            # Update instance
            self.instance.previous_state = from_state
            self.instance.current_state = to_state
            self.instance.updated_at = start_time
            
            # Update context if provided
            if 'context' in kwargs:
                context_updates = kwargs['context']
                if not self.instance.context_data:
                    self.instance.context_data = {}
                self.instance.context_data.update(context_updates)
            
            # Update progress
            self.instance.update_progress()
            
            # Check if workflow is completed
            final_states = [state.get('name') for state in self.definition.states 
                          if state.get('is_final', False)]
            if to_state in final_states:
                self.instance.status = "completed"
                self.instance.completed_at = start_time
            
            # Create history entry
            duration_ms = str(int((datetime.utcnow() - start_time).total_seconds() * 1000))
            
            history_entry = WorkflowHistory.create_entry(
                instance_id=self.instance.id,
                from_state=from_state,
                to_state=to_state,
                action=action,
                triggered_by=kwargs.get('user_id'),
                trigger_type=kwargs.get('trigger_type', 'manual'),
                comment=kwargs.get('comment'),
                action_metadata={
                    'transition_config': config,
                    'action_data': kwargs.get('data', {})
                },
                context_snapshot=dict(self.instance.context_data) if self.instance.context_data else None,
                duration_ms=duration_ms,
                was_successful="true"
            )
            
            # Add to session for saving
            from database import SessionLocal
            with SessionLocal() as session:
                session.add(history_entry)
                session.add(self.instance)
                session.commit()
            
            logger.info(f"Workflow {self.instance.id} transitioned from {from_state} to {to_state}")
            
        except Exception as e:
            # Record failed transition
            error_duration = str(int((datetime.utcnow() - start_time).total_seconds() * 1000))
            
            history_entry = WorkflowHistory.create_entry(
                instance_id=self.instance.id,
                from_state=from_state,
                to_state=to_state,
                action=action,
                triggered_by=kwargs.get('user_id'),
                trigger_type=kwargs.get('trigger_type', 'manual'),
                comment=kwargs.get('comment'),
                action_metadata={'error': str(e)},
                duration_ms=error_duration,
                was_successful="false",
                error_message=str(e)
            )
            
            # Update instance error info
            self.instance.error_count = str(int(self.instance.error_count) + 1)
            self.instance.last_error = str(e)
            
            from database import SessionLocal
            with SessionLocal() as session:
                session.add(history_entry)
                session.add(self.instance)
                session.commit()
            
            logger.error(f"Workflow transition failed: {str(e)}")
            raise

class WorkflowEngine:
    """
    Main workflow engine for managing workflow instances
    """
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session
    
    def create_workflow_instance(self, definition_id: str, entity_id: str, 
                                entity_type: str = None, title: str = None,
                                context: Dict = None, assigned_to: str = None,
                                organization_id: str = None, created_by: str = None) -> WorkflowInstance:
        """Create a new workflow instance"""
        
        # Get workflow definition
        definition = self.db_session.query(WorkflowDefinition).filter(
            WorkflowDefinition.id == definition_id,
            WorkflowDefinition.is_active == True
        ).first()
        
        if not definition:
            raise ValueError(f"Workflow definition {definition_id} not found or inactive")
        
        # Create instance
        instance = WorkflowInstance(
            id=uuid.uuid4(),
            definition_id=definition_id,
            entity_id=entity_id,
            entity_type=entity_type,
            title=title or f"Workflow for {entity_id}",
            current_state=definition.initial_state,
            context_data=context or {},
            assigned_to=assigned_to,
            organization_id=organization_id,
            created_by=created_by,
            started_at=datetime.utcnow(),
            status="active"
        )
        
        # Save to database
        self.db_session.add(instance)
        self.db_session.flush()  # Get the ID
        
        # Create initial history entry
        history_entry = WorkflowHistory.create_entry(
            instance_id=instance.id,
            to_state=definition.initial_state,
            action="create",
            triggered_by=created_by,
            trigger_type="manual",
            comment="Workflow instance created",
            context_snapshot=dict(context) if context else None
        )
        
        self.db_session.add(history_entry)
        
        # Update definition usage count
        definition.usage_count = (definition.usage_count or 0) + 1
        self.db_session.add(definition)
        
        self.db_session.commit()
        
        logger.info(f"Created workflow instance {instance.id} from definition {definition_id}")
        
        return instance
    
    def advance_workflow(self, instance_id: str, action: str, 
                        user_id: str = None, comment: str = None,
                        data: Dict = None, context_updates: Dict = None) -> WorkflowInstance:
        """Advance workflow to next state"""
        
        # Get instance with definition
        instance = self.db_session.query(WorkflowInstance).filter(
            WorkflowInstance.id == instance_id
        ).first()
        
        if not instance:
            raise ValueError(f"Workflow instance {instance_id} not found")
        
        if instance.status != "active":
            raise ValueError(f"Workflow instance {instance_id} is not active (status: {instance.status})")
        
        # Get definition
        definition = instance.definition
        if not definition:
            raise ValueError(f"Workflow definition not found for instance {instance_id}")
        
        # Find target state for this action
        valid_transitions = definition.get_valid_transitions(instance.current_state)
        target_transition = None
        
        for transition in valid_transitions:
            if transition.get('action') == action:
                target_transition = transition
                break
        
        if not target_transition:
            available_actions = [t.get('action') for t in valid_transitions]
            raise ValueError(
                f"Action '{action}' not available from state '{instance.current_state}'. "
                f"Available actions: {available_actions}"
            )
        
        target_state = target_transition.get('to')
        
        # Create state machine and execute transition
        state_machine = DynamicWorkflowStateMachine(definition, instance)
        
        # Execute the transition
        transition_method = getattr(state_machine, action, None)
        if not transition_method:
            raise ValueError(f"Transition method '{action}' not found")
        
        transition_method(
            user_id=user_id,
            comment=comment,
            data=data or {},
            context=context_updates or {}
        )
        
        # Refresh instance from database
        self.db_session.refresh(instance)
        
        return instance
    
    def get_workflow_status(self, instance_id: str) -> Dict:
        """Get comprehensive workflow status"""
        instance = self.db_session.query(WorkflowInstance).filter(
            WorkflowInstance.id == instance_id
        ).first()
        
        if not instance:
            raise ValueError(f"Workflow instance {instance_id} not found")
        
        # Get available actions
        available_actions = instance.get_available_actions()
        
        # Get recent history
        recent_history = instance.history.limit(10).all()
        
        return {
            "instance_id": str(instance.id),
            "definition_id": str(instance.definition_id),
            "entity_id": instance.entity_id,
            "current_state": instance.current_state,
            "previous_state": instance.previous_state,
            "status": instance.status,
            "progress_percentage": instance.progress_percentage,
            "started_at": instance.started_at.isoformat(),
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "due_date": instance.due_date.isoformat() if instance.due_date else None,
            "is_overdue": instance.is_overdue,
            "assigned_to": instance.assigned_to,
            "available_actions": available_actions,
            "context_data": instance.context_data,
            "recent_history": [
                {
                    "from_state": h.from_state,
                    "to_state": h.to_state,
                    "action": h.action,
                    "triggered_by": h.triggered_by,
                    "created_at": h.created_at.isoformat(),
                    "comment": h.comment,
                    "was_successful": h.is_successful
                }
                for h in recent_history
            ]
        }
    
    def get_user_workflows(self, user_id: str, organization_id: str = None,
                          status: str = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get workflows for a specific user"""
        query = self.db_session.query(WorkflowInstance).filter(
            WorkflowInstance.assigned_to == user_id
        )
        
        if organization_id:
            query = query.filter(WorkflowInstance.organization_id == organization_id)
        
        if status:
            query = query.filter(WorkflowInstance.status == status)
        
        instances = query.order_by(
            WorkflowInstance.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            {
                "instance_id": str(instance.id),
                "title": instance.title,
                "entity_id": instance.entity_id,
                "current_state": instance.current_state,
                "status": instance.status,
                "progress_percentage": instance.progress_percentage,
                "created_at": instance.created_at.isoformat(),
                "due_date": instance.due_date.isoformat() if instance.due_date else None,
                "is_overdue": instance.is_overdue,
                "definition_name": instance.definition.name if instance.definition else None
            }
            for instance in instances
        ]
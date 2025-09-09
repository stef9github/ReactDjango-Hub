"""
Notification Template Engine
Jinja2-based template rendering with multi-channel support and variable validation
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import uuid
import json
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateNotFound, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
import bleach
from sqlalchemy.orm import Session
import aiofiles

from .database import get_db_session
from .models import NotificationTemplate, NotificationCategory, NotificationChannel
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


class DatabaseTemplateLoader(BaseLoader):
    """Custom Jinja2 loader that loads templates from database"""
    
    def __init__(self):
        self.db_session = None
    
    async def get_db_session(self):
        if not self.db_session:
            self.db_session = get_db_session()
        return self.db_session
    
    def get_source(self, environment, template_name):
        """Load template from database"""
        try:
            # Parse template name: "template_id:channel" or just "template_id"
            parts = template_name.split(":")
            template_id = parts[0]
            channel = parts[1] if len(parts) > 1 else None
            
            # Query database for template
            session = get_db_session()
            query = session.query(NotificationTemplate).filter(
                NotificationTemplate.id == uuid.UUID(template_id),
                NotificationTemplate.is_active == True
            )
            
            if channel:
                query = query.filter(NotificationTemplate.channel == NotificationChannel(channel))
            
            template = query.first()
            
            if not template:
                raise TemplateNotFound(template_name)
            
            source = template.content
            mtime = template.updated_at.timestamp() if template.updated_at else datetime.utcnow().timestamp()
            
            def uptodate():
                # Check if template has been modified
                current_template = session.query(NotificationTemplate).filter(
                    NotificationTemplate.id == template.id
                ).first()
                return current_template and current_template.updated_at.timestamp() == mtime
            
            return source, None, uptodate
            
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            raise TemplateNotFound(template_name)


class TemplateEngine:
    """Advanced template engine for multi-channel notifications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.template_dirs = self.config.get("template_dirs", ["templates"])
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.cache_ttl = self.config.get("cache_ttl_seconds", 3600)
        self.sandbox_enabled = self.config.get("sandbox_enabled", True)
        self.auto_escape = self.config.get("auto_escape", True)
        self.redis_client = None
        
        # Initialize Jinja2 environment
        self._setup_jinja_env()
        
    def _setup_jinja_env(self):
        """Setup Jinja2 environment with appropriate settings"""
        if self.sandbox_enabled:
            # Use sandboxed environment for security
            self.jinja_env = SandboxedEnvironment(
                loader=DatabaseTemplateLoader(),
                autoescape=self.auto_escape,
                trim_blocks=True,
                lstrip_blocks=True,
                enable_async=True
            )
        else:
            self.jinja_env = Environment(
                loader=DatabaseTemplateLoader(),
                autoescape=self.auto_escape,
                trim_blocks=True,
                lstrip_blocks=True,
                enable_async=True
            )
        
        # Add custom filters
        self._add_custom_filters()
        
        # Add custom functions
        self._add_custom_functions()
    
    def _add_custom_filters(self):
        """Add custom Jinja2 filters"""
        
        def format_currency(value, currency="USD"):
            """Format value as currency"""
            try:
                return f"{float(value):.2f} {currency}"
            except (ValueError, TypeError):
                return str(value)
        
        def format_date(value, format="%Y-%m-%d"):
            """Format datetime value"""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    return value
            
            if isinstance(value, datetime):
                return value.strftime(format)
            return str(value)
        
        def truncate_words(value, length=50):
            """Truncate text to specified word count"""
            words = str(value).split()
            if len(words) <= length:
                return str(value)
            return ' '.join(words[:length]) + '...'
        
        def sanitize_html(value):
            """Sanitize HTML content"""
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
            allowed_attributes = {'a': ['href']}
            return bleach.clean(str(value), tags=allowed_tags, attributes=allowed_attributes)
        
        # Register filters
        self.jinja_env.filters['currency'] = format_currency
        self.jinja_env.filters['date'] = format_date
        self.jinja_env.filters['truncate_words'] = truncate_words
        self.jinja_env.filters['sanitize'] = sanitize_html
    
    def _add_custom_functions(self):
        """Add custom Jinja2 global functions"""
        
        def current_year():
            """Get current year"""
            return datetime.now().year
        
        def current_date(format="%Y-%m-%d"):
            """Get current date formatted"""
            return datetime.now().strftime(format)
        
        def url_for(endpoint, **values):
            """Generate URL for endpoint (placeholder)"""
            # This would integrate with your routing system
            base_url = self.config.get("base_url", "https://example.com")
            return f"{base_url}/{endpoint}"
        
        # Register global functions
        self.jinja_env.globals['current_year'] = current_year
        self.jinja_env.globals['current_date'] = current_date
        self.jinja_env.globals['url_for'] = url_for
    
    async def _get_redis_client(self):
        """Get Redis client for caching"""
        if not self.redis_client:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def render_template(
        self, 
        template_id: str, 
        variables: Dict[str, Any],
        channel: Optional[NotificationChannel] = None
    ) -> Dict[str, str]:
        """
        Render template with variables
        
        Args:
            template_id: UUID of template to render
            variables: Template variables
            channel: Notification channel for channel-specific templates
            
        Returns:
            Dict with 'subject' and 'content' keys
        """
        try:
            # Build template name for loader
            template_name = template_id
            if channel:
                template_name = f"{template_id}:{channel.value}"
            
            # Check cache first
            if self.cache_enabled:
                cached_result = await self._get_from_cache(template_name, variables)
                if cached_result:
                    return cached_result
            
            # Load and render template
            template = self.jinja_env.get_template(template_name)
            
            # Get template metadata
            template_data = await self._get_template_data(template_id)
            
            # Validate variables
            self._validate_variables(variables, template_data.get("variables", {}))
            
            # Render subject and content
            subject = ""
            if template_data.get("subject"):
                subject_template = self.jinja_env.from_string(template_data["subject"])
                subject = await subject_template.render_async(**variables)
            
            content = await template.render_async(**variables)
            
            # Post-process based on channel
            if channel:
                content = await self._post_process_content(content, channel)
            
            result = {
                "subject": subject.strip(),
                "content": content.strip()
            }
            
            # Cache result
            if self.cache_enabled:
                await self._cache_result(template_name, variables, result)
            
            return result
            
        except TemplateNotFound:
            raise ValueError(f"Template {template_id} not found")
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {str(e)}")
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise
    
    async def _get_template_data(self, template_id: str) -> Dict[str, Any]:
        """Get template metadata from database"""
        try:
            async with get_db_session() as session:
                template = await session.get(NotificationTemplate, uuid.UUID(template_id))
                if not template:
                    raise ValueError(f"Template {template_id} not found")
                
                return {
                    "id": str(template.id),
                    "name": template.name,
                    "subject": template.subject,
                    "variables": template.variables or {},
                    "channel": template.channel.value,
                    "language": template.language,
                    "version": template.version
                }
                
        except Exception as e:
            logger.error(f"Failed to get template data for {template_id}: {e}")
            raise
    
    def _validate_variables(self, variables: Dict[str, Any], required_variables: Dict[str, str]):
        """Validate that all required variables are provided with correct types"""
        missing_vars = []
        type_errors = []
        
        for var_name, var_type in required_variables.items():
            if var_name not in variables:
                missing_vars.append(var_name)
                continue
            
            value = variables[var_name]
            
            # Type checking
            if var_type == "string" and not isinstance(value, str):
                type_errors.append(f"{var_name} should be string, got {type(value).__name__}")
            elif var_type == "number" and not isinstance(value, (int, float)):
                type_errors.append(f"{var_name} should be number, got {type(value).__name__}")
            elif var_type == "boolean" and not isinstance(value, bool):
                type_errors.append(f"{var_name} should be boolean, got {type(value).__name__}")
            elif var_type == "date" and not isinstance(value, (str, datetime)):
                type_errors.append(f"{var_name} should be date string or datetime, got {type(value).__name__}")
        
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        
        if type_errors:
            raise ValueError(f"Variable type errors: {'; '.join(type_errors)}")
    
    async def _post_process_content(self, content: str, channel: NotificationChannel) -> str:
        """Post-process content based on notification channel"""
        if channel == NotificationChannel.SMS:
            # Truncate for SMS
            return content[:160]
        
        elif channel == NotificationChannel.EMAIL:
            # Ensure HTML is clean for email
            if "<html>" in content.lower() or "<body>" in content.lower():
                return bleach.clean(content, tags=bleach.ALLOWED_TAGS + ['html', 'body', 'head', 'title'])
        
        elif channel == NotificationChannel.PUSH:
            # Truncate for push notifications
            return content[:1000]
        
        return content
    
    async def _get_from_cache(self, template_name: str, variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Get rendered template from cache"""
        try:
            redis_client = await self._get_redis_client()
            cache_key = f"template_cache:{template_name}:{hash(frozenset(variables.items()))}"
            
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
        except Exception as e:
            logger.warning(f"Failed to get template from cache: {e}")
        
        return None
    
    async def _cache_result(self, template_name: str, variables: Dict[str, Any], result: Dict[str, str]):
        """Cache rendered template result"""
        try:
            redis_client = await self._get_redis_client()
            cache_key = f"template_cache:{template_name}:{hash(frozenset(variables.items()))}"
            
            await redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(result)
            )
            
        except Exception as e:
            logger.warning(f"Failed to cache template result: {e}")
    
    async def preview_template(
        self, 
        template_content: str,
        subject: str,
        variables: Dict[str, Any],
        channel: Optional[NotificationChannel] = None
    ) -> Dict[str, str]:
        """
        Preview template rendering without saving to database
        
        Args:
            template_content: Template content string
            subject: Template subject string
            variables: Template variables
            channel: Notification channel
            
        Returns:
            Dict with 'subject' and 'content' keys
        """
        try:
            # Render subject
            rendered_subject = ""
            if subject:
                subject_template = self.jinja_env.from_string(subject)
                rendered_subject = await subject_template.render_async(**variables)
            
            # Render content
            content_template = self.jinja_env.from_string(template_content)
            rendered_content = await content_template.render_async(**variables)
            
            # Post-process based on channel
            if channel:
                rendered_content = await self._post_process_content(rendered_content, channel)
            
            return {
                "subject": rendered_subject.strip(),
                "content": rendered_content.strip()
            }
            
        except Exception as e:
            logger.error(f"Template preview failed: {e}")
            raise ValueError(f"Template preview error: {str(e)}")
    
    async def validate_template_syntax(self, template_content: str, subject: str = "") -> Dict[str, Any]:
        """
        Validate template syntax without rendering
        
        Args:
            template_content: Template content to validate
            subject: Subject template to validate
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        try:
            # Validate content template
            self.jinja_env.from_string(template_content)
        except TemplateSyntaxError as e:
            errors.append(f"Content template syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Content template error: {str(e)}")
        
        try:
            # Validate subject template
            if subject:
                self.jinja_env.from_string(subject)
        except TemplateSyntaxError as e:
            errors.append(f"Subject template syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Subject template error: {str(e)}")
        
        # Check for potentially problematic patterns
        if "{{" in template_content and "}}" not in template_content:
            warnings.append("Unclosed template variable detected")
        
        if len(template_content) > 50000:
            warnings.append("Template content is very large (>50KB)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def clear_cache(self, template_id: Optional[str] = None):
        """Clear template cache"""
        try:
            redis_client = await self._get_redis_client()
            
            if template_id:
                # Clear cache for specific template
                pattern = f"template_cache:{template_id}*"
            else:
                # Clear all template cache
                pattern = "template_cache:*"
            
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} template cache entries")
            
        except Exception as e:
            logger.error(f"Failed to clear template cache: {e}")
    
    async def get_template_variables(self, template_content: str) -> List[str]:
        """Extract variable names from template content"""
        try:
            import re
            
            # Find all {{ variable }} patterns
            variable_pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s*(?:\|[^}]*)?\}\}'
            variables = re.findall(variable_pattern, template_content)
            
            # Remove duplicates and filter out built-in functions
            unique_vars = list(set(variables))
            built_ins = ['current_year', 'current_date', 'url_for']
            
            return [var for var in unique_vars if not any(var.startswith(builtin) for builtin in built_ins)]
            
        except Exception as e:
            logger.error(f"Failed to extract template variables: {e}")
            return []


# Global template engine instance
template_engine = TemplateEngine()
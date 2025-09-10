"""
Content Service Schemas

This module contains Pydantic models for API request/response validation
and data serialization for the content management service.
"""

from .document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentDetailResponse
)
from .processing import (
    ProcessingJobRequest,
    ProcessingJobResponse,
    ProcessingStatusResponse
)
from .search import (
    SearchRequest,
    SearchResponse,
    SemanticSearchRequest,
    SuggestionResponse
)
from .permission import (
    GrantUserPermissionRequest,
    GrantRolePermissionRequest,
    ShareDocumentRequest,
    ShareDocumentResponse,
    DocumentPermissionSummary,
    EffectivePermissionsResponse,
    DocumentAccessCheckRequest,
    DocumentAccessCheckResponse
)
from .common import (
    PaginationParams,
    ErrorResponse,
    SuccessResponse
)

__all__ = [
    "DocumentCreate",
    "DocumentUpdate", 
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentDetailResponse",
    "ProcessingJobRequest",
    "ProcessingJobResponse",
    "ProcessingStatusResponse",
    "SearchRequest",
    "SearchResponse",
    "SemanticSearchRequest",
    "SuggestionResponse",
    "GrantUserPermissionRequest",
    "GrantRolePermissionRequest",
    "ShareDocumentRequest",
    "ShareDocumentResponse",
    "DocumentPermissionSummary",
    "EffectivePermissionsResponse",
    "DocumentAccessCheckRequest",
    "DocumentAccessCheckResponse",
    "PaginationParams",
    "ErrorResponse",
    "SuccessResponse"
]
"""
Search-related schemas for the content service API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator

from .common import BaseResponse, PaginationInfo


class SearchType(str, Enum):
    """Types of search operations."""
    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    VISUAL = "visual"
    METADATA = "metadata"
    HYBRID = "hybrid"


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class SearchRequest(BaseModel):
    """Full-text search request."""
    query: str = Field(min_length=1, max_length=1000, description="Search query")
    search_type: SearchType = Field(default=SearchType.FULL_TEXT, description="Type of search")
    
    # Filters
    document_types: Optional[List[str]] = Field(default=None, description="Filter by document types")
    classifications: Optional[List[str]] = Field(default=None, description="Filter by classifications")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    created_after: Optional[datetime] = Field(default=None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(default=None, description="Filter by creation date")
    file_size_min: Optional[int] = Field(default=None, ge=0, description="Minimum file size")
    file_size_max: Optional[int] = Field(default=None, ge=0, description="Maximum file size")
    
    # Search options
    fuzzy: bool = Field(default=False, description="Enable fuzzy matching")
    exact_phrase: bool = Field(default=False, description="Search for exact phrase")
    include_content: bool = Field(default=True, description="Search in document content")
    include_metadata: bool = Field(default=True, description="Search in metadata")
    
    # Result options
    highlight: bool = Field(default=True, description="Highlight search terms")
    snippet_length: int = Field(default=200, ge=50, le=1000, description="Snippet length in characters")
    
    # Pagination and sorting
    limit: int = Field(default=20, ge=1, le=100, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    sort_by: str = Field(default="relevance", description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")
    
    @validator('file_size_max')
    def validate_file_size_range(cls, v, values):
        if v is not None and 'file_size_min' in values and values['file_size_min'] is not None:
            if v < values['file_size_min']:
                raise ValueError('file_size_max must be greater than file_size_min')
        return v


class SemanticSearchRequest(BaseModel):
    """Semantic search request using embeddings."""
    query: str = Field(min_length=1, max_length=1000, description="Natural language query")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    include_snippets: bool = Field(default=True, description="Include text snippets in results")


class SearchHighlight(BaseModel):
    """Highlighted text snippet."""
    field: str = Field(description="Field where match was found")
    fragment: str = Field(description="Text fragment with highlights")
    start_offset: int = Field(description="Start position in original text")
    end_offset: int = Field(description="End position in original text")


class SearchResultItem(BaseModel):
    """Individual search result item."""
    document_id: UUID = Field(description="Document ID")
    filename: str = Field(description="Document filename")
    title: Optional[str] = Field(default=None, description="Document title")
    content_type: str = Field(description="MIME type")
    file_size: int = Field(description="File size in bytes")
    
    # Relevance
    relevance_score: float = Field(description="Search relevance score")
    similarity_score: Optional[float] = Field(default=None, description="Semantic similarity score")
    
    # Content
    snippet: Optional[str] = Field(default=None, description="Content snippet")
    highlights: List[SearchHighlight] = Field(default_factory=list, description="Highlighted matches")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Document tags")
    classification: str = Field(description="Security classification")
    author: Optional[str] = Field(default=None, description="Document author")
    created_at: datetime = Field(description="Creation timestamp")
    
    # URLs
    download_url: str = Field(description="Download URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")


class SearchResponse(BaseResponse):
    """Search results response."""
    query: str = Field(description="Original search query")
    search_type: SearchType = Field(description="Type of search performed")
    results: List[SearchResultItem] = Field(description="Search results")
    
    # Statistics
    total_results: int = Field(description="Total number of matching documents")
    search_time_ms: int = Field(description="Search execution time in milliseconds")
    max_score: float = Field(description="Highest relevance score")
    
    # Pagination
    pagination: PaginationInfo = Field(description="Pagination information")
    
    # Facets and aggregations
    facets: Dict[str, Dict[str, int]] = Field(description="Search facets")
    suggestions: List[str] = Field(default_factory=list, description="Query suggestions")
    
    # Applied filters
    filters_applied: Dict[str, Any] = Field(description="Filters that were applied")


class SearchSuggestionRequest(BaseModel):
    """Request for search suggestions."""
    prefix: str = Field(min_length=1, max_length=100, description="Search prefix")
    limit: int = Field(default=10, ge=1, le=20, description="Maximum suggestions")
    context: Optional[str] = Field(default=None, description="Search context")


class SuggestionItem(BaseModel):
    """Individual search suggestion."""
    text: str = Field(description="Suggested search term")
    frequency: int = Field(description="How often this term appears")
    type: str = Field(description="Suggestion type (term, phrase, document)")


class SuggestionResponse(BaseResponse):
    """Search suggestions response."""
    prefix: str = Field(description="Original search prefix")
    suggestions: List[SuggestionItem] = Field(description="Suggested search terms")
    response_time_ms: int = Field(description="Response time in milliseconds")


class SavedSearchRequest(BaseModel):
    """Request to save a search query."""
    name: str = Field(min_length=1, max_length=100, description="Search name")
    description: Optional[str] = Field(default=None, max_length=500, description="Search description")
    search_params: SearchRequest = Field(description="Search parameters to save")
    alert_frequency: Optional[str] = Field(
        default=None,
        pattern="^(never|daily|weekly|monthly)$",
        description="Alert frequency for new matches"
    )


class SavedSearchResponse(BaseResponse):
    """Saved search response."""
    id: UUID = Field(description="Saved search ID")
    name: str = Field(description="Search name")
    description: Optional[str] = Field(description="Search description")
    search_params: SearchRequest = Field(description="Saved search parameters")
    alert_frequency: Optional[str] = Field(description="Alert frequency")
    
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="Creator user ID")
    last_executed: Optional[datetime] = Field(default=None, description="Last execution time")
    execution_count: int = Field(default=0, description="Number of times executed")


class SearchAnalytics(BaseResponse):
    """Search analytics and insights."""
    period_start: datetime = Field(description="Analytics period start")
    period_end: datetime = Field(description="Analytics period end")
    
    # Query statistics
    total_searches: int = Field(description="Total number of searches")
    unique_queries: int = Field(description="Number of unique search queries")
    average_results_per_query: float = Field(description="Average results per search")
    
    # Performance statistics
    average_response_time_ms: float = Field(description="Average search response time")
    slowest_queries: List[Dict[str, Any]] = Field(description="Slowest search queries")
    
    # Popular searches
    top_queries: List[Dict[str, Any]] = Field(description="Most frequent search queries")
    top_filters: List[Dict[str, Any]] = Field(description="Most used filters")
    
    # User behavior
    zero_result_queries: List[str] = Field(description="Queries that returned no results")
    click_through_rate: float = Field(description="Percentage of searches leading to downloads")
    
    # Content insights
    most_searched_documents: List[Dict[str, Any]] = Field(description="Most frequently found documents")
    search_coverage: float = Field(description="Percentage of documents found in searches")


class VisualSearchRequest(BaseModel):
    """Visual search request for image similarity."""
    query_image: Optional[str] = Field(default=None, description="Base64 encoded query image")
    query_document_id: Optional[UUID] = Field(default=None, description="Use existing document as query")
    similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Minimum similarity")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    
    @validator('query_document_id')
    def validate_query_source(cls, v, values):
        query_image = values.get('query_image')
        if not query_image and not v:
            raise ValueError('Either query_image or query_document_id must be provided')
        if query_image and v:
            raise ValueError('Cannot specify both query_image and query_document_id')
        return v
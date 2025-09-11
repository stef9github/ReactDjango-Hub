from ninja import NinjaAPI
from typing import List
from apps.analytics.models import AnalyticsRecord
from apps.analytics.ninja_schemas import AnalyticsRecordSchema, AnalyticsRecordCreateSchema
from django.shortcuts import get_object_or_404

# Import business API router
from apps.business.api import router as business_router

# Import authentication utilities
from apps.core.auth import jwt_auth, get_user_queryset, get_current_user_or_403

api = NinjaAPI(
    title="ReactDjango Hub Business Logic API", 
    description="Business logic endpoints - Authentication handled by auth-service on port 8001",
    version="1.0.0"
)

# Register business endpoints
api.add_router("/business", business_router)

# Health check endpoint (no authentication required)
@api.get("/health", tags=["System"])
def health_check(request):
    """Health check endpoint - no authentication required"""
    return {"status": "healthy", "service": "django-backend"}


@api.get("/analytics/records", response=List[AnalyticsRecordSchema], tags=["Analytics"], auth=jwt_auth)
def list_analytics_records(request):
    """List all analytics records for the authenticated user's organization"""
    user_context = get_current_user_or_403()
    return list(get_user_queryset(AnalyticsRecord, user_context))


@api.get("/analytics/records/{record_id}", response=AnalyticsRecordSchema, tags=["Analytics"], auth=jwt_auth)
def get_analytics_record(request, record_id: str):
    """Get a specific analytics record by ID from the user's organization"""
    user_context = get_current_user_or_403()
    queryset = get_user_queryset(AnalyticsRecord, user_context)
    return get_object_or_404(queryset, id=record_id)


@api.post("/analytics/records", response=AnalyticsRecordSchema, tags=["Analytics"], auth=jwt_auth)
def create_analytics_record(request, payload: AnalyticsRecordCreateSchema):
    """Create a new analytics record for the authenticated user's organization"""
    user_context = get_current_user_or_403()
    # The organization_id and created_by fields will be automatically set by BaseModel.save()
    record = AnalyticsRecord.objects.create(**payload.dict())
    return record


@api.put("/analytics/records/{record_id}", response=AnalyticsRecordSchema, tags=["Analytics"], auth=jwt_auth)
def update_analytics_record(request, record_id: str, payload: AnalyticsRecordCreateSchema):
    """Update an existing analytics record in the user's organization"""
    user_context = get_current_user_or_403()
    queryset = get_user_queryset(AnalyticsRecord, user_context)
    record = get_object_or_404(queryset, id=record_id)
    for attr, value in payload.dict().items():
        setattr(record, attr, value)
    record.save()  # updated_by will be automatically set by BaseModel.save()
    return record


@api.delete("/analytics/records/{record_id}", tags=["Analytics"], auth=jwt_auth)
def delete_analytics_record(request, record_id: str):
    """Delete an analytics record (soft delete) from the user's organization"""
    user_context = get_current_user_or_403()
    queryset = get_user_queryset(AnalyticsRecord, user_context)
    record = get_object_or_404(queryset, id=record_id)
    record.soft_delete()  # Use soft delete instead of hard delete
    return {"message": "Record deleted successfully"}
from ninja import NinjaAPI
from typing import List
from apps.analytics.models import AnalyticsRecord
from apps.analytics.ninja_schemas import AnalyticsRecordSchema, AnalyticsRecordCreateSchema
from django.shortcuts import get_object_or_404

# TODO: Add auth-service integration
# from apps.core.auth_integration import require_auth, get_current_user

api = NinjaAPI(
    title="ReactDjango Hub Business Logic API", 
    description="Business logic endpoints - Authentication handled by auth-service on port 8001",
    version="1.0.0"
)


@api.get("/analytics/records", response=List[AnalyticsRecordSchema], tags=["Analytics"])
def list_analytics_records(request):
    """List all analytics records"""
    return list(AnalyticsRecord.objects.all())


@api.get("/analytics/records/{record_id}", response=AnalyticsRecordSchema, tags=["Analytics"])
def get_analytics_record(request, record_id: str):
    """Get a specific analytics record by ID"""
    return get_object_or_404(AnalyticsRecord, id=record_id)


@api.post("/analytics/records", response=AnalyticsRecordSchema, tags=["Analytics"])
def create_analytics_record(request, payload: AnalyticsRecordCreateSchema):
    """Create a new analytics record"""
    record = AnalyticsRecord.objects.create(**payload.dict())
    return record


@api.put("/analytics/records/{record_id}", response=AnalyticsRecordSchema, tags=["Analytics"])
def update_analytics_record(request, record_id: str, payload: AnalyticsRecordCreateSchema):
    """Update an existing analytics record"""
    record = get_object_or_404(AnalyticsRecord, id=record_id)
    for attr, value in payload.dict().items():
        setattr(record, attr, value)
    record.save()
    return record


@api.delete("/analytics/records/{record_id}", tags=["Analytics"])
def delete_analytics_record(request, record_id: str):
    """Delete an analytics record"""
    record = get_object_or_404(AnalyticsRecord, id=record_id)
    record.delete()
    return {"message": "Record deleted successfully"}
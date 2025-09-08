from ninja import Schema
from datetime import datetime
from typing import Optional
import uuid


class AnalyticsRecordSchema(Schema):
    """Schema for Analytics Record output"""
    id: uuid.UUID
    metric_name: str
    metric_value: float
    created_at: datetime
    updated_at: datetime


class AnalyticsRecordCreateSchema(Schema):
    """Schema for creating Analytics Record"""
    metric_name: str
    metric_value: float
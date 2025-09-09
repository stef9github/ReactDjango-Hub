"""Multi-Factor Authentication API endpoints"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from app.api.deps import (
    get_mfa_service, get_current_user, get_event_publisher
)
from app.schemas.mfa import (
    MFASetupRequest, MFASetupResponse, MFAChallengeRequest,
    MFAChallengeResponse, MFAVerifyRequest, MFAVerifyResponse,
    MFAMethodResponse, RegenerateBackupCodesResponse
)
from app.services.mfa_service import MFAService
from app.utils.messaging import EventPublisher

router = APIRouter(prefix="/mfa", tags=["Multi-Factor Authentication"])


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa_method(
    request: MFASetupRequest,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """Setup new MFA method (email, SMS, TOTP)"""
    try:
        mfa_data = await mfa_service.setup_mfa_method(
            user_id=current_user["user_id"],
            method_type=request.method_type,
            phone_number=request.phone_number,
            backup_email=request.backup_email
        )
        
        # Publish MFA setup event
        await event_publisher.publish_event("mfa.method_setup", {
            "user_id": current_user["user_id"],
            "method_type": request.method_type.value,
            "method_id": mfa_data["method_id"]
        })
        
        return MFASetupResponse(**mfa_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/methods", response_model=List[MFAMethodResponse])
async def list_mfa_methods(
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """List user's configured MFA methods"""
    try:
        methods = await mfa_service.get_user_mfa_methods(current_user["user_id"])
        return [MFAMethodResponse(**method) for method in methods]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve MFA methods"
        )


@router.post("/challenge", response_model=MFAChallengeResponse)
async def initiate_mfa_challenge(
    request: MFAChallengeRequest,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """Initiate MFA challenge (send code)"""
    try:
        challenge_data = await mfa_service.create_mfa_challenge(
            user_id=current_user["user_id"],
            method_type=request.method_type,
            method_id=request.method_id
        )
        
        return MFAChallengeResponse(**challenge_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify", response_model=MFAVerifyResponse)
async def verify_mfa_challenge(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """Verify MFA challenge response"""
    try:
        verification_result = await mfa_service.verify_mfa_challenge(
            challenge_id=request.challenge_id,
            code=request.code,
            user_id=current_user["user_id"]
        )
        
        # Publish MFA verification event
        await event_publisher.publish_event("mfa.verification_completed", {
            "user_id": current_user["user_id"],
            "challenge_id": request.challenge_id,
            "verified": verification_result["verified"]
        })
        
        return MFAVerifyResponse(**verification_result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/methods/{method_id}")
async def remove_mfa_method(
    method_id: str,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """Remove MFA method"""
    try:
        await mfa_service.remove_mfa_method(
            user_id=current_user["user_id"],
            method_id=method_id
        )
        
        # Publish MFA removal event
        await event_publisher.publish_event("mfa.method_removed", {
            "user_id": current_user["user_id"],
            "method_id": method_id
        })
        
        return {"message": "MFA method removed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/backup-codes/regenerate", response_model=RegenerateBackupCodesResponse)
async def regenerate_backup_codes(
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """Generate new backup codes"""
    try:
        backup_codes_data = await mfa_service.regenerate_backup_codes(
            current_user["user_id"]
        )
        
        # Publish backup codes regeneration event
        await event_publisher.publish_event("mfa.backup_codes_regenerated", {
            "user_id": current_user["user_id"]
        })
        
        return RegenerateBackupCodesResponse(**backup_codes_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
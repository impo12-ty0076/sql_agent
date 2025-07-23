"""
API endpoints for policy management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..core.dependencies import get_current_admin_user, get_db
from ..models.user import UserResponse
from ..models.policy import (
    PolicyCreate,
    PolicyUpdate,
    PolicyResponse,
    PaginatedPolicies,
    PolicyType,
    PolicyStatus,
    PolicyFilterParams,
    UserPermissionPolicySettings,
    QueryLimitPolicySettings,
    SecurityPolicySettings
)
from ..services.policy_service import PolicyService

router = APIRouter()

@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: PolicyCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    정책 생성 (관리자 전용)
    
    새로운 정책을 생성합니다.
    
    - **policy_data**: 생성할 정책 데이터
    """
    try:
        return await PolicyService.create_policy(
            db=db,
            policy_data=policy_data,
            created_by=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=PaginatedPolicies)
async def get_policies(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(50, ge=1, le=100, description="페이지당 정책 수"),
    policy_type: Optional[PolicyType] = None,
    status: Optional[PolicyStatus] = None,
    role: Optional[str] = None,
    search_term: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    정책 목록 조회 (관리자 전용)
    
    다양한 필터링 옵션을 사용하여 정책 목록을 조회합니다.
    
    - **page**: 페이지 번호
    - **page_size**: 페이지당 정책 수
    - **policy_type**: 정책 유형 필터
    - **status**: 정책 상태 필터
    - **role**: 적용 대상 역할 필터
    - **search_term**: 검색어 (이름 및 설명에서 검색)
    """
    filters = PolicyFilterParams(
        policy_type=policy_type,
        status=status,
        role=role,
        search_term=search_term,
        created_by=None  # 모든 정책 조회
    )
    
    return await PolicyService.get_paginated_policies(
        db=db,
        page=page,
        page_size=page_size,
        filters=filters
    )

@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    정책 상세 조회 (관리자 전용)
    
    특정 정책의 상세 정보를 조회합니다.
    
    - **policy_id**: 조회할 정책 ID
    """
    policy = await PolicyService.get_policy(db=db, policy_id=policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="정책을 찾을 수 없습니다."
        )
    
    return policy

@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    policy_data: PolicyUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    정책 수정 (관리자 전용)
    
    특정 정책을 수정합니다.
    
    - **policy_id**: 수정할 정책 ID
    - **policy_data**: 수정할 정책 데이터
    """
    try:
        policy = await PolicyService.update_policy(
            db=db,
            policy_id=policy_id,
            policy_data=policy_data,
            user_id=current_user.id
        )
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="정책을 찾을 수 없습니다."
            )
        
        return policy
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    정책 삭제 (관리자 전용)
    
    특정 정책을 삭제합니다.
    
    - **policy_id**: 삭제할 정책 ID
    """
    result = await PolicyService.delete_policy(
        db=db,
        policy_id=policy_id,
        user_id=current_user.id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="정책을 찾을 수 없습니다."
        )

@router.get("/effective/user-permission", response_model=UserPermissionPolicySettings)
async def get_effective_user_permission_settings(
    role: str = Query("user", description="사용자 역할"),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    유효한 사용자 권한 설정 조회 (관리자 전용)
    
    특정 역할에 대한 유효한 사용자 권한 설정을 조회합니다.
    
    - **role**: 사용자 역할
    """
    return await PolicyService.get_effective_user_permission_settings(db=db, role=role)

@router.get("/effective/query-limit", response_model=QueryLimitPolicySettings)
async def get_effective_query_limit_settings(
    role: str = Query("user", description="사용자 역할"),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    유효한 쿼리 제한 설정 조회 (관리자 전용)
    
    특정 역할에 대한 유효한 쿼리 제한 설정을 조회합니다.
    
    - **role**: 사용자 역할
    """
    return await PolicyService.get_effective_query_limit_settings(db=db, role=role)

@router.get("/effective/security", response_model=SecurityPolicySettings)
async def get_effective_security_settings(
    role: str = Query("user", description="사용자 역할"),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    유효한 보안 설정 조회 (관리자 전용)
    
    특정 역할에 대한 유효한 보안 설정을 조회합니다.
    
    - **role**: 사용자 역할
    """
    return await PolicyService.get_effective_security_settings(db=db, role=role)
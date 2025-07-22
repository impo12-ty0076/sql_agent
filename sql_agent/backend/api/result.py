from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/result",
    tags=["result"],
    responses={401: {"description": "Unauthorized"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class ReportRequest(BaseModel):
    result_id: str
    visualization_types: List[str] = ["bar", "line", "pie"]
    include_insights: bool = True

@router.get("/{result_id}")
async def get_query_result(
    result_id: str, page: int = 1, page_size: int = 50, token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 실행 결과 조회
    """
    # 실제 구현에서는 결과 데이터 조회 및 페이지네이션
    return {
        "result_id": result_id,
        "columns": [
            {"name": "id", "type": "int"},
            {"name": "username", "type": "varchar"},
            {"name": "email", "type": "varchar"},
        ],
        "rows": [
            [1, "user1", "user1@example.com"],
            [2, "user2", "user2@example.com"],
        ],
        "row_count": 2,
        "truncated": False,
        "total_row_count": 2,
        "page": page,
        "page_size": page_size,
        "total_pages": 1,
    }

@router.get("/{result_id}/summary")
async def get_result_summary(result_id: str, token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    쿼리 결과 요약 조회
    """
    # 실제 구현에서는 LLM을 사용하여 결과 요약 생성
    return {
        "result_id": result_id,
        "summary": "총 2명의 사용자가 조회되었습니다. 사용자 ID, 사용자명, 이메일 정보가 포함되어 있습니다.",
    }

@router.post("/report")
async def generate_report(
    request: ReportRequest, background_tasks: BackgroundTasks, token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 결과에 대한 리포트 생성 요청
    """
    # 실제 구현에서는 파이썬 인터프리터를 사용하여 리포트 생성
    return {
        "result_id": request.result_id,
        "report_id": "rep123",
        "status": "generating",
    }

@router.get("/report/{report_id}")
async def get_report(report_id: str, token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    생성된 리포트 조회
    """
    # 실제 구현에서는 생성된 리포트 데이터 조회
    return {
        "report_id": report_id,
        "result_id": "r123",
        "status": "completed",
        "visualizations": [
            {
                "id": "vis1",
                "type": "bar",
                "title": "사용자 분포",
                "image_data": "base64_encoded_image_data",
            }
        ],
        "insights": [
            "사용자 데이터는 고르게 분포되어 있습니다.",
        ],
    }
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Query as QueryParam
from typing import Dict, Any, List, Optional
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from ..services.query_service import QueryService
from ..services.query_execution_service_updated import QueryExecutionService
from ..services.query_history_service import QueryHistoryService
from ..llm.nl_to_sql_service import NLToSQLService
from ..llm.factory import get_llm_service
from ..rag.rag_service import RagService
from ..services.database import DatabaseService
from ..models.query import QueryStatus, QueryCreate, QueryUpdate
from ..db.crud.query import create_query, update_query, get_query_by_id
from ..core.auth import get_current_user, get_current_user_id

router = APIRouter(
    prefix="/api/query",
    tags=["query"],
    responses={401: {"description": "Unauthorized"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class NaturalLanguageQuery(BaseModel):
    query: str
    db_id: str
    use_rag: bool = False
    conversation_id: Optional[str] = None
    save_to_history: bool = True

class SQLQuery(BaseModel):
    sql: str
    db_id: str
    query_id: Optional[str] = None
    save_to_history: bool = True

class SQLModification(BaseModel):
    sql: str
    query_id: str

class RagQuery(BaseModel):
    query: str
    db_id: str
    conversation_id: Optional[str] = None
    top_k: int = Field(5, description="Number of documents to retrieve")
    include_citations: bool = Field(True, description="Whether to include source citations")
    save_to_history: bool = True

# Service instances
query_service = QueryService()
query_execution_service = QueryExecutionService()
query_history_service = QueryHistoryService()
llm_service = get_llm_service()
nl_to_sql_service = NLToSQLService(llm_service)
rag_service = RagService(llm_service)
db_service = DatabaseService()

@router.post("/natural")
async def process_natural_language_query(
    query: NaturalLanguageQuery, 
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    자연어 질의를 SQL로 변환
    
    이 엔드포인트는 자연어 질의를 받아 해당 데이터베이스에 맞는 SQL 쿼리로 변환합니다.
    use_rag 파라미터가 True인 경우, RAG 시스템을 사용하여 응답을 생성합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # RAG 시스템 사용 여부에 따라 처리
        if query.use_rag:
            # RAG 시스템을 통한 응답 생성
            rag_query = RagQuery(
                query=query.query,
                db_id=query.db_id,
                conversation_id=query.conversation_id,
                save_to_history=query.save_to_history
            )
            return await process_rag_query(rag_query, token)
        
        # 데이터베이스 스키마 정보 가져오기
        db_schema = await db_service.get_database_schema(query.db_id)
        if not db_schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database with ID {query.db_id} not found or schema not available"
            )
        
        # 데이터베이스 유형 가져오기
        db_info = await db_service.get_database_by_id(query.db_id)
        db_type = db_info.get("type", "mssql")  # 기본값은 mssql
        
        # 자연어를 SQL로 변환
        result = await nl_to_sql_service.convert_nl_to_sql(
            user_id=user_id,
            natural_language=query.query,
            schema=db_schema,
            db_type=db_type,
            conversation_id=query.conversation_id
        )
        
        # 쿼리 ID 생성 및 저장
        query_id = str(uuid.uuid4())
        
        # 쿼리 생성 및 저장
        query_data = QueryCreate(
            user_id=user_id,
            db_id=query.db_id,
            natural_language=query.query,
            generated_sql=result["sql"]
        )
        
        created_query = await create_query(query_data)
        
        # 응답 생성
        response = {
            "query_id": created_query.id,
            "natural_language": query.query,
            "generated_sql": result["sql"],
            "db_id": query.db_id,
            "confidence": result.get("confidence", 0.9),
            "explanation": result.get("explanation", ""),
            "conversation_id": result.get("conversation_id", query.conversation_id),
            "status": QueryStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 이력에 저장 (옵션)
        if query.save_to_history:
            try:
                history_result = await query_history_service.save_query_to_history(
                    user_id=user_id,
                    query_id=created_query.id
                )
                response["history_id"] = history_result["id"]
            except Exception as e:
                # 이력 저장 실패는 전체 요청 실패로 처리하지 않음
                pass
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing natural language query: {str(e)}"
        )

@router.post("/rag")
async def process_rag_query(
    query: RagQuery,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    RAG 시스템을 사용하여 자연어 질의에 대한 응답 생성
    
    이 엔드포인트는 자연어 질의를 받아 RAG(Retrieval-Augmented Generation) 시스템을 통해
    데이터베이스 스키마 및 관련 문서를 검색하고 응답을 생성합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # RAG 응답 생성
        rag_response = await rag_service.generate_response_async(
            db_id=query.db_id,
            query=query.query,
            top_k=query.top_k,
            include_citations=query.include_citations
        )
        
        # 쿼리 ID 생성
        query_id = str(uuid.uuid4())
        
        # 응답 생성
        response = {
            "query_id": query_id,
            "natural_language": query.query,
            "db_id": query.db_id,
            "response": rag_response.response,
            "sources": [
                {
                    "document_id": source.document.id,
                    "document_type": source.document.doc_type,
                    "score": source.score,
                    "metadata": source.document.metadata
                }
                for source in rag_response.sources
            ],
            "conversation_id": query.conversation_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 이력에 저장 (옵션)
        if query.save_to_history:
            try:
                # RAG 쿼리의 경우 별도의 쿼리 레코드가 없으므로 임시 쿼리 생성
                query_data = QueryCreate(
                    user_id=user_id,
                    db_id=query.db_id,
                    natural_language=query.query,
                    generated_sql="RAG QUERY"  # RAG 쿼리임을 표시
                )
                
                created_query = await create_query(query_data)
                
                history_result = await query_history_service.save_query_to_history(
                    user_id=user_id,
                    query_id=created_query.id,
                    tags=["rag"]  # RAG 쿼리임을 태그로 표시
                )
                response["history_id"] = history_result["id"]
            except Exception as e:
                # 이력 저장 실패는 전체 요청 실패로 처리하지 않음
                pass
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}"
        )

@router.post("/modify-sql")
async def modify_sql(
    modification: SQLModification,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    생성된 SQL 쿼리 수정
    
    이 엔드포인트는 이전에 생성된 SQL 쿼리를 수정할 수 있게 합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 쿼리 존재 여부 확인
        query = await get_query_by_id(modification.query_id)
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {modification.query_id} not found"
            )
        
        # 사용자 권한 확인
        if query.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this query"
            )
        
        # 쿼리 업데이트
        query_update = QueryUpdate(
            generated_sql=modification.sql
        )
        
        updated_query = await update_query(modification.query_id, query_update)
        
        # 응답 생성
        response = {
            "query_id": updated_query.id,
            "natural_language": updated_query.natural_language,
            "generated_sql": updated_query.generated_sql,
            "db_id": updated_query.db_id,
            "status": updated_query.status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error modifying SQL: {str(e)}"
        )

@router.post("/execute")
async def execute_query(
    query: SQLQuery, 
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    SQL 쿼리 실행
    
    이 엔드포인트는 SQL 쿼리를 받아 지정된 데이터베이스에서 실행합니다.
    쿼리 실행은 백그라운드 작업으로 처리되며, 상태는 /status/{query_id} 엔드포인트를 통해 확인할 수 있습니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 쿼리 실행
        result = await query_execution_service.execute_query(
            user_id=user_id,
            db_id=query.db_id,
            sql=query.sql,
            query_id=query.query_id,
            timeout=300,  # 5 minutes timeout
            max_rows=10000,  # Maximum 10,000 rows
            auto_save_to_history=query.save_to_history  # 자동 이력 저장 여부
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing query: {str(e)}"
        )

@router.get("/status/{query_id}")
async def get_query_status(
    query_id: str, 
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 실행 상태 조회
    
    이 엔드포인트는 지정된 쿼리 ID의 실행 상태를 조회합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 쿼리 존재 여부 확인
        query = await get_query_by_id(query_id)
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )
        
        # 사용자 권한 확인
        if query.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this query"
            )
        
        # 쿼리 상태 조회
        status_result = await query_execution_service.get_query_status(query_id)
        
        return status_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting query status: {str(e)}"
        )

@router.post("/cancel/{query_id}")
async def cancel_query(
    query_id: str, 
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    실행 중인 쿼리 취소
    
    이 엔드포인트는 실행 중인 쿼리를 취소합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 쿼리 존재 여부 확인
        query = await get_query_by_id(query_id)
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )
        
        # 사용자 권한 확인
        if query.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to cancel this query"
            )
        
        # 쿼리 취소
        cancel_result = await query_execution_service.cancel_query(query_id)
        
        return cancel_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling query: {str(e)}"
        )

@router.get("/running")
async def get_running_queries(
    token: str = Depends(oauth2_scheme)
) -> List[Dict[str, Any]]:
    """
    실행 중인 쿼리 목록 조회
    
    이 엔드포인트는 현재 사용자의 실행 중인 쿼리 목록을 조회합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 실행 중인 쿼리 목록 조회
        running_queries = await query_execution_service.get_running_queries(user_id)
        
        return running_queries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting running queries: {str(e)}"
        )
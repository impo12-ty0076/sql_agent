# RAG 기반 응답 생성 구현 (Task 6.3)

## 개요

이 문서는 SQL DB LLM Agent 시스템의 RAG(Retrieval-Augmented Generation) 기반 응답 생성 기능의 구현 내용을 설명합니다.

## 구현된 기능

### 1. 향상된 컨텍스트 구성 (Enhanced Context Construction)

#### 주요 기능
- **검색 결과 기반 컨텍스트 구성**: 검색된 문서들을 관련도 순으로 정렬하여 컨텍스트 구성
- **컨텍스트 윈도우 관리**: 설정 가능한 컨텍스트 크기 제한으로 토큰 사용량 최적화
- **문서 타입별 포맷팅**: 테이블, 컬럼, 외래키 등 문서 타입에 따른 차별화된 포맷팅
- **메타데이터 통합**: 테이블명, 스키마명, 컬럼명 등 메타데이터 정보 포함

#### 구현 메서드
```python
def _build_enhanced_context(
    self, query: str, search_results: List[SearchResult], 
    context_window_size: int, include_citations: bool
) -> str
```

### 2. LLM 기반 응답 생성 (LLM-based Response Generation)

#### 주요 기능
- **향상된 프롬프트 엔지니어링**: 구체적인 답변 지침과 컨텍스트 활용 방법 제시
- **비동기 응답 생성**: 성능 향상을 위한 async/await 패턴 지원
- **오류 처리**: LLM 서비스 장애 시 적절한 오류 메시지 반환
- **한국어 최적화**: 한국어 사용자를 위한 자연스러운 응답 생성

#### 구현 메서드
```python
async def _generate_llm_response_async(
    self, query: str, context: str, include_citations: bool
) -> str
```

### 3. 소스 인용 및 참조 기능 (Source Citation and Reference)

#### 주요 기능
- **자동 인용 번호 생성**: 컨텍스트 내 문서에 [1], [2] 형태의 인용 번호 자동 부여
- **참고 자료 섹션**: 응답 하단에 사용된 소스 정보 상세 표시
- **관련도 점수 표시**: 각 소스의 검색 관련도 점수 포함
- **메타데이터 기반 소스 설명**: 테이블명, 스키마명 등을 활용한 소스 설명

#### 구현 메서드
```python
def _add_source_citations(
    self, response: str, search_results: List[SearchResult]
) -> str
```

### 4. 검색 폴백 전략 (Search Fallback Strategy)

#### 주요 기능
- **다중 검색 방식 지원**: hybrid → keyword → fuzzy 순서로 폴백
- **검색 결과 없음 처리**: 적절한 안내 메시지 제공
- **검색 타입별 최적화**: 각 검색 방식의 특성에 맞는 결과 처리

#### 구현 메서드
```python
def _search_with_fallback(
    self, search_query: SearchQuery, search_type: str
) -> List[SearchResult]
```

## 향상된 API

### 기본 응답 생성 (동기)
```python
def generate_response(
    self, db_id: str, query: str, top_k: int = 5, search_type: str = "hybrid",
    include_citations: bool = True, context_window_size: int = 2000
) -> RagResponse
```

### 비동기 응답 생성
```python
async def generate_response_async(
    self, db_id: str, query: str, top_k: int = 5, search_type: str = "hybrid",
    include_citations: bool = True, context_window_size: int = 2000
) -> RagResponse
```

## 사용 예시

### 기본 사용법
```python
# RAG 서비스 초기화
rag_service = RagService(llm_service=llm_service)

# 응답 생성
response = rag_service.generate_response(
    db_id="ecommerce_db",
    query="사용자 테이블의 구조에 대해 알려주세요",
    include_citations=True
)

print(response.response)
print(f"참조된 소스 수: {len(response.sources)}")
```

### 비동기 사용법
```python
# 비동기 응답 생성
response = await rag_service.generate_response_async(
    db_id="ecommerce_db",
    query="주문과 사용자 간의 관계를 설명해주세요",
    top_k=10,
    context_window_size=3000
)
```

## 응답 예시

### 입력
```
Query: "사용자 테이블의 구조에 대해 알려주세요"
```

### 출력
```
사용자 테이블(Users)에 대한 정보를 제공해드리겠습니다.

**테이블 구조:**
- 테이블명: Users
- 스키마: dbo
- 주요 컬럼:
  - id (int): 기본키, 사용자 고유 식별자 [1]
  - name (varchar): 사용자 이름 [1]
  - email (varchar): 사용자 이메일 주소 [1]

**관계:**
- Orders 테이블과 외래키 관계 (Orders.user_id → Users.id) [2]

이 테이블은 시스템의 사용자 정보를 저장하는 핵심 테이블입니다.

--- 참고 자료 ---
[1] 테이블 - Users (dbo) (관련도: 0.95)
[2] 외래키 - Orders → Users (관련도: 0.78)
```

## 성능 최적화

### 컨텍스트 윈도우 관리
- 기본 2000자 제한으로 토큰 사용량 최적화
- 관련도 높은 문서 우선 포함
- 동적 크기 조절 지원

### 비동기 처리
- LLM API 호출의 비동기 처리로 응답 시간 단축
- 동기/비동기 버전 모두 지원하여 호환성 확보

### 메모리 효율성
- 필요한 문서만 컨텍스트에 포함
- 긴 문서 내용 자동 truncation

## 오류 처리

### LLM 서비스 오류
- API 호출 실패 시 적절한 오류 메시지 반환
- 서비스 복구 가능한 오류와 치명적 오류 구분

### 검색 결과 없음
- 사용자 친화적인 안내 메시지 제공
- 대안 검색 방법 제안

### 컨텍스트 오버플로우
- 컨텍스트 크기 초과 시 자동 truncation
- 중요도 기반 문서 선별

## 테스트

### 단위 테스트
- 각 메서드별 독립적인 테스트
- Mock 객체를 활용한 의존성 분리
- 경계값 및 예외 상황 테스트

### 통합 테스트
- 전체 RAG 파이프라인 테스트
- 실제 데이터를 활용한 시나리오 테스트
- 성능 및 메모리 사용량 검증

## 향후 개선 사항

### 기능 확장
- 다국어 지원 확대
- 커스텀 프롬프트 템플릿 지원
- 응답 품질 평가 메트릭 추가

### 성능 최적화
- 캐싱 메커니즘 도입
- 배치 처리 지원
- 스트리밍 응답 지원

### 사용성 개선
- 응답 포맷 커스터마이징
- 인터랙티브 소스 탐색
- 응답 품질 피드백 수집

## 결론

RAG 기반 응답 생성 기능의 구현으로 다음과 같은 개선사항을 달성했습니다:

1. **정확성 향상**: 검색된 문서 기반의 정확한 정보 제공
2. **투명성 확보**: 소스 인용을 통한 정보 출처 명시
3. **사용성 개선**: 한국어 최적화 및 구조화된 응답 형식
4. **확장성 확보**: 비동기 처리 및 모듈화된 구조
5. **안정성 강화**: 포괄적인 오류 처리 및 폴백 전략

이러한 구현을 통해 사용자는 데이터베이스 스키마에 대한 질문에 대해 신뢰할 수 있고 이해하기 쉬운 답변을 받을 수 있게 되었습니다.
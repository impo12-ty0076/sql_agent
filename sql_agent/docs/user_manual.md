# SQL DB LLM Agent 사용자 매뉴얼

## 소개

SQL DB LLM Agent는 비전문가도 자연어로 MS-SQL 및 SAP HANA DB에 질의하고, 쿼리 결과를 표, 자연어 요약, 또는 AI 기반 파이썬 리포트(토글 방식)로 얻을 수 있는 웹 기반 LLM 에이전트 서비스입니다.

이 매뉴얼은 SQL DB LLM Agent의 사용 방법을 단계별로 안내합니다.

## 목차

1. [시작하기](#1-시작하기)
2. [로그인 및 계정 관리](#2-로그인-및-계정-관리)
3. [데이터베이스 연결](#3-데이터베이스-연결)
4. [자연어 질의하기](#4-자연어-질의하기)
5. [결과 보기 및 분석](#5-결과-보기-및-분석)
6. [이력 관리 및 공유](#6-이력-관리-및-공유)
7. [자주 묻는 질문(FAQ)](#7-자주-묻는-질문faq)
8. [문제 해결 가이드](#8-문제-해결-가이드)

## 1. 시작하기

### 시스템 요구사항

SQL DB LLM Agent는 웹 기반 애플리케이션으로, 다음 브라우저에서 최적의 성능을 제공합니다:

- Google Chrome (최신 버전)
- Microsoft Edge (최신 버전)
- Mozilla Firefox (최신 버전)
- Safari (최신 버전)

Internet Explorer는 지원되지 않습니다.

### 접속 방법

1. 웹 브라우저를 열고 제공된 URL로 이동합니다.
2. 로그인 페이지가 표시됩니다.

## 2. 로그인 및 계정 관리

### 로그인

1. 사용자 이름과 비밀번호를 입력합니다.
2. "로그인" 버튼을 클릭합니다.
3. 인증에 성공하면 메인 대시보드로 이동합니다.

### 비밀번호 재설정

1. 로그인 페이지에서 "비밀번호 찾기" 링크를 클릭합니다.
2. 등록된 이메일 주소를 입력합니다.
3. 이메일로 전송된 지침에 따라 비밀번호를 재설정합니다.

### 프로필 설정

1. 오른쪽 상단의 사용자 아이콘을 클릭합니다.
2. "프로필 설정"을 선택합니다.
3. 다음 설정을 변경할 수 있습니다:
   - 이메일 주소
   - 비밀번호
   - UI 테마 (라이트/다크)
   - 결과 페이지당 행 수
   - 기본 데이터베이스

### 로그아웃

1. 오른쪽 상단의 사용자 아이콘을 클릭합니다.
2. "로그아웃"을 선택합니다.

## 3. 데이터베이스 연결

### 데이터베이스 선택

1. 메인 대시보드의 왼쪽 사이드바에서 "데이터베이스" 섹션을 찾습니다.
2. 접근 권한이 있는 데이터베이스 목록이 표시됩니다.
3. 연결하려는 데이터베이스를 클릭합니다.
4. 연결이 성공하면 데이터베이스 이름 옆에 녹색 연결 상태 아이콘이 표시됩니다.

### 데이터베이스 스키마 탐색

1. 데이터베이스에 연결한 후, "스키마 탐색" 탭을 클릭합니다.
2. 데이터베이스의 스키마, 테이블, 컬럼 정보가 트리 구조로 표시됩니다.
3. 테이블을 클릭하면 해당 테이블의 컬럼 정보가 표시됩니다.
4. 컬럼을 클릭하면 데이터 유형, NULL 허용 여부 등의 상세 정보가 표시됩니다.

### 데이터베이스 전환

1. 다른 데이터베이스로 전환하려면 왼쪽 사이드바에서 원하는 데이터베이스를 클릭합니다.
2. 현재 연결은 자동으로 종료되고 새 데이터베이스에 연결됩니다.

## 4. 자연어 질의하기

### 자연어 질의 입력

1. 메인 대시보드의 중앙에 있는 질의 입력 필드에 자연어로 질문을 입력합니다.
   - 예: "지난 달 판매량이 가장 높은 상위 5개 제품은?"
   - 예: "부서별 평균 급여를 내림차순으로 보여줘"
2. 입력 필드 아래의 "질의하기" 버튼을 클릭합니다.

### SQL 변환 결과 확인

1. 시스템이 자연어 질의를 SQL로 변환합니다.
2. 변환된 SQL이 화면에 표시됩니다.
3. SQL을 검토하고 필요한 경우 직접 수정할 수 있습니다.
4. "실행" 버튼을 클릭하여 SQL을 실행합니다.

### RAG 시스템 사용

1. 자연어 질의 입력 필드 아래에 "RAG 모드 사용" 체크박스가 있습니다.
2. 데이터베이스 구조나 메타데이터에 대한 질문을 할 때 이 옵션을 선택합니다.
   - 예: "판매 데이터의 구조와 주요 테이블을 설명해줘"
   - 예: "고객 정보는 어떤 테이블에 저장되어 있나요?"
3. RAG 모드에서는 시스템이 SQL을 생성하는 대신 관련 정보를 검색하여 응답합니다.

### 대화 컨텍스트 유지

1. 이전 질의에 이어서 후속 질문을 할 수 있습니다.
   - 예: "지난 달 판매량이 가장 높은 상위 5개 제품은?" (첫 번째 질의)
   - 예: "그 중에서 재고가 가장 적은 제품은?" (후속 질의)
2. 시스템은 이전 대화 컨텍스트를 유지하여 적절한 SQL을 생성합니다.
3. 새로운 주제로 질의하려면 "새 대화" 버튼을 클릭합니다.

## 5. 결과 보기 및 분석

### 테이블 형식 결과

1. SQL 쿼리 실행 후, 결과가 테이블 형식으로 표시됩니다.
2. 결과 테이블에서 다음 기능을 사용할 수 있습니다:
   - 컬럼 정렬: 컬럼 헤더를 클릭하여 오름차순/내림차순 정렬
   - 필터링: 컬럼 헤더의 필터 아이콘을 클릭하여 값 필터링
   - 페이지 이동: 테이블 하단의 페이지네이션 컨트롤 사용
3. 대용량 결과의 경우, 시스템은 자동으로 페이지네이션을 적용합니다.

### 자연어 요약

1. 결과 테이블 위에 있는 "요약 생성" 버튼을 클릭합니다.
2. 시스템이 쿼리 결과를 분석하고 자연어로 요약을 생성합니다.
3. 요약에는 주요 인사이트, 패턴, 이상치 등이 포함됩니다.
4. 요약 상세도를 "낮음", "중간", "높음" 중에서 선택할 수 있습니다.

### 리포트 생성

1. 결과 테이블 위에 있는 "리포트 생성" 토글을 활성화합니다.
2. 리포트 옵션을 선택합니다:
   - 리포트 유형: 기본, 표준, 종합
   - 시각화 유형: 막대 그래프, 파이 차트, 선 그래프 등
   - 파이썬 코드 포함 여부
3. "리포트 생성" 버튼을 클릭합니다.
4. 시스템이 파이썬 인터프리터를 사용하여 데이터 분석 및 시각화를 수행합니다.
5. 생성된 리포트에는 다음 요소가 포함됩니다:
   - 데이터 요약 및 인사이트
   - 데이터 시각화 (차트, 그래프)
   - 통계 분석 결과
   - (선택 시) 사용된 파이썬 코드
6. "다운로드" 버튼을 클릭하여 리포트를 PDF, HTML 또는 JSON 형식으로 다운로드할 수 있습니다.

## 6. 이력 관리 및 공유

### 쿼리 이력 조회

1. 왼쪽 사이드바에서 "이력" 메뉴를 클릭합니다.
2. 실행한 모든 쿼리의 이력이 날짜순으로 표시됩니다.
3. 다음 필터를 사용하여 이력을 필터링할 수 있습니다:
   - 날짜 범위
   - 데이터베이스
   - 쿼리 유형
   - 태그
   - 즐겨찾기 여부
4. 검색 필드를 사용하여 특정 키워드가 포함된 쿼리를 검색할 수 있습니다.

### 즐겨찾기 및 태그 관리

1. 쿼리 이력 목록에서 각 항목 옆에 있는 별표 아이콘을 클릭하여 즐겨찾기로 설정/해제할 수 있습니다.
2. 쿼리 이력 항목을 클릭하여 상세 보기로 이동합니다.
3. 상세 보기에서 "태그 관리" 버튼을 클릭합니다.
4. 기존 태그를 선택하거나 새 태그를 입력하여 쿼리에 태그를 추가할 수 있습니다.
5. "저장" 버튼을 클릭하여 변경사항을 저장합니다.

### 쿼리 재실행

1. 쿼리 이력 목록에서 재실행하려는 쿼리를 찾습니다.
2. "재실행" 버튼을 클릭합니다.
3. 원본 SQL을 그대로 사용하거나 수정할 수 있습니다.
4. "실행" 버튼을 클릭하여 쿼리를 재실행합니다.

### 쿼리 및 결과 공유

1. 쿼리 이력 상세 보기에서 "공유" 버튼을 클릭합니다.
2. 공유 옵션을 설정합니다:
   - 만료 기간 (일)
   - 접근 허용 사용자 (이메일 주소)
   - 결과 포함 여부
   - 리포트 포함 여부
3. "공유 링크 생성" 버튼을 클릭합니다.
4. 생성된 공유 링크를 복사하여 다른 사용자와 공유할 수 있습니다.
5. 공유 링크에 접근하면 쿼리와 결과(설정에 따라)를 볼 수 있습니다.

## 7. 자주 묻는 질문(FAQ)

### 일반 질문

**Q: SQL DB LLM Agent는 어떤 데이터베이스를 지원하나요?**

A: 현재 MS-SQL Server 2012 이상과 SAP HANA 1.0 이상을 지원합니다.

**Q: 자연어 질의는 어떤 언어로 할 수 있나요?**

A: 현재 한국어와 영어를 지원합니다.

**Q: 데이터를 수정하는 쿼리(INSERT, UPDATE, DELETE 등)를 실행할 수 있나요?**

A: 아니요, 보안상의 이유로 읽기 전용 쿼리(SELECT)만 허용됩니다.

**Q: 세션이 자동으로 로그아웃되는 시간은 얼마인가요?**

A: 기본적으로 60분 동안 활동이 없으면 자동으로 로그아웃됩니다. 이 설정은 관리자가 변경할 수 있습니다.

### 자연어 질의 관련

**Q: 어떤 형식으로 질문해야 가장 정확한 SQL이 생성되나요?**

A: 명확하고 구체적인 질문이 가장 좋습니다. 테이블이나 필드 이름을 알고 있다면 포함시키는 것이 도움이 됩니다.

**Q: 복잡한 조인이나 서브쿼리가 필요한 질문도 할 수 있나요?**

A: 네, 시스템은 복잡한 조인, 서브쿼리, 집계 함수 등을 포함한 SQL을 생성할 수 있습니다.

**Q: 시스템이 생성한 SQL이 정확하지 않을 경우 어떻게 해야 하나요?**

A: SQL 미리보기 화면에서 직접 SQL을 수정한 후 실행할 수 있습니다.

### 결과 및 리포트 관련

**Q: 리포트 생성에 얼마나 시간이 걸리나요?**

A: 데이터 크기와 복잡성에 따라 다르지만, 일반적으로 몇 초에서 1분 이내에 완료됩니다.

**Q: 리포트에 어떤 종류의 시각화가 포함되나요?**

A: 막대 그래프, 파이 차트, 선 그래프, 산점도, 히트맵 등 다양한 시각화가 데이터 특성에 따라 자동으로 선택됩니다.

**Q: 대용량 결과를 다운로드할 수 있나요?**

A: 네, 결과를 CSV, Excel, JSON 형식으로 다운로드할 수 있습니다.

## 8. 문제 해결 가이드

### 로그인 문제

**문제: 로그인이 되지 않습니다.**

해결 방법:

1. 사용자 이름과 비밀번호를 정확히 입력했는지 확인하세요.
2. Caps Lock이 켜져 있는지 확인하세요.
3. 비밀번호를 잊은 경우 "비밀번호 찾기" 기능을 사용하세요.
4. 계정이 잠겨 있을 수 있습니다. 관리자에게 문의하세요.

### 데이터베이스 연결 문제

**문제: 데이터베이스에 연결할 수 없습니다.**

해결 방법:

1. 네트워크 연결 상태를 확인하세요.
2. 데이터베이스 서버가 실행 중인지 확인하세요.
3. 데이터베이스 접근 권한이 있는지 확인하세요.
4. 방화벽 설정을 확인하세요.
5. 오류 메시지를 확인하고 관리자에게 문의하세요.

### 쿼리 실행 문제

**문제: 쿼리 실행 시 오류가 발생합니다.**

해결 방법:

1. 오류 메시지를 확인하세요.
2. SQL 구문에 오류가 있는지 확인하세요.
3. 참조하는 테이블이나 필드가 존재하는지 확인하세요.
4. 쿼리가 너무 복잡하거나 대용량 데이터를 처리하는 경우, 쿼리를 단순화하거나 필터를 추가하세요.
5. 지속적인 문제가 발생하면 관리자에게 문의하세요.

### 리포트 생성 문제

**문제: 리포트 생성이 실패하거나 시간이 너무 오래 걸립니다.**

해결 방법:

1. 결과 데이터 크기가 너무 큰 경우, 쿼리를 수정하여 결과 크기를 줄이세요.
2. 리포트 유형을 "기본" 또는 "표준"으로 변경해 보세요.
3. 시각화 유형을 줄이거나 변경해 보세요.
4. 브라우저를 새로고침한 후 다시 시도하세요.
5. 지속적인 문제가 발생하면 관리자에게 문의하세요.

### 성능 문제

**문제: 시스템 응답이 느립니다.**

해결 방법:

1. 브라우저 캐시를 지우고 다시 시도하세요.
2. 다른 브라우저를 사용해 보세요.
3. 인터넷 연결 상태를 확인하세요.
4. 동시에 여러 복잡한 쿼리를 실행하는 경우, 하나씩 실행해 보세요.
5. 지속적인 성능 문제가 발생하면 관리자에게 문의하세요.

## 지원 및 문의

추가 지원이 필요하거나 문의사항이 있는 경우, 다음 방법으로 연락하세요:

- 이메일: support@example.com
- 전화: 02-123-4567
- 내부 지원 티켓 시스템: 애플리케이션 내 "지원" 메뉴 사용

# EnhancedResultTable Component

## 개요

`EnhancedResultTable` 컴포넌트는 SQL 쿼리 결과를 표시하기 위한 고급 테이블 컴포넌트입니다. 이 컴포넌트는 정렬, 필터링, 페이지네이션 및 대용량 데이터 처리 기능을 제공합니다.

## 주요 기능

- **테이블 형식 결과 표시**: 컬럼 헤더와 데이터 행을 포함한 테이블 형식으로 결과 표시
- **정렬 기능**: 컬럼 헤더 클릭으로 오름차순/내림차순 정렬
- **필터링 기능**:
  - 전역 검색: 모든 컬럼에 대한 검색
  - 컬럼별 필터링: 특정 컬럼에 대한 다양한 연산자(포함, 일치, 시작, 끝, 초과, 미만)를 사용한 필터링
- **페이지네이션**: 대용량 데이터를 페이지 단위로 표시
- **컬럼 표시 설정**: 특정 컬럼을 표시하거나 숨기는 기능
- **데이터 내보내기**:
  - 클립보드에 복사
  - CSV 파일로 다운로드
- **대용량 데이터 처리**:
  - 효율적인 렌더링을 위한 가상화
  - 대용량 결과에 대한 페이지네이션 및 샘플 표시
- **상태 표시**:
  - 로딩 상태
  - 오류 상태
  - 결과 없음 상태
- **접근성**: ARIA 레이블 및 키보드 탐색 지원

## Props

| Prop                 | 타입                                   | 설명                                 | 기본값 |
| -------------------- | -------------------------------------- | ------------------------------------ | ------ |
| columns              | Column[]                               | 컬럼 정보 배열 (name, type 포함)     | 필수   |
| rows                 | any[][]                                | 데이터 행 배열                       | 필수   |
| rowCount             | number                                 | 총 행 수                             | 필수   |
| loading              | boolean                                | 로딩 상태 여부                       | false  |
| truncated            | boolean                                | 결과가 잘렸는지 여부                 | false  |
| totalRowCount        | number                                 | 전체 행 수 (truncated가 true인 경우) | -      |
| executionTime        | number                                 | 쿼리 실행 시간 (ms)                  | -      |
| onRefresh            | () => void                             | 새로고침 버튼 클릭 시 호출할 함수    | -      |
| error                | string                                 | 오류 메시지                          | -      |
| maxHeight            | number \| string                       | 테이블 최대 높이                     | 600    |
| stickyHeader         | boolean                                | 헤더 고정 여부                       | true   |
| showRowNumbers       | boolean                                | 행 번호 표시 여부                    | false  |
| onRowClick           | (row: any[], rowIndex: number) => void | 행 클릭 시 호출할 함수               | -      |
| highlightSearchTerms | boolean                                | 검색어 하이라이트 여부               | true   |

## 사용 예시

```tsx
import EnhancedResultTable from '../components/EnhancedResultTable';

// 컴포넌트 내부
const columns = [
  { name: 'ID', type: 'number' },
  { name: '이름', type: 'string' },
  { name: '이메일', type: 'string' },
  { name: '나이', type: 'number' },
];

const rows = [
  [1, '홍길동', 'hong@example.com', 30],
  [2, '김철수', 'kim@example.com', 25],
  [3, '이영희', 'lee@example.com', 28],
];

// 렌더링
return (
  <EnhancedResultTable
    columns={columns}
    rows={rows}
    rowCount={rows.length}
    loading={isLoading}
    error={error}
    onRefresh={handleRefresh}
    showRowNumbers={true}
    onRowClick={handleRowClick}
  />
);
```

## 접근성 고려사항

- 테이블은 적절한 ARIA 레이블과 역할을 포함하여 스크린 리더 사용자가 접근할 수 있습니다.
- 키보드 탐색을 지원하여 마우스 없이도 모든 기능을 사용할 수 있습니다.
- 색상 대비가 충분하여 시각 장애가 있는 사용자도 내용을 쉽게 인식할 수 있습니다.

## 성능 최적화

- 대용량 데이터셋을 효율적으로 처리하기 위해 페이지네이션을 사용합니다.
- 필터링 및 정렬 작업은 메모이제이션을 통해 최적화되어 있습니다.
- 가상화를 통해 화면에 보이는 행만 렌더링하여 메모리 사용량을 최소화합니다.

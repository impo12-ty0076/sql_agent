import re
import string
import logging
import unicodedata
from typing import List, Set, Dict, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)

# Common English stop words
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "when", "who", "how", "where", "why", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does", "did",
    "doing", "would", "should", "could", "ought", "i'm", "you're", "he's",
    "she's", "it's", "we're", "they're", "i've", "you've", "we've", "they've",
    "i'd", "you'd", "he'd", "she'd", "we'd", "they'd", "i'll", "you'll",
    "he'll", "she'll", "we'll", "they'll", "isn't", "aren't", "wasn't",
    "weren't", "hasn't", "haven't", "hadn't", "doesn't", "don't", "didn't",
    "won't", "wouldn't", "shan't", "shouldn't", "can't", "cannot", "couldn't",
    "mustn't", "let's", "that's", "who's", "what's", "here's", "there's",
    "when's", "where's", "why's", "how's", "a", "an", "the", "and", "but",
    "if", "or", "because", "as", "until", "while", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now"
}

# SQL 관련 키워드 (검색 및 필터링에 유용)
SQL_KEYWORDS = {
    "select", "from", "where", "join", "inner", "outer", "left", "right", "full",
    "group", "by", "having", "order", "asc", "desc", "limit", "offset", "union",
    "insert", "update", "delete", "create", "alter", "drop", "table", "view",
    "index", "primary", "key", "foreign", "references", "constraint", "unique",
    "not", "null", "default", "check", "cascade", "restrict", "set", "on", "as",
    "distinct", "count", "sum", "avg", "min", "max", "between", "like", "in",
    "exists", "all", "any", "some", "and", "or", "not", "case", "when", "then",
    "else", "end", "with", "top", "percent", "pivot", "unpivot", "over", "partition"
}

def normalize_text(text: str, remove_stopwords: bool = False, keep_sql_keywords: bool = True) -> str:
    """
    텍스트를 정규화하여 소문자로 변환, 구두점 제거, 선택적으로 불용어 제거
    
    Args:
        text: 정규화할 텍스트
        remove_stopwords: 불용어 제거 여부
        keep_sql_keywords: SQL 키워드 유지 여부 (불용어 제거 시에만 적용)
        
    Returns:
        정규화된 텍스트
    """
    if not text:
        return ""
    
    # 유니코드 정규화 (NFC 형식)
    text = unicodedata.normalize('NFC', text)
    
    # 소문자로 변환
    text = text.lower()
    
    # 여러 공백을 하나의 공백으로 대체
    text = re.sub(r'\s+', ' ', text)
    
    # 숫자의 소수점과 약어의 마침표 보호
    text = re.sub(r'(\d)\.(\d)', r'\1<DOT>\2', text)  # 숫자의 소수점 보호
    text = re.sub(r'([a-z])\.([a-z])', r'\1<DOT>\2', text)  # 약어의 마침표 보호
    
    # 구두점 제거
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # 보호된 마침표 복원
    text = text.replace('<DOT>', '.')
    
    # 불용어 제거 (요청된 경우)
    if remove_stopwords:
        words = text.split()
        if keep_sql_keywords:
            # SQL 키워드는 유지하면서 불용어 제거
            words = [word for word in words if word not in STOP_WORDS or word in SQL_KEYWORDS]
        else:
            # 모든 불용어 제거
            words = [word for word in words if word not in STOP_WORDS]
        text = ' '.join(words)
    
    return text.strip()

def tokenize(text: str, remove_stopwords: bool = False, keep_sql_keywords: bool = True) -> List[str]:
    """
    텍스트를 단어로 토큰화
    
    Args:
        text: 토큰화할 텍스트
        remove_stopwords: 불용어 제거 여부
        keep_sql_keywords: SQL 키워드 유지 여부 (불용어 제거 시에만 적용)
        
    Returns:
        토큰 목록
    """
    if not text:
        return []
    
    # 텍스트 정규화
    text = normalize_text(text, remove_stopwords=False)
    
    # 단어로 분할
    words = text.split()
    
    # 불용어 제거 (요청된 경우)
    if remove_stopwords:
        if keep_sql_keywords:
            # SQL 키워드는 유지하면서 불용어 제거
            words = [word for word in words if word not in STOP_WORDS or word in SQL_KEYWORDS]
        else:
            # 모든 불용어 제거
            words = [word for word in words if word not in STOP_WORDS]
    
    return words

def extract_keywords(text: str, max_keywords: int = 10, include_sql_keywords: bool = True) -> List[str]:
    """
    텍스트에서 키워드 추출 (TF-IDF와 유사한 간단한 빈도 기반 접근법 사용)
    
    Args:
        text: 키워드를 추출할 텍스트
        max_keywords: 추출할 최대 키워드 수
        include_sql_keywords: SQL 키워드 포함 여부
        
    Returns:
        키워드 목록
    """
    if not text:
        return []
    
    # 토큰화 및 불용어 제거
    tokens = tokenize(text, remove_stopwords=True, keep_sql_keywords=include_sql_keywords)
    
    # 단어 빈도 계산
    word_counter = Counter()
    for token in tokens:
        if len(token) > 2:  # 최소 3자 이상의 단어만 고려
            word_counter[token] += 1
    
    # SQL 키워드에 가중치 부여 (요청된 경우)
    if include_sql_keywords:
        for word in word_counter:
            if word in SQL_KEYWORDS:
                word_counter[word] *= 1.5  # SQL 키워드에 1.5배 가중치
    
    # 빈도순으로 정렬
    sorted_words = word_counter.most_common(max_keywords)
    
    # 상위 키워드 반환
    return [word for word, _ in sorted_words]

def calculate_text_similarity(text1: str, text2: str, method: str = "jaccard") -> float:
    """
    두 텍스트 간의 유사도 계산
    
    Args:
        text1: 첫 번째 텍스트
        text2: 두 번째 텍스트
        method: 유사도 계산 방법 ("jaccard", "cosine", "overlap")
        
    Returns:
        0과 1 사이의 유사도 점수
    """
    if not text1 or not text2:
        return 0.0
    
    # 텍스트 토큰화
    tokens1 = tokenize(text1.lower())
    tokens2 = tokenize(text2.lower())
    
    if method == "jaccard":
        # Jaccard 유사도 계산
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
        
    elif method == "cosine":
        # 코사인 유사도 계산
        # 단어 빈도 벡터 생성
        all_words = list(set(tokens1 + tokens2))
        vec1 = [tokens1.count(word) for word in all_words]
        vec2 = [tokens2.count(word) for word in all_words]
        
        # 벡터의 내적 계산
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        
        # 벡터의 크기 계산
        magnitude1 = sum(v ** 2 for v in vec1) ** 0.5
        magnitude2 = sum(v ** 2 for v in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
        
    elif method == "overlap":
        # 오버랩 계수 계산
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = len(set1.intersection(set2))
        min_size = min(len(set1), len(set2))
        
        if min_size == 0:
            return 0.0
        
        return intersection / min_size
        
    else:
        # 기본적으로 Jaccard 유사도 사용
        logger.warning(f"Unknown similarity method: {method}. Using Jaccard similarity.")
        return calculate_text_similarity(text1, text2, "jaccard")

def extract_entities(text: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
    """
    텍스트에서 잠재적인 데이터베이스 엔티티(테이블, 컬럼) 추출
    
    Args:
        text: 엔티티를 추출할 텍스트
        schema_info: 스키마 정보 (제공된 경우 정확도 향상)
        
    Returns:
        엔티티 유형을 키로, 엔티티 목록을 값으로 하는 사전
    """
    entities = {
        "tables": [],
        "columns": [],
        "values": [],
        "conditions": [],
        "aggregations": []
    }
    
    # 텍스트 전처리
    text = text.lower()
    
    # 스키마 정보가 제공된 경우 실제 테이블 및 컬럼 이름 검색
    if schema_info:
        tables = schema_info.get("tables", [])
        columns = []
        
        # 테이블 및 컬럼 목록 추출
        for table in tables:
            table_name = table.get("name", "").lower()
            if table_name in text:
                entities["tables"].append(table_name)
            
            for column in table.get("columns", []):
                column_name = column.get("name", "").lower()
                columns.append(column_name)
                if column_name in text:
                    entities["columns"].append(column_name)
    
    # 스키마 정보가 없는 경우 휴리스틱 기반 접근법 사용
    else:
        # 잠재적 테이블 이름 검색 (명사, 주로 복수형)
        table_patterns = [
            r'\b([A-Z][a-z]+s)\b',  # 대문자로 시작하는 복수 명사
            r'\b([a-z]+_[a-z]+)\b',  # 스네이크 케이스 식별자
            r'\b([a-z]+s)\b',  # 소문자 복수 명사
            r'\b(tbl[A-Za-z]+)\b',  # 'tbl' 접두사가 있는 단어
            r'\b([a-z]+Table)\b'  # 'Table' 접미사가 있는 단어
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, text)
            entities["tables"].extend(matches)
        
        # 잠재적 컬럼 이름 검색
        column_patterns = [
            r'\b(id|name|date|time|year|month|day|amount|price|quantity|description|status|type|code|number|address|email|phone)\b',  # 일반적인 컬럼 이름
            r'\b([a-z]+_id)\b',  # 외래 키 컬럼
            r'\b([a-z]+Id)\b',  # camelCase 외래 키 컬럼
            r'\b(first_[a-z]+|last_[a-z]+)\b',  # 접두사가 있는 컬럼
            r'\b([a-z]+_date|[a-z]+_time|[a-z]+_amount)\b'  # 특정 접미사가 있는 컬럼
        ]
        
        for pattern in column_patterns:
            matches = re.findall(pattern, text.lower())
            entities["columns"].extend(matches)
    
    # 잠재적 값 검색
    value_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  # 날짜
        r'\b\d+\.\d+\b',  # 소수
        r'"([^"]+)"',  # 큰따옴표로 묶인 문자열
        r"'([^']+)'",  # 작은따옴표로 묶인 문자열
        r'\b\d+\b'  # 정수
    ]
    
    for pattern in value_patterns:
        matches = re.findall(pattern, text)
        # 빈 문자열이 아닌 경우에만 추가
        entities["values"].extend([m for m in matches if m])
    
    # 조건 검색
    condition_patterns = [
        r'\b(equals|equal to|is|=|==)\b',  # 동등 조건
        r'\b(greater than|>|>=|less than|<|<=)\b',  # 비교 조건
        r'\b(between)\b',  # 범위 조건
        r'\b(like|contains|starts with|ends with)\b',  # 패턴 매칭
        r'\b(in|not in)\b',  # 집합 조건
        r'\b(is null|is not null)\b'  # NULL 조건
    ]
    
    for pattern in condition_patterns:
        matches = re.findall(pattern, text.lower())
        entities["conditions"].extend(matches)
    
    # 집계 함수 검색
    aggregation_patterns = [
        r'\b(count|sum|average|avg|minimum|min|maximum|max|mean|median|mode|standard deviation|std|variance|var)\b'
    ]
    
    for pattern in aggregation_patterns:
        matches = re.findall(pattern, text.lower())
        entities["aggregations"].extend(matches)
    
    # 중복 제거
    for entity_type in entities:
        entities[entity_type] = list(set(entities[entity_type]))
    
    return entities
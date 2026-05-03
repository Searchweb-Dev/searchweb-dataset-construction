# Excel 리더 도구 - 기능 명세

## 📋 개요

엑셀 파일을 LLM이 이해할 수 있는 JSON 형식으로 변환하는 도구입니다.

---

## ✅ 구현된 기능

### 1. 엑셀 파일 읽기
- ✓ 모든 시트 자동 감지 (`sheet_name=None`)
- ✓ `.xlsx` 형식 완전 지원
- ✓ 파일 검증 (존재 여부, 형식 확인)

### 2. 데이터 구조 분석
- ✓ 시트별 메타데이터 추출
  - 행 수, 열 수, 컬럼명
- ✓ 각 컬럼의 데이터 통계
  - Non-null / Null 개수
  - 샘플 값 (최대 5개)
- ✓ 자동 타입 추론
  - integer, float, string, boolean, datetime, unknown

### 3. JSON 출력
- ✓ LLM 친화적 구조
- ✓ 완전한 UTF-8 지원
- ✓ 깔끔한 포맷팅 (indent=2)

### 4. 함수 기반 구조
```python
✓ read_excel_to_json()      # 메인 분석 함수
✓ extract_sheet_metadata()  # 시트 메타데이터 추출
✓ infer_column_type()       # 데이터 타입 추론
✓ get_excel_sheets()        # 시트 목록 조회
✓ save_schema_json()        # JSON 저장
```

### 5. 타입 힌트
- ✓ 모든 함수에 완전한 타입 힌트
- ✓ Dict, List, Optional 등 활용
- ✓ 리턴 타입 명시

### 6. 로깅
- ✓ `logging` 모듈 사용
- ✓ 파일 로깅: `reader.log` (UTF-8)
- ✓ 콘솔 로깅
- ✓ 타임스탬프 포함
- ✓ 정보, 경고, 에러 레벨

### 7. 예외 처리
- ✓ FileNotFoundError (파일 없음)
- ✓ ValueError (지원하지 않는 형식)
- ✓ 시트 읽기 실패 시 에러 정보 포함
- ✓ 상세한 에러 메시지

### 8. CLI 실행
- ✓ `if __name__ == "__main__":` 구조
- ✓ sys.argv 기반 입력 경로
- ✓ 선택적 출력 파일 경로
- ✓ 종료 코드 반환 (0: 성공, 1: 실패)

### 9. UTF-8 환경 지원
- ✓ 파일 읽기/쓰기 UTF-8 인코딩
- ✓ 로그 파일 UTF-8 인코딩
- ✓ 한글/일본어/중국어 등 모든 문자 지원

---

## 📊 데이터 타입 감지

| 입력 데이터 | 감지 타입 |
|-----------|---------|
| 1, 2, 100 | `integer` |
| 3.14, 99.99 | `float` |
| "hello", "한국어" | `string` |
| True, False | `boolean` |
| "2026-05-03" | `datetime` |
| 비어있음 | `unknown` |

---

## 🔧 주요 특징

### 성능
- 일반적인 데이터: < 1초
- 1M 행: 수십 초
- 효율적인 메모리 사용

### 안정성
- 하나의 시트 실패 → 다른 시트 계속 처리
- 타입 추론 실패 → "unknown" 반환
- 완전한 에러 로깅

### 라이브러리로 사용 가능
```python
from excel_reader import read_excel_to_json
result = read_excel_to_json("data.xlsx")
```

### CLI로 바로 실행 가능
```bash
python excel_reader.py data.xlsx output.json
```

---

## 📝 출력 예제

### JSON 구조
```json
{
  "file_path": "data.xlsx",
  "total_sheets": 2,
  "sheets": [
    {
      "sheet_name": "users",
      "row_count": 100,
      "column_count": 5,
      "columns": [
        {
          "index": 1,
          "name": "user_id",
          "type": "integer",
          "non_null_count": 100,
          "null_count": 0,
          "sample_values": [1, 2, 3, 4, 5]
        },
        {
          "index": 2,
          "name": "email",
          "type": "string",
          "non_null_count": 98,
          "null_count": 2,
          "sample_values": ["user@example.com"]
        }
      ]
    }
  ]
}
```

---

## 🚀 사용 시나리오

1. **LLM에 엑셀 분석 요청**
   ```bash
   python excel_reader.py sales.xlsx
   # schema.json으로 분석 결과 저장
   ```

2. **데이터 구조 이해**
   ```python
   from excel_reader import read_excel_to_json
   schema = read_excel_to_json("data.xlsx")
   # 각 시트의 구조를 프로그래밍으로 파악
   ```

3. **자동 문서 생성**
   - 엑셀 스키마 → JSON → LLM → 마크다운 문서

---

## 🎯 설계 원칙

✅ **심플성**: 복잡한 기능 없음, 핵심만 구현
✅ **안정성**: 예외 처리, 부분 실패 허용
✅ **확장성**: 함수 기반 구조로 활용 용이
✅ **가독성**: 명확한 변수명, 한글 주석
✅ **로깅**: 디버깅 용이한 상세 로그

---

## 📦 의존성

- `pandas` - 엑셀 읽기, 데이터 조작
- `openpyxl` - 시트명 조회

설치:
```bash
pip install pandas openpyxl
```

---

## ✨ 요구사항 충족도

| 요구사항 | 상태 | 비고 |
|---------|------|------|
| 엑셀 파일 읽기 | ✅ | .xlsx 지원 |
| 모든 시트 읽기 | ✅ | sheet_name=None 사용 |
| 메타데이터 추출 | ✅ | 행/열/타입/null 정보 |
| JSON 변환 | ✅ | LLM 친화적 구조 |
| 함수 기반 | ✅ | 5개 주요 함수 |
| 타입 힌트 | ✅ | 모든 함수 지원 |
| 로깅 | ✅ | logging 모듈 사용 |
| UTF-8 지원 | ✅ | 완전 지원 |
| 예외 처리 | ✅ | 모든 경우 처리 |
| CLI 실행 | ✅ | sys.argv 기반 |
| main() 함수 | ✅ | if __name__=="__main__" |

---

## 🔍 테스트 결과

✅ 3개 시트 (5행, 4행, 3행)
✅ 5가지 데이터 타입 (integer, string, float, boolean, datetime)
✅ Null 값 처리
✅ 샘플 데이터 추출
✅ JSON 저장
✅ 로그 기록
✅ UTF-8 한글 처리

모든 테스트 통과 ✅

# Excel 리더 도구 (excel_reader.py)

LLM이 엑셀 파일을 읽고 이해할 수 있도록 변환하는 경량 도구입니다.

## 개요

엑셀 파일의 구조를 분석하여 LLM 친화적인 JSON 형식으로 변환합니다:
- 모든 시트 자동 읽기
- 각 열의 데이터 타입 추론
- Null 값 통계
- 샘플 데이터 포함

## 설치

### 필수 라이브러리
```bash
pip install pandas openpyxl
```

## 사용법

### 1. CLI 모드

```bash
# 기본: schema.json으로 저장
python excel_reader.py data.xlsx

# 출력 파일 지정
python excel_reader.py data.xlsx output.json
```

### 2. 라이브러리로 사용

```python
from excel_reader import read_excel_to_json, save_schema_json

# 엑셀 분석
result = read_excel_to_json("data.xlsx")

# JSON 저장
save_schema_json(result, "schema.json")
```

## 출력 구조

### JSON 스키마

```json
{
  "file_path": "data.xlsx",
  "total_sheets": 3,
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
          "sample_values": ["user1@example.com", "user2@example.com"]
        }
      ]
    }
  ]
}
```

### 지원 데이터 타입

| 타입 | 설명 |
|------|------|
| `integer` | 정수 (int64, int32 등) |
| `float` | 실수 (float64, float32 등) |
| `string` | 문자열 |
| `boolean` | 불린 (true/false) |
| `datetime` | 날짜/시간 |
| `unknown` | 판별 불가능 |

## 로깅

도구는 자동으로 `reader.log` 파일에 로그를 기록합니다:

```bash
cat reader.log
```

## 핵심 함수

### `read_excel_to_json(file_path: str) -> Dict[str, Any]`
엑셀 파일 전체를 분석하여 JSON 데이터 반환

### `extract_sheet_metadata(file_path: str, sheet_name: str) -> Dict[str, Any]`
특정 시트의 메타데이터 추출

### `infer_column_type(series: pd.Series) -> str`
pandas Series에서 데이터 타입 추론

### `save_schema_json(data: Dict[str, Any], output_path: str) -> None`
분석 결과를 JSON 파일로 저장

## 예제

### 예제 1: 기본 사용

```bash
python excel_reader.py sales_data.xlsx
cat schema.json
```

### 예제 2: Python 코드에서

```python
from excel_reader import read_excel_to_json
import json

# 분석 실행
data = read_excel_to_json("products.xlsx")

# 첫 번째 시트 정보 출력
first_sheet = data["sheets"][0]
print(f"시트명: {first_sheet['sheet_name']}")
print(f"행: {first_sheet['row_count']}, 열: {first_sheet['column_count']}")

for col in first_sheet["columns"]:
    print(f"  - {col['name']}: {col['type']} ({col['non_null_count']} non-null)")
```

## UTF-8 지원

도구는 완전한 UTF-8 지원을 포함합니다:
- 한국어, 일본어, 중국어 등 모든 문자 지원
- 로그 파일도 UTF-8로 저장됨
- JSON 출력도 UTF-8 인코딩

## 에러 처리

파일이 없거나 형식이 잘못된 경우 자동으로 처리됩니다:

```
✗ 오류 발생: 파일을 찾을 수 없음: missing.xlsx
```

## 제한사항

- `.xlsx` 형식만 지원 (`.xls` 미지원)
- 매우 큰 파일(>100MB)은 메모리 사용량 증가
- 셀 공식은 값으로 읽음 (공식 자체는 읽지 않음)
- 병합된 셀은 첫 번째 값만 읽음

## 성능

- 일반적인 데이터: < 1초
- 큰 시트 (>100K 행): 5-10초
- 매우 큰 시트 (>1M 행): 수십 초

## 테스트

테스트 스크립트 실행:

```bash
python test_excel_reader.py
```

3개의 샘플 시트(사용자, 제품, 주문)로 도구 기능을 검증합니다.

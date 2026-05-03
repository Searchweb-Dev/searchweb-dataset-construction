# Token Optimization Strategy

Claude API 호출 단계에서 토큰 사용을 최소화하는 방법들:

## 1. Prompt Caching (가장 효과적: 90% 절감)

**적용 방법:**
- 반복되는 시스템 프롬프트를 `cache_control` 설정으로 캐싱
- 모든 분석 요청에서 동일한 지시문 재사용
- 첫 요청: 전체 토큰 사용
- 이후 요청: 캐시된 부분 90% 절감

**구현:**
```python
system=[
    {
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"}  # 캐싱 활성화
    }
]
```

**효과:**
- 월 1000개 분석 시: ~70K 토큰 → ~7K 토큰 절감
- 캐시 히트율 90% 이상

---

## 2. 프롬프트 최적화 (30~40% 절감)

**현재 (과다):**
```
분석 대상 URL: {url}
다음을 판단해줘:
1. AI 서비스인가? (true/false)
...
```

**최적화:**
```
Analyze {url}: is_ai_tool, category (level_1, level_2, level_3, tags), scores (utility/trust/originality 1-10), summary (한국어)
```

**효과:** 프롬프트 토큰 30~40% 감소

---

## 3. 응답 포맷 단순화 (10~20% 절감)

**현재:**
```
응답 형식:
{
  "is_ai_tool": boolean,  // 설명
  "category": {
    "level_1": "string",  // 설명
    ...
  },
  ...
}
```

**최적화:**
```
JSON only, no markdown
```

**효과:** 응답 지시문 토큰 감소

---

## 4. DB 캐싱 (중복 제거: 100% 절감)

**적용:**
```python
async def analyze_with_cache(url: str) -> dict:
    # 1. DB에서 이미 분석된 URL 확인
    cached = db.query(AISite).filter_by(url=url).first()
    if cached:
        return cached.to_dict()  # API 호출 안 함
    
    # 2. 새로운 URL만 Claude 분석
    result = await analyze_with_mcp(url)
    db.add(AISite(**result))
    db.commit()
    return result
```

**효과:**
- 같은 URL 재분석 시 100% 절감 (API 호출 자체 제거)
- 월 1000개 중 30% 반복 분석이면: ~210K 토큰 절감

---

## 예상 토큰 사용량 (월 1000개 분석)

| 항목 | 적용 전 | 적용 후 | 절감 |
|------|--------|--------|------|
| **시스템 프롬프트** | 600 | 60 | 90% |
| **사용자 메시지** | 2000 | 1200 | 40% |
| **응답** | 500 | 500 | - |
| **요청당 합계** | 3100 | 1760 | 43% |
| **월 총량 (1000회)** | 3.1M | 1.76M | 43% |
| **중복 제거 (30%)** | 3.1M | 1.23M | 60% |

**연간 비용 절감:**
- Sonnet: $3 × 3.1M → $0.37 (60% 절감)

---

## 구현 우선순위

1. **즉시 (MVP)**: Prompt Caching + DB 캐싱 → 60% 절감
2. **1개월**: 프롬프트 최적화 → 추가 40% 절감
3. **필요시**: 콘텐츠 필터링 → 20~50% 절감

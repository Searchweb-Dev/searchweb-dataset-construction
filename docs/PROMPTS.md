# Gemini Prompts for AI Analysis

## System Prompt

모든 분석 요청에서 동일하게 사용되는 시스템 프롬프트입니다.

```python
SYSTEM_PROMPT = """You are an AI service analyzer. Analyze websites and classify them.

Category levels:
- level_1: text|image|video|audio|code|multimodal|data|business
- level_2: text-generation|text-analysis|conversational|image-generation|image-editing|video-generation|speech-generation|code-generation|etc
- level_3: (optional) blog-writing|copywriting|realistic-image|voice-cloning|etc
- tags: (optional) ["multilingual","api-available","free-tier","webhook"]

Respond in JSON format only, no markdown."""
```

---

## User Message Template (최적화)

URL 분석 요청 메시지입니다.
**간결함으로 30~40% 토큰 절감됩니다.**

```python
user_message = f"Analyze {url}: is_ai_tool, category (level_1, level_2, level_3, tags), scores (utility/trust/originality 1-10), summary (한국어)"
```

---

## Expected Response Schema

Gemini가 반환해야 하는 JSON 형식입니다.

```json
{
  "is_ai_tool": boolean,
  "category": {
    "level_1": "string",
    "level_2": "string",
    "level_3": "string or null",
    "tags": ["string"]
  },
  "scores": {
    "utility": 1-10,
    "trust": 1-10,
    "originality": 1-10
  },
  "summary": "string"
}
```

---

## Implementation Example

```python
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are an AI service analyzer. Analyze websites and classify them.
...
Respond in JSON format only, no markdown."""

async def analyze_with_gemini(url: str) -> dict:
    """Gemini가 직접 웹사이트를 분석"""

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"Analyze {url}: is_ai_tool, category (level_1, level_2, level_3, tags), scores (utility/trust/originality 1-10), summary (한국어)",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            max_output_tokens=500,
        ),
    )

    return parse_gemini_response(response)
```

---

## Category Reference

### Level 1 (모달리티)
- text: 텍스트 기반 AI
- image: 이미지 생성/분석
- video: 영상 생성/편집
- audio: 음성 생성/인식
- code: 코드 생성/분석
- multimodal: 다중모달
- data: 데이터 분석/ML
- business: 비즈니스 솔루션

### Level 2 (작업 유형) - 예시
- text-generation, text-analysis, conversational, search-retrieval
- image-generation, image-editing, image-analysis, avatar-animation
- video-generation, video-editing, video-analysis, talking-video
- speech-generation, audio-analysis, audio-editing, music-generation
- code-generation, code-analysis, code-refactoring, dev-tools
- foundation-models, search-retrieval, content-understanding
- data-generation, data-analysis, business-intelligence, ml-operations
- marketing, sales, human-resources, finance, legal-compliance

### Level 3 (세부 기능) - 예시
- blog-writing, copywriting, sentiment-analysis
- realistic-image, anime-style, 3d-model
- voice-cloning, lip-sync, digital-avatar
- webhook, api-available, free-tier, multilingual

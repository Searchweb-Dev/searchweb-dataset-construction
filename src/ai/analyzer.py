"""Claude API 클라이언트 및 분석 로직."""

import json
import logging
from typing import Optional, Any
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class WebAnalyzer:
    """Claude를 사용한 웹사이트 분석기."""

    def __init__(self, api_key: Optional[str] = None):
        """Claude 클라이언트 초기화."""
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-6"

    def analyze_website(
        self,
        url: str,
        page_content: str,
        screenshot_base64: Optional[str] = None,
    ) -> dict[str, Any]:
        """웹사이트를 분석하여 AI 여부 및 분류 판정."""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": self._build_analysis_prompt(url, page_content),
                    }
                ],
            }
        ]

        # 스크린샷이 있으면 추가
        if screenshot_base64:
            messages[0]["content"].append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_base64,
                },
            })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=messages,
            system=self._get_system_prompt(),
        )

        # Claude 응답 파싱
        result = self._parse_response(response.content[0].text)
        return result

    def _build_analysis_prompt(self, url: str, page_content: str) -> str:
        """분석 프롬프트 생성."""
        return f"""
다음 웹사이트를 분석하고 AI 판별 및 분류 결과를 JSON으로 반환하세요.

URL: {url}

페이지 내용:
{page_content[:4000]}

다음 정보를 JSON으로 반환하세요:
1. is_ai_tool (boolean): AI 도구 여부
2. title (string): 서비스 제목
3. description (string): 서비스 설명 (한글)
4. categories (array): 
   - level_1 (string): 대분류
   - level_2 (string): 중분류  
   - level_3 (string): 소분류
   - is_primary (boolean): 주요 카테고리 여부
5. tags (array): 기능별 태그
6. scores (object):
   - utility (1-10): 유용성
   - trust (1-10): 신뢰도
   - originality (1-10): 독창성
7. confidence (0-1): 판단 신뢰도

JSON 형식으로만 반환하세요.
"""

    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 반환."""
        return """당신은 웹사이트 분석 전문가입니다.
주어진 URL과 페이지 내용을 분석하여 다음을 판정하세요:

1. 해당 웹사이트가 AI 도구/서비스인지 판정
2. 서비스의 분류 (대/중/소분류)
3. 주요 기능별 태그
4. 유용성, 신뢰도, 독창성을 1-10점으로 평가

판정 기준:
- AI 도구: ChatGPT, Claude, Gemini, 이미지생성AI 등 AI 기술 기반 서비스
- 신뢰도: 공식 정보 출처, 명확한 개인정보보호정책 여부
- 유용성: 실용적 가치, 사용자 편의성

신중하고 객관적으로 판정하세요."""

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        """Claude 응답 파싱."""
        try:
            # JSON 블록 추출
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("응답에서 JSON을 찾을 수 없음")
                return self._default_response()

            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            return self._default_response()

    def _default_response(self) -> dict[str, Any]:
        """기본 응답 구조."""
        return {
            "is_ai_tool": False,
            "title": "Unknown",
            "description": "분석 실패",
            "categories": [],
            "tags": [],
            "scores": {
                "utility": 0,
                "trust": 0,
                "originality": 0,
            },
            "confidence": 0,
        }

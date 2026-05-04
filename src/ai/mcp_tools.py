"""Playwright MCP 도구 설정 및 웹사이트 렌더링."""

import asyncio
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def render_website(url: str, timeout: int = 30000) -> dict[str, str]:
    """Playwright를 사용하여 웹사이트 렌더링 및 컨텐츠 추출."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})

            try:
                # 페이지 로드
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                # 텍스트 컨텐츠 추출
                text_content = await page.evaluate(
                    """() => {
                        const text = document.body.innerText;
                        return text.substring(0, 8000);
                    }"""
                )

                # 스크린샷 캡처 및 Base64 인코딩
                screenshot = await page.screenshot()
                screenshot_base64 = base64.b64encode(screenshot).decode("utf-8")

                # 메타데이터 추출
                title = await page.title()
                description = await page.evaluate(
                    """() => {
                        const meta = document.querySelector('meta[name="description"]');
                        return meta ? meta.getAttribute('content') : '';
                    }"""
                )

                return {
                    "url": url,
                    "title": title,
                    "description": description or "",
                    "text_content": text_content,
                    "screenshot_base64": screenshot_base64,
                }

            finally:
                await browser.close()

    except Exception as e:
        logger.error(f"웹사이트 렌더링 실패 ({url}): {e}")
        return {
            "url": url,
            "title": "",
            "description": "",
            "text_content": "",
            "screenshot_base64": "",
            "error": str(e),
        }


def render_website_sync(url: str, timeout: int = 30000) -> dict[str, str]:
    """동기 버전의 웹사이트 렌더링."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(render_website(url, timeout))
    finally:
        loop.close()


async def get_accessibility_tree(url: str) -> str:
    """웹사이트의 접근성 트리 추출 (AXE 기반)."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url)

                # 페이지 구조 추출
                tree = await page.evaluate(
                    """() => {
                        function getAccessibilityTree(element, depth = 0) {
                            if (depth > 5) return null;
                            
                            const role = element.getAttribute('role') || element.tagName;
                            const text = element.innerText?.substring(0, 100) || '';
                            const ariaLabel = element.getAttribute('aria-label') || '';
                            
                            const children = [];
                            for (const child of element.children) {
                                const childTree = getAccessibilityTree(child, depth + 1);
                                if (childTree) children.push(childTree);
                            }
                            
                            return { role, text, ariaLabel, children };
                        }
                        
                        return getAccessibilityTree(document.body);
                    }"""
                )

                return str(tree)

            finally:
                await browser.close()

    except Exception as e:
        logger.error(f"접근성 트리 추출 실패 ({url}): {e}")
        return f"Error: {str(e)}"

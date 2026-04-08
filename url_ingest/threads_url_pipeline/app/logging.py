from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any


ACCESS_TOKEN_QUERY_PATTERN = re.compile(r"([?&]access_token=)([^&\s]+)", re.IGNORECASE)
ENV_TOKEN_PATTERN = re.compile(r"(THREADS_API_TOKEN=)(\S+)")
THREADS_TOKEN_PATTERN = re.compile(r"\b(TH[A-Za-z0-9]{6})[A-Za-z0-9]+\b")


def _mask_sensitive_string(value: str) -> str:
    """문자열 내 액세스 토큰을 마스킹해 로그 노출을 줄인다."""
    masked = ACCESS_TOKEN_QUERY_PATTERN.sub(r"\1***REDACTED***", value)
    masked = ENV_TOKEN_PATTERN.sub(r"\1***REDACTED***", masked)
    masked = THREADS_TOKEN_PATTERN.sub(r"\1...", masked)
    return masked


def _sanitize_value(value: Any) -> Any:
    """로그 페이로드를 재귀 순회하며 민감 문자열을 마스킹한다."""
    if isinstance(value, str):
        return _mask_sensitive_string(value)
    if isinstance(value, dict):
        return {key: _sanitize_value(inner_value) for key, inner_value in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_value(item) for item in value)
    return value


class JsonFormatter(logging.Formatter):
    """구조화 로그 출력을 위한 JSON 포맷터."""

    def format(self, record: logging.LogRecord) -> str:
        """LogRecord를 JSON 문자열로 직렬화해 반환한다."""
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        standard_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        }
        for key, value in record.__dict__.items():
            if key not in standard_fields:
                payload[key] = value
        sanitized_payload = _sanitize_value(payload)
        return json.dumps(sanitized_payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """루트 로거를 JSON 포맷 기반 콘솔 출력으로 초기화한다."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # 외부 HTTP 클라이언트의 요청 URL INFO 로그를 억제해 액세스 토큰 노출을 줄인다.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """이름 기반 로거 인스턴스를 반환한다."""
    return logging.getLogger(name)

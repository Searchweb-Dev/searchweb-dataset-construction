from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qsl, urlparse, urlunparse

TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}

SECOND_LEVEL_KR = {"co.kr", "or.kr", "ac.kr", "go.kr", "ne.kr", "re.kr"}


class ShortUrlExpander(Protocol):
    """짧은 URL 확장 로직을 주입하기 위한 인터페이스."""

    def expand(self, url: str) -> str:
        """입력 URL을 확장한 URL로 반환한다."""
        raise NotImplementedError


class NoOpShortUrlExpander:
    """입력 URL을 그대로 반환하는 기본 확장기."""

    def expand(self, url: str) -> str:
        """URL 확장을 수행하지 않고 원본을 반환한다."""
        return url


@dataclass(frozen=True)
class NormalizedURL:
    """URL 정규화 결과를 담는 데이터 클래스."""
    raw_url: str
    normalized_url: str
    domain: str


def _ensure_scheme(raw_url: str) -> str:
    """스킴(http/https)이 없으면 기본 https 스킴을 보강한다."""
    candidate = raw_url.strip()
    if candidate.lower().startswith(("http://", "https://")):
        return candidate
    if candidate.lower().startswith("www."):
        return f"https://{candidate}"
    return f"https://{candidate}"


def _registered_domain(host: str) -> str:
    """호스트에서 등록 도메인 단위를 계산해 반환한다."""
    labels = [label for label in host.split(".") if label]
    if len(labels) <= 2:
        return host

    tail2 = ".".join(labels[-2:])
    if tail2 in SECOND_LEVEL_KR and len(labels) >= 3:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def apply_subdomain_policy(host: str, policy: str = "registered") -> str:
    """설정된 서브도메인 정책(full/registered)을 적용한다."""

    if policy == "full":
        return host
    return _registered_domain(host)


def normalize_url(
    raw_url: str,
    expander: ShortUrlExpander | None = None,
    subdomain_policy: str = "registered",
) -> NormalizedURL | None:
    """
    URL을 정규화하고 집계용 도메인을 계산한다.

    - host 소문자화
    - 추적 파라미터 제거
    - fragment 제거
    - www. 접두어 제거
    """

    if not raw_url or not raw_url.strip():
        return None

    expander = expander or NoOpShortUrlExpander()

    expanded = expander.expand(raw_url.strip())
    normalized_input = _ensure_scheme(expanded)
    parsed = urlparse(normalized_input)

    host = parsed.hostname.lower() if parsed.hostname else None
    if not host:
        return None
    if host.startswith("www."):
        host = host[4:]

    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]
    query_str = "&".join(f"{key}={value}" for key, value in filtered_query)

    port = parsed.port
    netloc = host
    if port and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"

    path = parsed.path or "/"
    normalized_full = urlunparse((parsed.scheme.lower(), netloc, path, "", query_str, ""))
    normalized_domain = apply_subdomain_policy(host, policy=subdomain_policy)

    return NormalizedURL(
        raw_url=raw_url,
        normalized_url=normalized_full,
        domain=normalized_domain,
    )

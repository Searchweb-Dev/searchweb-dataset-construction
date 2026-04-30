"""품질 평가 파이프라인 CLI 실행 엔트리포인트를 제공하는 모듈."""

from __future__ import annotations

import json
import hashlib
import logging
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

from config import EvalConfig
from classifiers.criteria_evaluator import WeightedQualityEvaluator
from fetchers.page_fetcher import PageFetcher
from models import DummyLLM, EvaluationResult


PipelineContext = Dict[str, Any]
PipelineStep = Callable[[Any, PipelineContext], None]
TOOL_REGISTRY_SCHEMA_VERSION = 1


def _build_shared_text_cache(all_pages: Dict[str, Any]) -> Dict[str, str]:
    """ai_scope/taxonomy가 공통으로 사용하는 텍스트 블롭 캐시를 생성한다."""
    usable_pages = [p for p in all_pages.values() if getattr(p, "ok", False)]
    page_blobs = [" ".join([p.final_url, p.title, p.meta_description, p.text[:5000]]) for p in usable_pages]
    header_blobs = [" ".join([p.final_url, p.title, p.meta_description]) for p in usable_pages]
    link_blobs = [f"{t} {u}" for p in usable_pages for t, u in p.links[:80]]

    from utils import lower

    corpus = lower(" ".join(page_blobs))
    header_blob = lower(" ".join(header_blobs))
    links_blob = lower(" ".join(link_blobs))
    ai_scope_blob = lower(" ".join(page_blobs + link_blobs))
    combined_blob = " ".join([corpus, header_blob, links_blob])
    return {
        "corpus": corpus,
        "header_blob": header_blob,
        "links_blob": links_blob,
        "combined_blob": combined_blob,
        "ai_scope_blob": ai_scope_blob,
    }


def step_fetch_and_collect_pages(evaluator: Any, ctx: PipelineContext) -> None:
    """홈페이지와 후보 페이지를 수집해 컨텍스트에 적재한다."""
    normalized_url = ctx["normalized_url"]
    logger.info("[%s] 페이지 수집 시작", normalized_url)
    
    homepage = evaluator.fetcher.fetch(normalized_url)
    if not homepage.ok:
        logger.warning("[%s] 홈페이지 수집 실패: %s", normalized_url, homepage.error)
    else:
        logger.info("[%s] 홈페이지 수집 성공 (fetched_by=%s)", normalized_url, homepage.fetched_by)

    candidate_urls = evaluator._collect_candidate_urls(normalized_url, homepage)
    if candidate_urls:
        logger.info("[%s] 후보 페이지 %d개 발견, 수집 시작", normalized_url, len(candidate_urls))
    
    candidate_workers = evaluator.config.candidate_fetch_workers
    if (
        evaluator.config.auto_tune_nested_parallel
        and evaluator.config.parallel_url_evaluation
        and evaluator.config.url_evaluation_workers > 1
    ):
        tuned_workers = max(1, candidate_workers // evaluator.config.url_evaluation_workers)
        if tuned_workers == 1 and candidate_workers > 1 and len(candidate_urls) > 1:
            tuned_workers = 2
        candidate_workers = tuned_workers

    if candidate_urls and evaluator.config.parallel_candidate_fetch and candidate_workers > 1:
        fetched_candidates = evaluator.fetcher.fetch_many(
            candidate_urls,
            max_workers=candidate_workers,
            lightweight=evaluator.config.candidate_lightweight_fetch,
        )
    else:
        fetched_candidates = {
            u: evaluator.fetcher.fetch(u, lightweight=evaluator.config.candidate_lightweight_fetch)
            for u in candidate_urls
        }

    all_pages: Dict[str, Any] = {}
    all_pages[homepage.final_url] = homepage
    for result in fetched_candidates.values():
        all_pages[result.final_url] = result

    ctx["homepage"] = homepage
    ctx["all_pages"] = all_pages
    logger.info("[%s] 페이지 수집 완료 (총 %d개 페이지)", normalized_url, len(all_pages))


def step_extract_signals(evaluator: Any, ctx: PipelineContext) -> None:
    """수집된 페이지들에서 구조화 신호(extracted)를 추출한다."""
    normalized_url = ctx["normalized_url"]
    logger.info("[%s] 구조화 신호 추출 중...", normalized_url)
    homepage = ctx["homepage"]
    all_pages = ctx["all_pages"]
    extracted = evaluator._extract_structured_signals(homepage, list(all_pages.values()))
    ctx["shared_text_cache"] = _build_shared_text_cache(all_pages)
    ctx["extracted"] = extracted


def step_classify_taxonomy(evaluator: Any, ctx: PipelineContext) -> None:
    """추출 결과에 taxonomy 분류 결과를 추가한다."""
    normalized_url = ctx["normalized_url"]
    homepage = ctx["homepage"]
    all_pages = ctx["all_pages"]
    extracted = ctx["extracted"]
    shared_text_cache = ctx.get("shared_text_cache")
    
    logger.info("[%s] Taxonomy 분류 시작", normalized_url)
    taxonomy = evaluator._classify_taxonomy(homepage, all_pages, extracted, text_cache=shared_text_cache)
    extracted["taxonomy"] = taxonomy
    
    if not taxonomy.get("taxonomy_skipped"):
        logger.info("[%s] Taxonomy 분류 완료: %s (conf=%.2f)", 
                    normalized_url, taxonomy.get("primary_category"), taxonomy.get("primary_confidence", 0))


def step_assess_ai_scope(evaluator: Any, ctx: PipelineContext) -> None:
    """평가 대상이 AI 사이트인지 스코프 게이트를 판정한다."""
    normalized_url = ctx["normalized_url"]
    homepage = ctx["homepage"]
    all_pages = ctx["all_pages"]
    extracted = ctx["extracted"]
    shared_text_cache = ctx.get("shared_text_cache")
    
    logger.info("[%s] AI Scope 판정 중...", normalized_url)
    ai_scope = evaluator._classify_ai_scope(homepage, all_pages, text_cache=shared_text_cache)
    extracted["ai_scope"] = ai_scope
    logger.info("[%s] AI Scope 판정 완료: %s (conf=%.2f)", 
                normalized_url, ai_scope.get("scope_decision"), ai_scope.get("confidence", 0))


def step_evaluate_criteria(evaluator: Any, ctx: PipelineContext) -> None:
    """품질 기준 평가 결과와 통과 집계를 계산한다."""
    normalized_url = ctx["normalized_url"]
    logger.info("[%s] 품질 지표(Criteria) 평가 시작", normalized_url)
    homepage = ctx["homepage"]
    all_pages = ctx["all_pages"]
    extracted = ctx["extracted"]
    criteria = evaluator._build_criteria(homepage, all_pages, extracted)
    passed_count = sum(1 for c in criteria.values() if c.passed)
    hard_pass = all(criteria[name].passed for name in evaluator.config.hard_criteria)

    ctx["criteria"] = criteria
    ctx["passed_count"] = passed_count
    ctx["hard_pass"] = hard_pass
    logger.info("[%s] 품질 평가 완료: %d/5 통과 (hard_pass=%s)", normalized_url, passed_count, hard_pass)


def step_score_and_predict_status(evaluator: Any, ctx: PipelineContext) -> None:
    """점수 컨텍스트를 만들고 상태를 1차 예측한다."""
    normalized_url = ctx["normalized_url"]
    homepage = ctx["homepage"]
    extracted = ctx["extracted"]
    criteria = ctx["criteria"]
    passed_count = ctx["passed_count"]
    hard_pass = ctx["hard_pass"]

    score_context = evaluator._build_score_context(criteria)
    predicted_status = evaluator._predict_status(criteria, passed_count, hard_pass, score_context)
    total_score = float(score_context.get("total_score", 0.0))

    if bool(extracted.get("anti_bot_blocked")) and not homepage.ok and passed_count == 0 and predicted_status == "rejected":
        predicted_status = "incubating"
        logger.info("[%s] Anti-bot 차단 감지되어 rejected -> incubating 완충 적용", normalized_url)

    ctx["score_context"] = score_context
    ctx["predicted_status"] = predicted_status
    logger.info("[%s] 상태 예측: %s (Score: %.1f)", normalized_url, predicted_status, total_score)


def step_review_and_finalize_status(evaluator: Any, ctx: PipelineContext) -> None:
    """리뷰 게이트를 적용해 최종 상태와 검수 사유를 확정한다."""
    normalized_url = ctx["normalized_url"]
    homepage = ctx["homepage"]
    extracted = ctx["extracted"]
    criteria = ctx["criteria"]
    predicted_status = ctx["predicted_status"]

    review_required, review_reasons = evaluator._review_gate(criteria, homepage, extracted, predicted_status)
    final_status = predicted_status

    if predicted_status == "curated" and evaluator.config.curated_requires_no_review and review_required:
        final_status = "incubating"
        if "curated 후보였지만 수동 검수 전 보류" not in review_reasons:
            review_reasons.append("curated 후보였지만 수동 검수 전 보류")
        logger.info("[%s] Curated 후보이나 리뷰 필요 사유로 인해 incubating으로 조정", normalized_url)

    ctx["review_required"] = review_required
    ctx["review_reasons"] = review_reasons
    ctx["final_status"] = final_status
    logger.info("[%s] 최종 상태 확정: %s (Review Required: %s)", normalized_url, final_status, review_required)


def step_build_summary(evaluator: Any, ctx: PipelineContext) -> None:
    """최종 결과 요약 문자열을 생성한다."""
    summary = evaluator._build_summary(
        ctx["criteria"],
        ctx["predicted_status"],
        ctx["final_status"],
        ctx["passed_count"],
        ctx["review_required"],
        ctx["review_reasons"],
        ctx.get("score_context", {}),
    )
    ctx["summary"] = summary


DEFAULT_PIPELINE_STEPS: List[PipelineStep] = [
    step_fetch_and_collect_pages,
    step_extract_signals,
    step_assess_ai_scope,
    step_classify_taxonomy,
    step_evaluate_criteria,
    step_score_and_predict_status,
    step_review_and_finalize_status,
    step_build_summary,
]


def _utc_now_iso() -> str:
    """UTC 기준 ISO-8601 문자열(초 단위)로 현재 시각을 반환한다."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_output_json_path() -> str:
    """프로젝트 루트의 result 폴더에 기본 결과 JSON 파일 경로를 생성한다."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result_dir = os.path.join(project_root, "result")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(result_dir, f"results_{timestamp}.json")


def _default_registry_json_path() -> str:
    """프로젝트 루트의 result 폴더에 기본 툴 레지스트리 JSON 파일 경로를 생성한다."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result_dir = os.path.join(project_root, "result")
    return os.path.join(result_dir, "tool_registry.json")


def _write_results_json(results: List[EvaluationResult], output_path: str) -> str:
    """평가 결과를 JSON 파일로 저장하고 실제 저장 경로를 반환한다."""
    payload = [result.to_dict() for result in results]
    resolved_path = os.path.abspath(output_path)
    parent_dir = os.path.dirname(resolved_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(resolved_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return resolved_path


def _normalize_optional_url(url: str) -> str:
    """문자열 URL을 안전하게 정규화한다(실패 시 원문 유지)."""
    from utils import normalize_url

    raw = str(url or "").strip()
    if not raw:
        return ""
    try:
        return normalize_url(raw)
    except Exception:
        return raw


def _canonical_url_from_result(result: EvaluationResult) -> str:
    """평가 결과에서 대표 canonical URL을 도출한다."""
    extracted = result.extracted if isinstance(result.extracted, dict) else {}
    candidates = [
        extracted.get("homepage_final_url", ""),
        result.normalized_url,
        result.input_url,
    ]
    for candidate in candidates:
        normalized = _normalize_optional_url(str(candidate or ""))
        if normalized:
            return normalized
    return result.normalized_url


def _build_tool_id(canonical_url: str) -> str:
    """canonical URL 기반의 안정적인 tool_id를 생성한다."""
    normalized = _normalize_optional_url(canonical_url) or "https://unknown.local/"
    parsed = urlparse(normalized)
    host_part = re.sub(r"[^a-z0-9]+", "-", (parsed.netloc or "unknown").lower()).strip("-") or "unknown"
    path_part = re.sub(r"[^a-z0-9]+", "-", (parsed.path or "/").lower().strip("/")).strip("-")
    base = host_part if not path_part else f"{host_part}-{path_part}"
    base = base[:48].rstrip("-") or "unknown"
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"tool_{base}_{digest}"


def _safe_list_of_str(values: object) -> List[str]:
    """입력값을 중복 없는 문자열 리스트로 정규화한다."""
    if not isinstance(values, list):
        return []
    out: List[str] = []
    seen = set()
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _merge_aliases(alias_groups: List[List[str]]) -> List[str]:
    """여러 alias 후보를 URL 정규화 기준으로 병합한다."""
    merged: List[str] = []
    seen = set()
    for group in alias_groups:
        for value in group:
            normalized = _normalize_optional_url(value)
            candidate = normalized or str(value).strip()
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            merged.append(candidate)
    return merged


def _derive_display_name(result: EvaluationResult, canonical_url: str, existing_name: str) -> str:
    """homepage title 우선으로 표시명을 도출하고 없으면 호스트명을 사용한다."""
    if existing_name:
        return existing_name
    extracted = result.extracted if isinstance(result.extracted, dict) else {}
    homepage_title = str(extracted.get("homepage_title", "")).strip()
    if homepage_title:
        first = homepage_title.split("|")[0].split(" - ")[0].strip()
        if first:
            return first[:120]
    host = (urlparse(canonical_url).netloc or "").strip()
    if host:
        return host
    return result.normalized_url


def _derive_lifecycle_state(final_status: str) -> str:
    """현재 파이프라인 결과를 lifecycle 상태값으로 매핑한다."""
    status = str(final_status or "").strip().lower()
    allowed = {"discovered", "screened", "incubating", "curated", "rejected", "archived"}
    if status in allowed:
        return status
    if status:
        return "screened"
    return "discovered"


def _to_float(value: object) -> Optional[float]:
    """값을 float으로 안전 변환한다."""
    try:
        return float(value)
    except Exception:
        return None


def _round_if_number(value: object, ndigits: int = 2) -> Optional[float]:
    """숫자형 값이면 반올림하고 아니면 None을 반환한다."""
    parsed = _to_float(value)
    if parsed is None:
        return None
    return round(parsed, ndigits)


def _derive_review_queue_reasons(
    result: EvaluationResult,
    previous_status: Optional[str],
    config: EvalConfig,
) -> List[str]:
    """권장 검수 큐 기준으로 자동 검수 사유 태그를 생성한다."""
    extracted = result.extracted if isinstance(result.extracted, dict) else {}
    ai_scope = extracted.get("ai_scope", {}) if isinstance(extracted.get("ai_scope"), dict) else {}
    taxonomy = extracted.get("taxonomy", {}) if isinstance(extracted.get("taxonomy"), dict) else {}

    reasons: List[str] = []
    if str(ai_scope.get("scope_decision", "")).lower() == "uncertain":
        reasons.append("ai_scope_uncertain")
    if bool(result.review_required):
        reasons.append("review_required")
    if bool(extracted.get("anti_bot_blocked")):
        reasons.append("anti_bot_blocked")

    primary_confidence = _to_float(taxonomy.get("primary_confidence"))
    if (
        primary_confidence is not None
        and primary_confidence < float(config.taxonomy_low_confidence_threshold)
    ):
        reasons.append("low_taxonomy_confidence")

    if previous_status and previous_status != result.final_status:
        reasons.append(f"status_changed:{previous_status}->{result.final_status}")
    return reasons


def _derive_reevaluation_priority(lifecycle_state: str, anti_bot_blocked: bool) -> str:
    """상태/차단 여부 기반 재평가 우선순위를 계산한다."""
    if anti_bot_blocked:
        return "retry_short_backoff"
    state = str(lifecycle_state or "").lower()
    if state == "curated":
        return "slow"
    if state == "incubating":
        return "fast"
    if state == "rejected":
        return "manual_or_long"
    if state == "archived":
        return "none"
    return "normal"


def _detect_changed_fields(
    previous: Dict[str, object],
    current_status: str,
    current_taxonomy: Optional[str],
    current_score: Optional[float],
    review_required: bool,
    review_notes: List[str],
) -> List[str]:
    """직전 스냅샷 대비 주요 변경 필드 목록을 계산한다."""
    if not previous:
        return ["new_tool"]

    changed: List[str] = []
    if str(previous.get("current_status", "")) != current_status:
        changed.append("current_status")

    prev_taxonomy = previous.get("current_taxonomy")
    if (str(prev_taxonomy) if prev_taxonomy is not None else None) != current_taxonomy:
        changed.append("current_taxonomy")

    prev_score = _to_float(previous.get("current_score"))
    if prev_score is None and current_score is not None:
        changed.append("current_score")
    elif prev_score is not None and current_score is None:
        changed.append("current_score")
    elif prev_score is not None and current_score is not None and abs(prev_score - current_score) >= 0.01:
        changed.append("current_score")

    if bool(previous.get("review_required")) != bool(review_required):
        changed.append("review_required")

    prev_notes = _safe_list_of_str(previous.get("review_notes", []))
    if prev_notes != review_notes:
        changed.append("review_notes")

    return changed


def _build_registry_history_entry(
    result: EvaluationResult,
    canonical_url: str,
    checked_at: str,
    rule_version: str,
    changed_fields: List[str],
) -> Dict[str, object]:
    """단일 실행 결과를 registry change history 항목으로 변환한다."""
    extracted = result.extracted if isinstance(result.extracted, dict) else {}
    taxonomy = extracted.get("taxonomy", {}) if isinstance(extracted.get("taxonomy"), dict) else {}
    return {
        "checked_at": checked_at,
        "input_url": result.input_url,
        "normalized_url": result.normalized_url,
        "canonical_url": canonical_url,
        "predicted_status": result.predicted_status,
        "final_status": result.final_status,
        "total_score": _round_if_number(result.total_score),
        "taxonomy": taxonomy.get("primary_category"),
        "review_required": bool(result.review_required),
        "review_reasons": _safe_list_of_str(result.review_reasons),
        "rule_version": rule_version,
        "changed_fields": changed_fields,
    }


def _load_tool_registry(registry_path: str) -> Dict[str, Dict[str, object]]:
    """registry JSON 파일을 읽어 tool_id 기준 dict로 반환한다."""
    if not registry_path:
        return {}
    resolved_path = os.path.abspath(registry_path)
    if not os.path.isfile(resolved_path):
        return {}
    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}

    raw_tools: object = {}
    if isinstance(payload, dict):
        raw_tools = payload.get("tools", {})

    tools: Dict[str, Dict[str, object]] = {}
    if isinstance(raw_tools, list):
        for item in raw_tools:
            if not isinstance(item, dict):
                continue
            tool_id = str(item.get("tool_id", "")).strip()
            if not tool_id:
                continue
            tools[tool_id] = item
    elif isinstance(raw_tools, dict):
        for tool_id, item in raw_tools.items():
            if not isinstance(item, dict):
                continue
            normalized_tool_id = str(item.get("tool_id", tool_id)).strip()
            if not normalized_tool_id:
                continue
            item["tool_id"] = normalized_tool_id
            tools[normalized_tool_id] = item
    return tools


def _write_tool_registry(registry_tools: Dict[str, Dict[str, object]], registry_path: str, checked_at: str) -> str:
    """tool_id dict를 레지스트리 JSON 형태로 저장한다."""
    if not registry_path:
        return ""
    resolved_path = os.path.abspath(registry_path)
    parent_dir = os.path.dirname(resolved_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    payload = {
        "schema_version": TOOL_REGISTRY_SCHEMA_VERSION,
        "updated_at": checked_at,
        "tools": sorted(
            registry_tools.values(),
            key=lambda item: str(item.get("tool_id", "")),
        ),
    }
    with open(resolved_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return resolved_path


def _annotate_results_with_management(
    results: List[EvaluationResult],
    source: str,
    checked_at: str,
    registry_tools: Dict[str, Dict[str, object]],
    config: EvalConfig,
) -> None:
    """평가 결과에 관리 메타데이터를 주입하고 레지스트리를 갱신한다."""
    for result in results:
        canonical_url = _canonical_url_from_result(result)
        tool_id = _build_tool_id(canonical_url)
        previous = registry_tools.get(tool_id, {})

        previous_aliases = _safe_list_of_str(previous.get("aliases", []))
        aliases = _merge_aliases(
            [
                previous_aliases,
                [result.input_url, result.normalized_url, canonical_url],
            ]
        )

        lifecycle_state = _derive_lifecycle_state(result.final_status)
        taxonomy = result.extracted.get("taxonomy", {}) if isinstance(result.extracted, dict) else {}
        current_taxonomy: Optional[str] = None
        if isinstance(taxonomy, dict) and not bool(taxonomy.get("taxonomy_skipped")):
            raw_taxonomy = taxonomy.get("primary_category")
            if raw_taxonomy is not None:
                current_taxonomy = str(raw_taxonomy)
        current_score = _round_if_number(result.total_score)
        review_notes = _safe_list_of_str(result.review_reasons)
        previous_status = str(previous.get("current_status", "")).strip() or None
        review_queue_reasons = _derive_review_queue_reasons(result, previous_status, config)

        display_name = _derive_display_name(
            result=result,
            canonical_url=canonical_url,
            existing_name=str(previous.get("display_name", "")).strip(),
        )
        first_seen_at = str(previous.get("first_seen_at", checked_at))

        management: Dict[str, object] = {
            "tool_id": tool_id,
            "display_name": display_name,
            "canonical_url": canonical_url,
            "aliases": aliases,
            "source": source,
            "first_seen_at": first_seen_at,
            "last_checked_at": checked_at,
            "lifecycle_state": lifecycle_state,
            "current_status": result.final_status,
            "current_taxonomy": current_taxonomy,
            "current_score": current_score,
            "review_required": bool(result.review_required),
            "review_notes": review_notes,
            "review_queue_reasons": review_queue_reasons,
            "reevaluation_priority": _derive_reevaluation_priority(
                lifecycle_state=lifecycle_state,
                anti_bot_blocked=bool(result.extracted.get("anti_bot_blocked")) if isinstance(result.extracted, dict) else False,
            ),
            "rule_version": config.rule_version,
        }
        result.management = management

        changed_fields = _detect_changed_fields(
            previous=previous,
            current_status=result.final_status,
            current_taxonomy=current_taxonomy,
            current_score=current_score,
            review_required=bool(result.review_required),
            review_notes=review_notes,
        )
        history_entry = _build_registry_history_entry(
            result=result,
            canonical_url=canonical_url,
            checked_at=checked_at,
            rule_version=config.rule_version,
            changed_fields=changed_fields,
        )

        history = previous.get("change_history", [])
        if not isinstance(history, list):
            history = []
        history.append(history_entry)
        max_len = max(1, int(config.max_change_history_per_tool))
        history = history[-max_len:]

        updated_record = dict(management)
        updated_record["change_history"] = history
        registry_tools[tool_id] = updated_record


def _favicon_url(canonical_url: str) -> str:
    """canonical URL에서 favicon URL을 조합한다."""
    parsed = urlparse(canonical_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    return ""


def _result_to_ai_tools_entry(result: EvaluationResult) -> Optional[Dict[str, str]]:
    """평가 결과를 ai-tools.json 항목 형태로 변환한다."""
    if not result.management:
        return None
    management = result.management
    canonical_url = str(management.get("canonical_url", "")).strip()
    if not canonical_url:
        return None

    extracted = result.extracted if isinstance(result.extracted, dict) else {}
    taxonomy = extracted.get("taxonomy", {}) if isinstance(extracted.get("taxonomy"), dict) else {}

    name = str(management.get("display_name", "")).strip()
    desc = str(taxonomy.get("one_line_summary", "")).strip() if not taxonomy.get("taxonomy_skipped") else ""
    img = _favicon_url(canonical_url)
    link = canonical_url
    category = str(taxonomy.get("primary_category", "")).strip() if not taxonomy.get("taxonomy_skipped") else ""

    return {"name": name, "desc": desc, "img": img, "link": link, "category": category}


def _load_ai_tools_json(path: str) -> List[Dict[str, str]]:
    """ai-tools.json 파일을 읽어 목록으로 반환한다."""
    resolved = os.path.abspath(path)
    if not os.path.isfile(resolved):
        return []
    try:
        with open(resolved, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        pass
    return []


def _write_ai_tools_json(items: List[Dict[str, str]], path: str) -> str:
    """ai-tools.json 파일을 저장하고 실제 저장 경로를 반환한다."""
    resolved = os.path.abspath(path)
    parent = os.path.dirname(resolved)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(resolved, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return resolved


def _derive_output_ai_tools_path(source_path: str, checked_at: str) -> str:
    """원본 ai-tools.json 경로에 타임스탬프를 붙여 새 출력 경로를 생성한다."""
    resolved = os.path.abspath(source_path)
    directory = os.path.dirname(resolved)
    name, ext = os.path.splitext(os.path.basename(resolved))
    timestamp = checked_at.replace("-", "").replace("T", "_").replace(":", "").replace("Z", "")[:15]
    return os.path.join(directory, f"{name}_{timestamp}{ext}")


def _update_ai_tools_json(
    results: List[EvaluationResult],
    ai_tools_path: str,
    checked_at: str,
    include_statuses: Optional[List[str]] = None,
) -> Optional[str]:
    """평가 결과를 ai-tools.json 기반의 새 파일에 추가하거나 기존 항목을 업데이트한다."""
    if not ai_tools_path:
        return None

    statuses = set(include_statuses or ["curated", "incubating"])
    existing = _load_ai_tools_json(ai_tools_path)

    link_index: Dict[str, int] = {}
    for i, item in enumerate(existing):
        normalized = _normalize_optional_url(str(item.get("link", "")).strip())
        if normalized:
            link_index[normalized] = i

    added = 0
    updated = 0
    for result in results:
        if result.final_status not in statuses:
            continue
        entry = _result_to_ai_tools_entry(result)
        if not entry or not entry.get("link"):
            continue
        normalized_link = _normalize_optional_url(entry["link"])
        if normalized_link in link_index:
            existing[link_index[normalized_link]] = entry
            updated += 1
        else:
            link_index[normalized_link] = len(existing)
            existing.append(entry)
            added += 1

    output_path = _derive_output_ai_tools_path(ai_tools_path, checked_at)
    saved = _write_ai_tools_json(existing, output_path)
    print(f"ai-tools.json 저장 완료: {saved} (추가 {added}건, 수정 {updated}건, 원본 유지: {os.path.abspath(ai_tools_path)})")
    return saved


def _read_urls_from_file(file_path: str) -> List[str]:
    """텍스트 파일에서 URL 목록(줄 단위)을 읽는다."""
    urls: List[str] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def _read_urls_from_json(file_path: str) -> List[str]:
    """ai-tools.json 형식 파일의 link 필드에서 URL 목록을 읽는다."""
    urls: List[str] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    link = str(item.get("link", "")).strip()
                    if link:
                        urls.append(link)
    except Exception as e:
        print(f"JSON 파일 읽기 실패 ({file_path}): {e}")
    return urls


def _parse_cli_args(args: List[str]) -> tuple[List[str], str, str, str, str]:
    """CLI 인자에서 URL 목록/결과 파일/레지스트리 파일/source/ai-tools 파일을 파싱한다."""
    collected: List[str] = []
    output_json_path = _default_output_json_path()
    registry_json_path = _default_registry_json_path()
    source = "manual_cli"
    ai_tools_json_path = ""
    i = 0
    while i < len(args):
        arg = args[i].strip()
        if not arg:
            i += 1
            continue

        if arg in ("-o", "--output-json"):
            if i + 1 >= len(args):
                raise ValueError("--output-json 옵션 뒤에 파일 경로가 필요합니다.")
            output_json_path = args[i + 1].strip()
            i += 2
            continue

        if arg == "--registry-json":
            if i + 1 >= len(args):
                raise ValueError("--registry-json 옵션 뒤에 파일 경로가 필요합니다.")
            registry_raw = args[i + 1].strip()
            if registry_raw.lower() in {"none", "off", "disable", "-"}:
                registry_json_path = ""
            else:
                registry_json_path = registry_raw
            i += 2
            continue

        if arg == "--source":
            if i + 1 >= len(args):
                raise ValueError("--source 옵션 뒤에 source 문자열이 필요합니다.")
            source = args[i + 1].strip() or "manual_cli"
            i += 2
            continue

        if arg == "--ai-tools-json":
            if i + 1 >= len(args):
                raise ValueError("--ai-tools-json 옵션 뒤에 파일 경로가 필요합니다.")
            ai_tools_json_path = args[i + 1].strip()
            i += 2
            continue

        if arg in ("-f", "--url-file"):
            if i + 1 >= len(args):
                raise ValueError("--url-file 옵션 뒤에 파일 경로가 필요합니다.")
            file_path = args[i + 1].strip()
            if file_path.lower().endswith(".json"):
                collected.extend(_read_urls_from_json(file_path))
                if not ai_tools_json_path:
                    ai_tools_json_path = file_path
            else:
                collected.extend(_read_urls_from_file(file_path))
            i += 2
            continue

        if arg.lower().endswith(".txt") and os.path.isfile(arg):
            collected.extend(_read_urls_from_file(arg))
            i += 1
            continue

        if arg.lower().endswith(".json") and os.path.isfile(arg):
            collected.extend(_read_urls_from_json(arg))
            if not ai_tools_json_path:
                ai_tools_json_path = arg
            i += 1
            continue

        collected.append(arg)
        i += 1

    deduped: List[str] = []
    seen = set()
    for url in collected:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped, output_json_path, registry_json_path, source, ai_tools_json_path


def run_quality_pipeline(
    urls: List[str],
    use_llm: bool = False,
    config: Optional[EvalConfig] = None,
) -> List[EvaluationResult]:
    """입력 URL 목록에 대해 전체 품질 평가 파이프라인을 실행한다."""
    runtime_config = config or EvalConfig(enable_llm_for_clear_desc=use_llm)
    if use_llm and not runtime_config.enable_llm_for_clear_desc:
        runtime_config.enable_llm_for_clear_desc = True
    if (
        runtime_config.parallel_url_evaluation
        and runtime_config.url_evaluation_workers > 1
        and len(urls) > 1
    ):
        thread_local = threading.local()
        created_evaluators: List[WeightedQualityEvaluator] = []
        created_evaluators_lock = threading.Lock()

        def get_worker_evaluator() -> WeightedQualityEvaluator:
            evaluator = getattr(thread_local, "evaluator", None)
            if evaluator is not None:
                return evaluator

            llm = DummyLLM() if use_llm else None
            fetcher = PageFetcher(runtime_config)
            evaluator = WeightedQualityEvaluator(fetcher=fetcher, config=runtime_config, llm=llm)
            evaluator.set_pipeline_steps(DEFAULT_PIPELINE_STEPS)
            thread_local.evaluator = evaluator
            with created_evaluators_lock:
                created_evaluators.append(evaluator)
            return evaluator

        def evaluate_one(index: int, url: str) -> tuple[int, EvaluationResult]:
            evaluator = get_worker_evaluator()
            logger.info("[%d/%d] 평가 시작: %s", index + 1, len(urls), url)
            result = evaluator.evaluate(url)
            logger.info("[%d/%d] 평가 완료: %s → %s", index + 1, len(urls), url, result.final_status)
            should_sleep = (
                evaluator.config.inter_url_delay_sec > 0
                and not evaluator.config.skip_inter_url_delay_in_parallel
            )
            if should_sleep:
                time.sleep(evaluator.config.inter_url_delay_sec)
            return index, result

        results: List[EvaluationResult | None] = [None] * len(urls)
        max_workers = min(runtime_config.url_evaluation_workers, len(urls))

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(evaluate_one, index, url): index
                    for index, url in enumerate(urls)
                }
                for future in as_completed(futures):
                    index, result = future.result()
                    results[index] = result
        finally:
            for evaluator in created_evaluators:
                try:
                    evaluator.fetcher.close()
                except Exception:
                    pass

        ordered_results: List[EvaluationResult] = []
        for index, result in enumerate(results):
            if result is None:
                raise RuntimeError(f"evaluation result missing for index={index}, url={urls[index]}")
            ordered_results.append(result)
        return ordered_results

    llm = DummyLLM() if use_llm else None
    fetcher = PageFetcher(runtime_config)
    evaluator = WeightedQualityEvaluator(fetcher=fetcher, config=runtime_config, llm=llm)
    evaluator.set_pipeline_steps(DEFAULT_PIPELINE_STEPS)
    try:
        results: List[EvaluationResult] = []
        for url in urls:
            results.append(evaluator.evaluate(url))
            if evaluator.config.inter_url_delay_sec > 0:
                time.sleep(evaluator.config.inter_url_delay_sec)
        return results
    finally:
        evaluator.fetcher.close()


def main() -> None:
    """CLI 인자를 받아 단일 파이프라인 엔트리포인트로 평가를 수행한다."""
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python run.py https://chatgpt.com https://cursor.com")
        print('  python run.py "https://news.google.com/home?hl=ko&gl=KR&ceid=KR%3Ako"')
        print("  python run.py --url-file data/site_url_list.txt")
        print("  python run.py data/site_url_list.txt")
        print("  python run.py --output-json result/results.json https://chatgpt.com")
        print("  python run.py --source ai-tools.json --registry-json result/tool_registry.json --url-file data/site_url_list.txt")
        print("  python run.py --ai-tools-json ../../ai-tools.json --url-file data/site_url_list.txt")
        print("주의: 쿼리스트링 URL은 반드시 따옴표로 감싸세요. (&가 셸에서 백그라운드 기호로 해석됩니다)")
        print("기본 출력 파일은 ai_url_classifier/result 폴더에 results_YYYYMMDD_HHMMSS.json 형식으로 저장됩니다.")
        print("기본 레지스트리 파일은 ai_url_classifier/result/tool_registry.json 입니다.")
        sys.exit(1)

    try:
        urls, output_json_path, registry_json_path, source, ai_tools_json_path = _parse_cli_args(sys.argv[1:])
    except Exception as e:
        print(f"입력 인자 처리 실패: {e}")
        sys.exit(1)
    if not urls:
        print("실행할 URL이 없습니다. URL 인자 또는 --url-file을 확인하세요.")
        sys.exit(1)

    config = EvalConfig(enable_llm_for_clear_desc=False)
    results = run_quality_pipeline(urls, use_llm=False, config=config)
    checked_at = _utc_now_iso()
    registry_tools = _load_tool_registry(registry_json_path)
    _annotate_results_with_management(
        results=results,
        source=source,
        checked_at=checked_at,
        registry_tools=registry_tools,
        config=config,
    )
    saved_path = _write_results_json(results, output_json_path)
    print(f"결과 JSON 저장 완료: {saved_path}")
    if registry_json_path:
        registry_saved_path = _write_tool_registry(registry_tools, registry_json_path, checked_at)
        print(f"툴 레지스트리 저장 완료: {registry_saved_path}")
    if ai_tools_json_path:
        _update_ai_tools_json(results, ai_tools_json_path, checked_at)


if __name__ == "__main__":
    main()

"""품질 평가 파이프라인 CLI 실행 엔트리포인트를 제공하는 모듈."""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List

from config import EvalConfig
from criteria_evaluator import WeightedQualityEvaluator
from models import DummyLLM, EvaluationResult
from page_fetcher import PageFetcher


PipelineContext = Dict[str, Any]
PipelineStep = Callable[[Any, PipelineContext], None]


def step_fetch_and_collect_pages(evaluator: Any, ctx: PipelineContext) -> None:
    """홈페이지와 후보 페이지를 수집해 컨텍스트에 적재한다."""
    normalized_url = ctx["normalized_url"]
    homepage = evaluator.fetcher.fetch(normalized_url)
    candidate_urls = evaluator._collect_candidate_urls(normalized_url, homepage)
    candidate_workers = evaluator.config.candidate_fetch_workers
    if (
        evaluator.config.auto_tune_nested_parallel
        and evaluator.config.parallel_url_evaluation
        and evaluator.config.url_evaluation_workers > 1
    ):
        candidate_workers = max(1, candidate_workers // evaluator.config.url_evaluation_workers)

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


def step_extract_signals(evaluator: Any, ctx: PipelineContext) -> None:
    """수집된 페이지들에서 구조화 신호(extracted)를 추출한다."""
    homepage = ctx["homepage"]
    all_pages = ctx["all_pages"]
    extracted = evaluator._extract_structured_signals(homepage, list(all_pages.values()))
    ctx["extracted"] = extracted


def step_classify_taxonomy(evaluator: Any, ctx: PipelineContext) -> None:
    """추출 결과에 taxonomy 분류 결과를 추가한다."""
    homepage = ctx["homepage"]
    all_pages = ctx["all_pages"]
    extracted = ctx["extracted"]
    taxonomy = evaluator._classify_taxonomy(homepage, all_pages, extracted)
    extracted["taxonomy"] = taxonomy


def step_assess_ai_scope(evaluator: Any, ctx: PipelineContext) -> None:
    """평가 대상이 AI 사이트인지 스코프 게이트를 판정한다."""
    homepage = ctx["homepage"]
    all_pages = ctx["all_pages"]
    extracted = ctx["extracted"]
    ai_scope = evaluator._classify_ai_scope(homepage, all_pages)
    extracted["ai_scope"] = ai_scope


def step_evaluate_criteria(evaluator: Any, ctx: PipelineContext) -> None:
    """품질 기준 평가 결과와 통과 집계를 계산한다."""
    homepage = ctx["homepage"]
    all_pages = ctx["all_pages"]
    extracted = ctx["extracted"]
    criteria = evaluator._build_criteria(homepage, all_pages, extracted)
    passed_count = sum(1 for c in criteria.values() if c.passed)
    hard_pass = all(criteria[name].passed for name in evaluator.config.hard_criteria)

    ctx["criteria"] = criteria
    ctx["passed_count"] = passed_count
    ctx["hard_pass"] = hard_pass


def step_score_and_predict_status(evaluator: Any, ctx: PipelineContext) -> None:
    """점수 컨텍스트를 만들고 상태를 1차 예측한다."""
    homepage = ctx["homepage"]
    extracted = ctx["extracted"]
    criteria = ctx["criteria"]
    passed_count = ctx["passed_count"]
    hard_pass = ctx["hard_pass"]

    score_context = evaluator._build_score_context(criteria)
    predicted_status = evaluator._predict_status(criteria, passed_count, hard_pass, score_context)

    if bool(extracted.get("anti_bot_blocked")) and not homepage.ok and passed_count == 0 and predicted_status == "rejected":
        predicted_status = "incubating"

    ctx["score_context"] = score_context
    ctx["predicted_status"] = predicted_status


def step_review_and_finalize_status(evaluator: Any, ctx: PipelineContext) -> None:
    """리뷰 게이트를 적용해 최종 상태와 검수 사유를 확정한다."""
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

    ctx["review_required"] = review_required
    ctx["review_reasons"] = review_reasons
    ctx["final_status"] = final_status


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


def _collect_urls_from_cli(args: List[str]) -> List[str]:
    """CLI 인자(URL/파일)를 통합해 최종 URL 목록을 생성한다."""
    collected: List[str] = []
    i = 0
    while i < len(args):
        arg = args[i].strip()
        if not arg:
            i += 1
            continue

        if arg in ("-f", "--url-file"):
            if i + 1 >= len(args):
                raise ValueError("--url-file 옵션 뒤에 파일 경로가 필요합니다.")
            file_path = args[i + 1].strip()
            collected.extend(_read_urls_from_file(file_path))
            i += 2
            continue

        if arg.lower().endswith(".txt") and os.path.isfile(arg):
            collected.extend(_read_urls_from_file(arg))
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
    return deduped


def run_quality_pipeline(urls: List[str], use_llm: bool = False) -> List[EvaluationResult]:
    """입력 URL 목록에 대해 전체 품질 평가 파이프라인을 실행한다."""
    config = EvalConfig(enable_llm_for_clear_desc=use_llm)
    if (
        config.parallel_url_evaluation
        and config.url_evaluation_workers > 1
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
            fetcher = PageFetcher(config)
            evaluator = WeightedQualityEvaluator(fetcher=fetcher, config=config, llm=llm)
            evaluator.set_pipeline_steps(DEFAULT_PIPELINE_STEPS)
            thread_local.evaluator = evaluator
            with created_evaluators_lock:
                created_evaluators.append(evaluator)
            return evaluator

        def evaluate_one(index: int, url: str) -> tuple[int, EvaluationResult]:
            evaluator = get_worker_evaluator()
            result = evaluator.evaluate(url)
            should_sleep = (
                evaluator.config.inter_url_delay_sec > 0
                and not evaluator.config.skip_inter_url_delay_in_parallel
            )
            if should_sleep:
                time.sleep(evaluator.config.inter_url_delay_sec)
            return index, result

        results: List[EvaluationResult | None] = [None] * len(urls)
        max_workers = min(config.url_evaluation_workers, len(urls))

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
    fetcher = PageFetcher(config)
    evaluator = WeightedQualityEvaluator(fetcher=fetcher, config=config, llm=llm)
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
        print("  python src/main.py https://chatgpt.com https://cursor.com")
        print('  python src/main.py "https://news.google.com/home?hl=ko&gl=KR&ceid=KR%3Ako"')
        print("  python src/main.py --url-file site_url_list.txt")
        print("  python src/main.py site_url_list.txt")
        print("주의: 쿼리스트링 URL은 반드시 따옴표로 감싸세요. (&가 셸에서 백그라운드 기호로 해석됩니다)")
        sys.exit(1)

    try:
        urls = _collect_urls_from_cli(sys.argv[1:])
    except Exception as e:
        print(f"입력 인자 처리 실패: {e}")
        sys.exit(1)
    if not urls:
        print("실행할 URL이 없습니다. URL 인자 또는 --url-file을 확인하세요.")
        sys.exit(1)

    results = run_quality_pipeline(urls, use_llm=False)
    print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

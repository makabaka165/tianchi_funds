from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

import baseline_weekday_mean as model
from evaluate import (
    GateThresholds,
    check_submission_format,
    official_proxy_score,
    relative_error,
)
from rolling_validate import DEFAULT_MONTHS, evaluate_month, load_daily_features


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
ROLLING_DETAIL_PATH = OUTPUT_DIR / "rolling_validation_2014_05_08.csv"
SUBMISSION_PATH = OUTPUT_DIR / "tc_comp_predict_table.csv"
SEARCH_CSV_PATH = OUTPUT_DIR / "candidate_search_report.csv"
SEARCH_JSON_PATH = OUTPUT_DIR / "candidate_search_report.json"

PURCHASE_FACTOR_GRID = [
    0.86,
    0.88,
    0.90,
    0.92,
    0.94,
    0.96,
    0.98,
    1.02,
    1.03,
    1.04,
    1.06,
    1.08,
    1.10,
    1.12,
    1.15,
    1.18,
    1.20,
]
REDEEM_FACTOR_GRID = [
    0.80,
    0.84,
    0.86,
    0.88,
    0.90,
    0.92,
    0.94,
    0.95,
    0.96,
    0.97,
    0.98,
    1.02,
    1.03,
    1.04,
    1.06,
    1.08,
    1.10,
    1.12,
    1.15,
    1.18,
    1.20,
]
RANGE_FACTOR_GRID = [0.90, 0.92, 0.94, 0.96, 0.98, 1.02, 1.03, 1.04, 1.06, 1.08, 1.10]
PARAMETER_GRIDS = {
    "PURCHASE_CALIBRATION": [0.94, 0.95, 0.96, 0.97, 0.99, 1.00, 1.01],
    "REDEEM_CALIBRATION": [0.82, 0.83, 0.84, 0.86, 0.87, 0.88],
    "PURCHASE_OPTIMIZED_BLEND": [0.00, 0.01, 0.02, 0.04, 0.05, 0.06, 0.08],
}


@dataclass(frozen=True)
class PostAdjustment:
    kind: str
    target: str
    factor: float
    label: str
    day: int | None = None
    weekday: int | None = None
    start_day: int | None = None
    end_day: int | None = None

    def validation_mask(self, dates: pd.Series) -> pd.Series:
        if self.day is not None:
            return dates.dt.day == self.day
        if self.weekday is not None:
            return dates.dt.weekday == self.weekday
        if self.start_day is not None and self.end_day is not None:
            return dates.dt.day.between(self.start_day, self.end_day)
        raise ValueError(f"Candidate {self.label} has no date selector")

    def affected_submission_dates(self) -> str:
        dates = pd.Series(pd.date_range("2014-09-01", "2014-09-30"))
        affected = dates[self.validation_mask(dates)].dt.strftime("%Y%m%d").tolist()
        return ",".join(affected)


def load_base_detail(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing rolling validation detail: {path}. Run src/rolling_validate.py first."
        )
    return pd.read_csv(path, parse_dates=["date"])


def enrich_detail(detail: pd.DataFrame) -> pd.DataFrame:
    enriched = detail.copy()
    purchase_error = relative_error(enriched["purchase"], enriched["pred_purchase"])
    redeem_error = relative_error(enriched["redeem"], enriched["pred_redeem"])
    enriched["purchase_relative_error"] = purchase_error
    enriched["redeem_relative_error"] = redeem_error
    enriched["weighted_relative_error"] = 0.45 * purchase_error + 0.55 * redeem_error
    enriched["purchase_proxy_score"] = official_proxy_score(purchase_error)
    enriched["redeem_proxy_score"] = official_proxy_score(redeem_error)
    enriched["weighted_proxy_score"] = (
        0.45 * enriched["purchase_proxy_score"] + 0.55 * enriched["redeem_proxy_score"]
    )
    return enriched


def summarize_detail(detail: pd.DataFrame) -> dict[str, Any]:
    enriched = enrich_detail(detail)
    months: dict[str, dict[str, float]] = {}
    for month, group in enriched.groupby("validation_month", sort=True):
        months[month] = {
            "purchase_relative_error_mean": float(group["purchase_relative_error"].mean()),
            "redeem_relative_error_mean": float(group["redeem_relative_error"].mean()),
            "weighted_relative_error_mean": float(group["weighted_relative_error"].mean()),
            "weighted_proxy_score_mean": float(group["weighted_proxy_score"].mean()),
            "bad_day_rate_max": float(
                max(
                    (group["purchase_relative_error"] > 0.3).mean(),
                    (group["redeem_relative_error"] > 0.3).mean(),
                )
            ),
        }

    overall = {
        "purchase_relative_error_mean": float(enriched["purchase_relative_error"].mean()),
        "redeem_relative_error_mean": float(enriched["redeem_relative_error"].mean()),
        "weighted_relative_error_mean": float(enriched["weighted_relative_error"].mean()),
        "weighted_proxy_score_mean": float(enriched["weighted_proxy_score"].mean()),
        "bad_day_rate_max": float(
            max(
                (enriched["purchase_relative_error"] > 0.3).mean(),
                (enriched["redeem_relative_error"] > 0.3).mean(),
            )
        ),
    }
    return {"months": months, "overall": overall}


def august_gate_failures(
    august_stats: dict[str, float],
    submission_issues: list[str],
) -> list[str]:
    thresholds = GateThresholds()
    failures = list(submission_issues)

    if august_stats["weighted_relative_error_mean"] > thresholds.max_weighted_relative_error:
        failures.append("8月 weighted_relative_error_mean 超过门限")
    if august_stats["purchase_relative_error_mean"] > thresholds.max_purchase_relative_error:
        failures.append("8月 purchase_relative_error_mean 超过门限")
    if august_stats["redeem_relative_error_mean"] > thresholds.max_redeem_relative_error:
        failures.append("8月 redeem_relative_error_mean 超过门限")
    if august_stats["weighted_proxy_score_mean"] < thresholds.min_weighted_proxy_score:
        failures.append("8月 weighted_proxy_score_mean 低于门限")
    if august_stats["bad_day_rate_max"] > thresholds.max_bad_day_rate:
        failures.append("8月 bad_day_rate_max 超过门限")
    return failures


def result_row(
    *,
    label: str,
    kind: str,
    target: str,
    factor: float | None,
    overrides: dict[str, float] | None,
    summary: dict[str, Any],
    base_summary: dict[str, Any],
    submission_issues: list[str],
    affected_validation_rows: int,
    affected_submission_dates: str,
    max_month_drop: float,
    min_overall_delta: float,
) -> dict[str, Any]:
    base_months = base_summary["months"]
    months = summary["months"]
    month_deltas = {
        month: months[month]["weighted_proxy_score_mean"]
        - base_months[month]["weighted_proxy_score_mean"]
        for month in months
    }
    max_month_delta = min(month_deltas.values())
    overall = summary["overall"]
    base_overall = base_summary["overall"]
    overall_delta = (
        overall["weighted_proxy_score_mean"] - base_overall["weighted_proxy_score_mean"]
    )
    august = months["2014-08"]
    gate_failures = august_gate_failures(august, submission_issues)
    risk_failures = []
    if overall_delta <= min_overall_delta:
        risk_failures.append("overall proxy 未超过当前基线")
    if max_month_delta < -max_month_drop:
        risk_failures.append("单月 proxy 下滑超过风险线")

    decision = "KEEP_CANDIDATE" if not gate_failures and not risk_failures else "SKIP"
    return {
        "decision": decision,
        "label": label,
        "kind": kind,
        "target": target,
        "factor": factor,
        "overrides": json.dumps(overrides or {}, sort_keys=True),
        "overall_proxy": overall["weighted_proxy_score_mean"],
        "overall_delta": overall_delta,
        "overall_weighted_error": overall["weighted_relative_error_mean"],
        "august_proxy": august["weighted_proxy_score_mean"],
        "august_weighted_error": august["weighted_relative_error_mean"],
        "august_bad_day_rate_max": august["bad_day_rate_max"],
        "max_month_delta": max_month_delta,
        "bad_day_rate_max": overall["bad_day_rate_max"],
        "affected_validation_rows": affected_validation_rows,
        "affected_submission_dates": affected_submission_dates,
        "month_proxy_deltas": json.dumps(month_deltas, sort_keys=True),
        "gate_failures": "; ".join(gate_failures),
        "risk_failures": "; ".join(risk_failures),
    }


def apply_post_adjustment(detail: pd.DataFrame, candidate: PostAdjustment) -> tuple[pd.DataFrame, int]:
    adjusted = detail.copy()
    mask = candidate.validation_mask(adjusted["date"])
    column = f"pred_{candidate.target}"
    adjusted.loc[mask, column] = (
        adjusted.loc[mask, column].astype(float) * candidate.factor
    ).round().clip(lower=0).astype("int64")
    return adjusted, int(mask.sum())


def generate_post_adjustments() -> list[PostAdjustment]:
    candidates: list[PostAdjustment] = []
    for target, factors in [
        ("purchase", PURCHASE_FACTOR_GRID),
        ("redeem", REDEEM_FACTOR_GRID),
    ]:
        for day in range(1, 32):
            for factor in factors:
                candidates.append(
                    PostAdjustment(
                        kind="single_day",
                        target=target,
                        factor=factor,
                        day=day,
                        label=f"{target}_day{day}_x{factor:.2f}",
                    )
                )
        for weekday in range(7):
            weekday_grid = PURCHASE_FACTOR_GRID if target == "purchase" else REDEEM_FACTOR_GRID
            for factor in weekday_grid:
                candidates.append(
                    PostAdjustment(
                        kind="weekday",
                        target=target,
                        factor=factor,
                        weekday=weekday,
                        label=f"{target}_weekday{weekday}_x{factor:.2f}",
                    )
                )
        for window in [2, 3, 4, 7]:
            for start_day in range(1, 32 - window + 1):
                end_day = start_day + window - 1
                for factor in RANGE_FACTOR_GRID:
                    candidates.append(
                        PostAdjustment(
                            kind="day_range",
                            target=target,
                            factor=factor,
                            start_day=start_day,
                            end_day=end_day,
                            label=f"{target}_day{start_day}_{end_day}_x{factor:.2f}",
                        )
                    )
    return candidates


def evaluate_parameter_candidate(
    overrides: dict[str, float],
    months: list[str],
) -> pd.DataFrame:
    original = {name: getattr(model, name) for name in overrides}
    try:
        for name, value in overrides.items():
            setattr(model, name, value)
        features = load_daily_features()
        return pd.concat(
            [evaluate_month(features, month) for month in months],
            ignore_index=True,
        )
    finally:
        for name, value in original.items():
            setattr(model, name, value)


def generate_parameter_overrides() -> list[tuple[str, dict[str, float]]]:
    candidates: list[tuple[str, dict[str, float]]] = []
    for parameter, values in PARAMETER_GRIDS.items():
        current = float(getattr(model, parameter))
        for value in values:
            if abs(value - current) < 1e-12:
                continue
            label = f"param_{parameter}_{value:.2f}"
            candidates.append((label, {parameter: value}))
    return candidates


def run_search(args: argparse.Namespace) -> pd.DataFrame:
    base_detail = load_base_detail(args.detail)
    base_summary = summarize_detail(base_detail)
    submission_issues = check_submission_format(args.submission)
    rows: list[dict[str, Any]] = []

    for candidate in generate_post_adjustments():
        adjusted, affected_rows = apply_post_adjustment(base_detail, candidate)
        summary = summarize_detail(adjusted)
        rows.append(
            result_row(
                label=candidate.label,
                kind=candidate.kind,
                target=candidate.target,
                factor=candidate.factor,
                overrides=None,
                summary=summary,
                base_summary=base_summary,
                submission_issues=submission_issues,
                affected_validation_rows=affected_rows,
                affected_submission_dates=candidate.affected_submission_dates(),
                max_month_drop=args.max_month_drop,
                min_overall_delta=args.min_overall_delta,
            )
        )

    if not args.skip_parameter_search:
        for label, overrides in generate_parameter_overrides():
            detail = evaluate_parameter_candidate(overrides, args.months)
            summary = summarize_detail(detail)
            rows.append(
                result_row(
                    label=label,
                    kind="parameter",
                    target="model",
                    factor=None,
                    overrides=overrides,
                    summary=summary,
                    base_summary=base_summary,
                    submission_issues=submission_issues,
                    affected_validation_rows=len(detail),
                    affected_submission_dates="20140901-20140930",
                    max_month_drop=args.max_month_drop,
                    min_overall_delta=args.min_overall_delta,
                )
            )

    results = pd.DataFrame(rows)
    results = results.sort_values(
        by=["decision", "overall_delta", "max_month_delta"],
        ascending=[True, False, False],
    ).reset_index(drop=True)
    return results


def write_reports(
    results: pd.DataFrame,
    csv_path: Path,
    json_path: Path,
    save_limit: int,
) -> pd.DataFrame:
    csv_path.parent.mkdir(exist_ok=True)
    saved = results if save_limit <= 0 else results.head(save_limit)
    saved.to_csv(csv_path, index=False, encoding="utf-8")
    json_path.write_text(
        json.dumps(saved.to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return saved


def print_top(results: pd.DataFrame, top: int) -> None:
    keep = results[results["decision"] == "KEEP_CANDIDATE"].head(top)
    print("Candidate search report")
    print("=======================")
    if keep.empty:
        print("No KEEP_CANDIDATE rows found under the current risk rules.")
        return
    for idx, row in enumerate(keep.itertuples(index=False), start=1):
        print(
            f"{idx:02d}. {row.label}: overall_delta={row.overall_delta:+.6f}, "
            f"overall={row.overall_proxy:.6f}, august={row.august_proxy:.6f}, "
            f"max_month_delta={row.max_month_delta:+.6f}, "
            f"affected={row.affected_submission_dates}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search read-only post-adjustment and parameter candidates from the current "
            "rolling validation baseline."
        )
    )
    parser.add_argument("--detail", type=Path, default=ROLLING_DETAIL_PATH)
    parser.add_argument("--submission", type=Path, default=SUBMISSION_PATH)
    parser.add_argument("--csv", type=Path, default=SEARCH_CSV_PATH)
    parser.add_argument("--json", type=Path, default=SEARCH_JSON_PATH)
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument(
        "--save-limit",
        type=int,
        default=200,
        help="Number of sorted rows to save. Use 0 to save the full search result.",
    )
    parser.add_argument("--max-month-drop", type=float, default=0.05)
    parser.add_argument("--min-overall-delta", type=float, default=0.0)
    parser.add_argument("--months", nargs="+", default=DEFAULT_MONTHS)
    parser.add_argument(
        "--skip-parameter-search",
        action="store_true",
        help="Only scan post-adjustment candidates from the existing rolling detail file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_search(args)
    saved = write_reports(results, args.csv, args.json, args.save_limit)
    print_top(results, args.top)
    print()
    print(f"Scanned rows: {len(results)}")
    print(f"Saved rows:   {len(saved)}")
    print(f"Saved CSV:  {args.csv}")
    print(f"Saved JSON: {args.json}")


if __name__ == "__main__":
    main()

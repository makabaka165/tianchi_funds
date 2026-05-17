from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from evaluate import GateThresholds, check_submission_format, official_proxy_score, relative_error
from rolling_validate import DEFAULT_MONTHS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
ROLLING_DETAIL_PATH = OUTPUT_DIR / "rolling_validation_2014_05_08.csv"
SUBMISSION_PATH = OUTPUT_DIR / "tc_comp_predict_table.csv"
SEARCH_CSV_PATH = OUTPUT_DIR / "candidate_search_report.csv"
SEARCH_JSON_PATH = OUTPUT_DIR / "candidate_search_report.json"

REDEEM_DAY17_GRID = [0.98, 1.00, 1.02, 1.04, 1.06]
REDEEM_DAY30_GRID = [0.96, 1.00, 1.02, 1.04, 1.06, 1.08]
REDEEM_LATE_MONTH_GRID = [1.04, 1.06, 1.08, 1.10]
REDEEM_MONTH_END_GRID = [1.02, 1.04, 1.06, 1.08]
REDEEM_WEEKDAY6_GRID = [0.95, 0.97, 1.03, 1.05]


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
        failures.append("8月 weighted_relative_error_mean exceeds gate")
    if august_stats["purchase_relative_error_mean"] > thresholds.max_purchase_relative_error:
        failures.append("8月 purchase_relative_error_mean exceeds gate")
    if august_stats["redeem_relative_error_mean"] > thresholds.max_redeem_relative_error:
        failures.append("8月 redeem_relative_error_mean exceeds gate")
    if august_stats["weighted_proxy_score_mean"] < thresholds.min_weighted_proxy_score:
        failures.append("8月 weighted_proxy_score_mean below gate")
    if august_stats["bad_day_rate_max"] > thresholds.max_bad_day_rate:
        failures.append("8月 bad_day_rate_max exceeds gate")
    return failures


def result_row(
    *,
    label: str,
    kind: str,
    target: str,
    factor: float,
    summary: dict[str, Any],
    base_summary: dict[str, Any],
    submission_issues: list[str],
    affected_validation_rows: int,
    affected_submission_dates: str,
    max_month_drop: float,
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
    if overall["weighted_relative_error_mean"] > base_overall["weighted_relative_error_mean"]:
        risk_failures.append("overall weighted_relative_error_mean worse than baseline")
    if august["weighted_relative_error_mean"] > base_months["2014-08"]["weighted_relative_error_mean"]:
        risk_failures.append("8月 weighted_relative_error_mean worse than baseline")
    if months["2014-06"]["weighted_relative_error_mean"] > base_months["2014-06"]["weighted_relative_error_mean"]:
        risk_failures.append("2014-06 weighted_relative_error_mean worse than baseline")
    if overall["bad_day_rate_max"] > base_overall["bad_day_rate_max"]:
        risk_failures.append("overall bad_day_rate_max worse than baseline")
    if max_month_delta < -max_month_drop:
        risk_failures.append("monthly proxy drop exceeds risk threshold")

    decision = "KEEP_CANDIDATE" if not gate_failures and not risk_failures else "SKIP"
    return {
        "decision": decision,
        "label": label,
        "kind": kind,
        "target": target,
        "factor": factor,
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
    for factor in REDEEM_DAY17_GRID:
        candidates.append(
            PostAdjustment(
                kind="single_day",
                target="redeem",
                factor=factor,
                day=17,
                label=f"redeem_day17_x{factor:.2f}",
            )
        )
    for factor in REDEEM_DAY30_GRID:
        candidates.append(
            PostAdjustment(
                kind="single_day",
                target="redeem",
                factor=factor,
                day=30,
                label=f"redeem_day30_x{factor:.2f}",
            )
        )
    for factor in REDEEM_LATE_MONTH_GRID:
        candidates.append(
            PostAdjustment(
                kind="day_range",
                target="redeem",
                factor=factor,
                start_day=22,
                end_day=29,
                label=f"redeem_day22_29_x{factor:.2f}",
            )
        )
    for factor in REDEEM_MONTH_END_GRID:
        candidates.append(
            PostAdjustment(
                kind="day_range",
                target="redeem",
                factor=factor,
                start_day=28,
                end_day=31,
                label=f"redeem_day28_31_x{factor:.2f}",
            )
        )
    for factor in REDEEM_WEEKDAY6_GRID:
        candidates.append(
            PostAdjustment(
                kind="weekday",
                target="redeem",
                factor=factor,
                weekday=6,
                label=f"redeem_weekday6_x{factor:.2f}",
            )
        )
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
                summary=summary,
                base_summary=base_summary,
                submission_issues=submission_issues,
                affected_validation_rows=affected_rows,
                affected_submission_dates=candidate.affected_submission_dates(),
                max_month_drop=args.max_month_drop,
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
            "Search conservative redeem-only candidates from the current rolling validation baseline."
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
    parser.add_argument("--max-month-drop", type=float, default=0.03)
    parser.add_argument("--months", nargs="+", default=DEFAULT_MONTHS)
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

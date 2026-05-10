from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VALIDATION_PATH = ROOT / "output" / "validation_august_2014.csv"
DEFAULT_SUBMISSION_PATH = ROOT / "output" / "tc_comp_predict_table.csv"
DEFAULT_REPORT_PATH = ROOT / "output" / "evaluation_report.json"


@dataclass(frozen=True)
class GateThresholds:
    max_weighted_relative_error: float = 0.18
    max_purchase_relative_error: float = 0.16
    max_redeem_relative_error: float = 0.22
    min_weighted_proxy_score: float = 4.0
    max_bad_day_rate: float = 0.20


def relative_error(actual: pd.Series, predicted: pd.Series) -> pd.Series:
    actual = actual.astype(float)
    predicted = predicted.astype(float)
    denominator = actual.replace(0, np.nan)
    error = (predicted - actual).abs() / denominator
    return error.fillna(0)


def official_proxy_score(error: pd.Series) -> pd.Series:
    return (10 * (1 - error / 0.3)).clip(lower=0)


def weighted_stats(validation: pd.DataFrame) -> dict[str, float]:
    purchase_error = relative_error(
        validation["purchase"], validation["pred_purchase"]
    )
    redeem_error = relative_error(validation["redeem"], validation["pred_redeem"])
    weighted_error = 0.45 * purchase_error + 0.55 * redeem_error

    purchase_score = official_proxy_score(purchase_error)
    redeem_score = official_proxy_score(redeem_error)
    weighted_score = 0.45 * purchase_score + 0.55 * redeem_score

    return {
        "purchase_relative_error_mean": float(purchase_error.mean()),
        "purchase_relative_error_median": float(purchase_error.median()),
        "purchase_relative_error_max": float(purchase_error.max()),
        "purchase_bad_day_rate": float((purchase_error > 0.3).mean()),
        "redeem_relative_error_mean": float(redeem_error.mean()),
        "redeem_relative_error_median": float(redeem_error.median()),
        "redeem_relative_error_max": float(redeem_error.max()),
        "redeem_bad_day_rate": float((redeem_error > 0.3).mean()),
        "weighted_relative_error_mean": float(weighted_error.mean()),
        "weighted_relative_error_median": float(weighted_error.median()),
        "weighted_relative_error_max": float(weighted_error.max()),
        "weighted_proxy_score_mean": float(weighted_score.mean()),
        "weighted_proxy_score_median": float(weighted_score.median()),
        "weighted_proxy_score_min": float(weighted_score.min()),
        "bad_day_rate_max": float(
            max((purchase_error > 0.3).mean(), (redeem_error > 0.3).mean())
        ),
    }


def check_submission_format(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"submission file does not exist: {path}"]

    submission = pd.read_csv(path, header=None)
    if submission.shape != (30, 3):
        issues.append(
            f"submission shape should be (30, 3), got {submission.shape}"
        )

    if submission.shape[1] == 3:
        submission.columns = ["report_date", "purchase", "redeem"]
        expected_dates = pd.date_range("2014-09-01", "2014-09-30").strftime("%Y%m%d")
        actual_dates = submission["report_date"].astype(str).tolist()
        if actual_dates != expected_dates.tolist():
            issues.append("submission dates are not exactly 20140901-20140930")

        for column in ["purchase", "redeem"]:
            numeric = pd.to_numeric(submission[column], errors="coerce")
            if numeric.isna().any():
                issues.append(f"{column} contains non-numeric values")
            if (numeric < 0).any():
                issues.append(f"{column} contains negative values")
            if not np.all(np.equal(np.mod(numeric, 1), 0)):
                issues.append(f"{column} contains non-integer values")

    return issues


def decide_candidate(stats: dict[str, float], submission_issues: list[str]) -> tuple[bool, list[str]]:
    thresholds = GateThresholds()
    failures: list[str] = []

    if submission_issues:
        failures.extend(submission_issues)
    if stats["weighted_relative_error_mean"] > thresholds.max_weighted_relative_error:
        failures.append(
            "weighted_relative_error_mean "
            f"{stats['weighted_relative_error_mean']:.6f} "
            f"> {thresholds.max_weighted_relative_error:.6f}"
        )
    if stats["purchase_relative_error_mean"] > thresholds.max_purchase_relative_error:
        failures.append(
            "purchase_relative_error_mean "
            f"{stats['purchase_relative_error_mean']:.6f} "
            f"> {thresholds.max_purchase_relative_error:.6f}"
        )
    if stats["redeem_relative_error_mean"] > thresholds.max_redeem_relative_error:
        failures.append(
            "redeem_relative_error_mean "
            f"{stats['redeem_relative_error_mean']:.6f} "
            f"> {thresholds.max_redeem_relative_error:.6f}"
        )
    if stats["weighted_proxy_score_mean"] < thresholds.min_weighted_proxy_score:
        failures.append(
            "weighted_proxy_score_mean "
            f"{stats['weighted_proxy_score_mean']:.6f} "
            f"< {thresholds.min_weighted_proxy_score:.6f}"
        )
    if stats["bad_day_rate_max"] > thresholds.max_bad_day_rate:
        failures.append(
            f"bad_day_rate_max {stats['bad_day_rate_max']:.6f} "
            f"> {thresholds.max_bad_day_rate:.6f}"
        )

    return not failures, failures


def evaluate(
    validation_path: Path,
    submission_path: Path,
    report_path: Path,
) -> dict[str, object]:
    validation = pd.read_csv(validation_path)
    required = {"purchase", "redeem", "pred_purchase", "pred_redeem"}
    missing = required - set(validation.columns)
    if missing:
        raise ValueError(f"validation file missing columns: {sorted(missing)}")

    stats = weighted_stats(validation)
    submission_issues = check_submission_format(submission_path)
    is_candidate, gate_failures = decide_candidate(stats, submission_issues)

    report: dict[str, object] = {
        "validation_path": str(validation_path),
        "submission_path": str(submission_path),
        "thresholds": asdict(GateThresholds()),
        "stats": stats,
        "submission_issues": submission_issues,
        "is_official_submission_candidate": is_candidate,
        "gate_failures": gate_failures,
    }

    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def print_report(report: dict[str, object]) -> None:
    stats = report["stats"]
    assert isinstance(stats, dict)

    print("Local evaluation report")
    print("=======================")
    print(f"Validation file: {report['validation_path']}")
    print(f"Submission file: {report['submission_path']}")
    print()
    print(f"Purchase relative error mean: {stats['purchase_relative_error_mean']:.6f}")
    print(f"Redeem relative error mean:   {stats['redeem_relative_error_mean']:.6f}")
    print(f"Weighted relative error mean: {stats['weighted_relative_error_mean']:.6f}")
    print(f"Weighted proxy score mean:    {stats['weighted_proxy_score_mean']:.6f}")
    print(f"Bad day rate max:             {stats['bad_day_rate_max']:.6f}")
    print()

    if report["is_official_submission_candidate"]:
        print("Decision: PASS - keep as official submission candidate")
    else:
        print("Decision: FAIL - do not submit this version to the official site yet")
        print("Gate failures:")
        for failure in report["gate_failures"]:
            print(f"- {failure}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate local validation results with an official-like proxy gate."
    )
    parser.add_argument(
        "--validation",
        type=Path,
        default=DEFAULT_VALIDATION_PATH,
        help="Validation CSV containing actual and predicted August values.",
    )
    parser.add_argument(
        "--submission",
        type=Path,
        default=DEFAULT_SUBMISSION_PATH,
        help="September submission CSV to format-check.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="JSON report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = evaluate(args.validation, args.submission, args.report)
    print_report(report)


if __name__ == "__main__":
    main()

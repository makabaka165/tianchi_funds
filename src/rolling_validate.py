from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from baseline_weekday_mean import (
    DAILY_FEATURES_PATH,
    OUTPUT_DIR,
    apply_calibration,
    build_daily_features,
    weekday_window_predict,
)
from evaluate import official_proxy_score, relative_error


DEFAULT_MONTHS = ["2014-05", "2014-06", "2014-07", "2014-08"]
ROLLING_DETAIL_PATH = OUTPUT_DIR / "rolling_validation_2014_05_08.csv"
ROLLING_SUMMARY_PATH = OUTPUT_DIR / "rolling_validation_summary.json"


def load_daily_features(path: Path = DAILY_FEATURES_PATH) -> pd.DataFrame:
    if path.exists():
        features = pd.read_csv(path, parse_dates=["date"])
    else:
        features = build_daily_features()
        OUTPUT_DIR.mkdir(exist_ok=True)
        features.to_csv(path, index=False, encoding="utf-8")
    return features.sort_values("date").reset_index(drop=True)


def evaluate_month(features: pd.DataFrame, month: str) -> pd.DataFrame:
    start = pd.Timestamp(f"{month}-01")
    end = start + pd.offsets.MonthEnd(0)
    train = features[features["date"] < start].copy()
    valid = features[(features["date"] >= start) & (features["date"] <= end)].copy()

    if train.empty or valid.empty:
        raise ValueError(f"Month {month} does not have enough train/validation data")

    valid["validation_month"] = month
    valid["pred_purchase"] = apply_calibration(
        weekday_window_predict(train, valid["date"], "purchase"),
        "purchase",
    )
    valid["pred_redeem"] = apply_calibration(
        weekday_window_predict(train, valid["date"], "redeem"),
        "redeem",
    )
    valid["purchase_relative_error"] = relative_error(
        valid["purchase"], valid["pred_purchase"]
    )
    valid["redeem_relative_error"] = relative_error(
        valid["redeem"], valid["pred_redeem"]
    )
    valid["weighted_relative_error"] = (
        0.45 * valid["purchase_relative_error"]
        + 0.55 * valid["redeem_relative_error"]
    )
    valid["purchase_proxy_score"] = official_proxy_score(
        valid["purchase_relative_error"]
    )
    valid["redeem_proxy_score"] = official_proxy_score(valid["redeem_relative_error"])
    valid["weighted_proxy_score"] = (
        0.45 * valid["purchase_proxy_score"] + 0.55 * valid["redeem_proxy_score"]
    )
    return valid


def summarize(detail: pd.DataFrame) -> dict[str, object]:
    monthly = []
    for month, group in detail.groupby("validation_month", sort=True):
        monthly.append(
            {
                "validation_month": month,
                "days": int(len(group)),
                "purchase_relative_error_mean": float(
                    group["purchase_relative_error"].mean()
                ),
                "redeem_relative_error_mean": float(
                    group["redeem_relative_error"].mean()
                ),
                "weighted_relative_error_mean": float(
                    group["weighted_relative_error"].mean()
                ),
                "weighted_proxy_score_mean": float(
                    group["weighted_proxy_score"].mean()
                ),
                "bad_day_rate_max": float(
                    max(
                        (group["purchase_relative_error"] > 0.3).mean(),
                        (group["redeem_relative_error"] > 0.3).mean(),
                    )
                ),
            }
        )

    return {
        "months": monthly,
        "overall": {
            "days": int(len(detail)),
            "purchase_relative_error_mean": float(
                detail["purchase_relative_error"].mean()
            ),
            "redeem_relative_error_mean": float(detail["redeem_relative_error"].mean()),
            "weighted_relative_error_mean": float(
                detail["weighted_relative_error"].mean()
            ),
            "weighted_proxy_score_mean": float(detail["weighted_proxy_score"].mean()),
            "bad_day_rate_max": float(
                max(
                    (detail["purchase_relative_error"] > 0.3).mean(),
                    (detail["redeem_relative_error"] > 0.3).mean(),
                )
            ),
            "worst_month_by_weighted_error": max(
                monthly, key=lambda item: item["weighted_relative_error_mean"]
            )["validation_month"],
        },
    }


def run_rolling_validation(months: list[str]) -> tuple[pd.DataFrame, dict[str, object]]:
    features = load_daily_features()
    detail = pd.concat(
        [evaluate_month(features, month) for month in months],
        ignore_index=True,
    )
    summary = summarize(detail)

    OUTPUT_DIR.mkdir(exist_ok=True)
    detail.to_csv(ROLLING_DETAIL_PATH, index=False, encoding="utf-8")
    ROLLING_SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return detail, summary


def print_summary(summary: dict[str, object]) -> None:
    print("Rolling validation report")
    print("=========================")
    for month in summary["months"]:
        print(
            "{validation_month}: weighted_error={weighted_relative_error_mean:.6f}, "
            "purchase_error={purchase_relative_error_mean:.6f}, "
            "redeem_error={redeem_relative_error_mean:.6f}, "
            "bad_day_rate={bad_day_rate_max:.6f}, "
            "proxy_score={weighted_proxy_score_mean:.6f}".format(**month)
        )

    overall = summary["overall"]
    print()
    print(
        "Overall: weighted_error={weighted_relative_error_mean:.6f}, "
        "purchase_error={purchase_relative_error_mean:.6f}, "
        "redeem_error={redeem_relative_error_mean:.6f}, "
        "bad_day_rate={bad_day_rate_max:.6f}, "
        "proxy_score={weighted_proxy_score_mean:.6f}".format(**overall)
    )
    print(f"Worst month: {overall['worst_month_by_weighted_error']}")
    print(f"Saved detail: {ROLLING_DETAIL_PATH}")
    print(f"Saved summary: {ROLLING_SUMMARY_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run month-by-month rolling validation for the calibrated baseline."
    )
    parser.add_argument(
        "--months",
        nargs="+",
        default=DEFAULT_MONTHS,
        help="Validation months in YYYY-MM format.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _, summary = run_rolling_validation(args.months)
    print_summary(summary)


if __name__ == "__main__":
    main()

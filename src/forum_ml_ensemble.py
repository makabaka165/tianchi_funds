from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import baseline_weekday_mean as rule_model
from evaluate import official_proxy_score, relative_error


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"

ML_DETAIL_PATH = OUTPUT_DIR / "forum_ml_validation_2014_05_08.csv"
ML_AUGUST_PATH = OUTPUT_DIR / "forum_ml_validation_august_2014.csv"
ML_SUMMARY_PATH = OUTPUT_DIR / "forum_ml_summary.json"
ML_SUBMISSION_PATH = OUTPUT_DIR / "forum_ml_tc_comp_predict_table.csv"

BLEND_DETAIL_PATH = OUTPUT_DIR / "forum_blend_validation_2014_05_08.csv"
BLEND_AUGUST_PATH = OUTPUT_DIR / "forum_blend_validation_august_2014.csv"
BLEND_SUMMARY_PATH = OUTPUT_DIR / "forum_blend_summary.json"
BLEND_SUBMISSION_PATH = OUTPUT_DIR / "forum_blend_tc_comp_predict_table.csv"
BLEND_WEIGHT_SCAN_PATH = OUTPUT_DIR / "forum_blend_weight_scan.csv"

MODEL_REPORT_PATH = OUTPUT_DIR / "forum_ml_model_report.json"
FINAL_SUBMISSION_PATH = OUTPUT_DIR / "tc_comp_predict_table.csv"

VALIDATION_MONTHS = ["2014-05", "2014-06", "2014-07", "2014-08"]
TARGETS = ["purchase", "redeem"]
LAGS = [1, 2, 3, 7, 14, 21, 28]
ROLLING_WINDOWS = [7, 14, 28]
MODEL_MIN_PROXY_SCORE = 3.0
MODEL_MAX_BAD_DAY_RATE = 0.38
RECENT_7_FILL_COLUMNS = [
    "mfd_daily_yield",
    "mfd_7daily_yield",
    "Interest_O_N",
    "Interest_1_W",
    "Interest_2_W",
    "Interest_1_M",
    "Interest_3_M",
    "Interest_6_M",
    "Interest_9_M",
    "Interest_1_Y",
]
DROP_MODEL_COLUMNS = {
    "date",
    "report_date",
    "purchase",
    "redeem",
    "total_purchase_amt",
    "total_redeem_amt",
    "tBalance",
    "yBalance",
    "direct_purchase_amt",
    "purchase_bal_amt",
    "purchase_bank_amt",
    "consume_amt",
    "transfer_amt",
    "tftobal_amt",
    "tftocard_amt",
    "share_amt",
    "category1",
    "category2",
    "category3",
    "category4",
    "active_users",
    "purchase_users",
    "redeem_users",
    "avg_purchase_per_user",
    "avg_redeem_per_user",
}


@dataclass(frozen=True)
class CandidateResult:
    name: str
    detail: pd.DataFrame
    summary: dict[str, object]
    august_detail: pd.DataFrame
    submission: pd.DataFrame


def clean_prediction_series(
    values: pd.Series,
    fallback: pd.Series | None = None,
) -> pd.Series:
    result = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)
    if fallback is not None:
        fallback_values = pd.to_numeric(fallback, errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
        result = result.fillna(fallback_values)
    return result.fillna(0).round().clip(lower=0).astype("int64")


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)


def load_features() -> pd.DataFrame:
    features = rule_model.build_daily_features()
    return features.sort_values("date").reset_index(drop=True)


def add_static_calendar(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    date = result["date"]
    result["weekday"] = date.dt.weekday
    result["day"] = date.dt.day
    result["month"] = date.dt.month
    result["is_weekend"] = result["weekday"].isin([5, 6]).astype(int)
    result["is_month_start"] = date.dt.is_month_start.astype(int)
    result["is_month_end"] = date.dt.is_month_end.astype(int)
    result["days_to_month_end"] = (date.dt.days_in_month - date.dt.day).astype(int)
    result["is_holiday"] = date.dt.strftime("%Y-%m-%d").isin(rule_model.HOLIDAY_DATES).astype(int)
    result["is_post_holiday"] = (
        (date - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d").isin(rule_model.HOLIDAY_DATES)
    ).astype(int)
    return result


def fill_future_external_features(frame: pd.DataFrame, history_end: pd.Timestamp) -> pd.DataFrame:
    result = frame.copy()
    recent = result[result["date"] <= history_end].tail(7)
    for column in RECENT_7_FILL_COLUMNS:
        if column in result.columns:
            fill_value = float(recent[column].mean())
            result[column] = result[column].fillna(fill_value)
    return result


def add_time_series_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = add_static_calendar(frame).sort_values("date").reset_index(drop=True)
    for column in result.columns:
        if column != "date":
            result[column] = pd.to_numeric(result[column], errors="coerce")

    for target in TARGETS:
        for lag in LAGS:
            result[f"{target}_lag_{lag}"] = result[target].shift(lag)

        shifted = result[target].shift(1)
        for window in ROLLING_WINDOWS:
            rolling = shifted.rolling(window=window, min_periods=max(3, window // 2))
            result[f"{target}_roll_mean_{window}"] = rolling.mean()
            result[f"{target}_roll_median_{window}"] = rolling.median()
            result[f"{target}_roll_std_{window}"] = rolling.std()
            result[f"{target}_roll_min_{window}"] = rolling.min()
            result[f"{target}_roll_max_{window}"] = rolling.max()
            result[f"{target}_trend_ratio_{window}"] = result[f"{target}_lag_1"] / (
                result[f"{target}_roll_mean_{window}"] + 1
            )

        result[f"{target}_weekday_mean_8"] = (
            result.groupby("weekday")[target]
            .shift(1)
            .rolling(window=8, min_periods=2)
            .mean()
            .reset_index(level=0, drop=True)
        )
        result[f"{target}_weekday_median_8"] = (
            result.groupby("weekday")[target]
            .shift(1)
            .rolling(window=8, min_periods=2)
            .median()
            .reset_index(level=0, drop=True)
        )

    result["purchase_redeem_lag1_ratio"] = result["purchase_lag_1"] / (
        result["redeem_lag_1"] + 1
    )
    result["redeem_purchase_lag1_ratio"] = result["redeem_lag_1"] / (
        result["purchase_lag_1"] + 1
    )

    numeric_cols = result.select_dtypes(include=[np.number]).columns
    result[numeric_cols] = result[numeric_cols].replace([np.inf, -np.inf], np.nan)
    result[numeric_cols] = result[numeric_cols].ffill().bfill().fillna(0)
    return result


def feature_columns(model_frame: pd.DataFrame) -> list[str]:
    columns = [
        column
        for column in model_frame.columns
        if column not in DROP_MODEL_COLUMNS and pd.api.types.is_numeric_dtype(model_frame[column])
    ]
    return sorted(columns)


def make_model(kind: str):
    if kind == "lgb":
        return lgb.LGBMRegressor(
            objective="regression_l1",
            n_estimators=220,
            learning_rate=0.035,
            num_leaves=15,
            max_depth=4,
            min_child_samples=12,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.15,
            reg_lambda=1.2,
            random_state=2026,
            verbosity=-1,
        )
    if kind == "xgb":
        return xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=220,
            learning_rate=0.035,
            max_depth=3,
            min_child_weight=3,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.05,
            reg_lambda=1.2,
            random_state=2026,
            n_jobs=1,
        )
    if kind == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=8.0))
    raise ValueError(f"Unknown model kind: {kind}")


def fit_target_models(
    train_frame: pd.DataFrame,
    target: str,
    columns: list[str],
    kinds: list[str],
) -> dict[str, object]:
    x_train = train_frame[columns]
    y_train = np.log1p(train_frame[target].clip(lower=0))
    models = {}
    for kind in kinds:
        model = make_model(kind)
        model.fit(x_train, y_train)
        models[kind] = model
    return models


def predict_one_day(
    history_future: pd.DataFrame,
    date: pd.Timestamp,
    columns: list[str],
    fitted: dict[str, dict[str, object]],
    kinds: list[str],
) -> dict[str, dict[str, float]]:
    features = add_time_series_features(history_future)
    row = features[features["date"] == date].iloc[-1]
    x_row = row[columns].to_frame().T.astype(float)
    predictions: dict[str, dict[str, float]] = {}
    for target in TARGETS:
        predictions[target] = {}
        for kind in kinds:
            raw_log = float(fitted[target][kind].predict(x_row)[0])
            raw_log = float(np.clip(raw_log, 0.0, 23.0))
            value = float(np.expm1(raw_log))
            predictions[target][kind] = max(0.0, value)
    return predictions


def recursive_predict(
    train_history: pd.DataFrame,
    predict_dates: pd.Series,
    kinds: list[str],
    feedback_weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    history_end = pd.Timestamp(train_history["date"].max())
    future = pd.DataFrame({"date": pd.to_datetime(predict_dates)})
    future["report_date"] = future["date"].dt.strftime("%Y%m%d").astype(int)
    for target in TARGETS:
        future[target] = np.nan
    future = add_static_calendar(future)

    for column in train_history.columns:
        if column not in future.columns:
            future[column] = np.nan

    combined = pd.concat([train_history, future[train_history.columns]], ignore_index=True)
    combined = fill_future_external_features(combined, history_end)
    model_frame = add_time_series_features(train_history)
    columns = feature_columns(model_frame)

    fitted = {
        target: fit_target_models(model_frame, target, columns, kinds)
        for target in TARGETS
    }
    if feedback_weights is None:
        feedback_weights = {kind: 1 / len(kinds) for kind in kinds}
    feedback_total = sum(feedback_weights.get(kind, 0.0) for kind in kinds)
    if feedback_total <= 0:
        feedback_weights = {kind: 1 / len(kinds) for kind in kinds}
    else:
        feedback_weights = {
            kind: feedback_weights.get(kind, 0.0) / feedback_total for kind in kinds
        }

    rows = []
    for date in pd.to_datetime(predict_dates):
        preds = predict_one_day(combined, date, columns, fitted, kinds)
        row = {"date": date, "report_date": int(date.strftime("%Y%m%d"))}
        for kind in kinds:
            row[f"pred_purchase_{kind}"] = preds["purchase"][kind]
            row[f"pred_redeem_{kind}"] = preds["redeem"][kind]

        combined.loc[combined["date"] == date, "purchase"] = sum(
            feedback_weights[kind] * preds["purchase"][kind] for kind in kinds
        )
        combined.loc[combined["date"] == date, "redeem"] = sum(
            feedback_weights[kind] * preds["redeem"][kind] for kind in kinds
        )
        rows.append(row)

    return pd.DataFrame(rows)


def score_detail(detail: pd.DataFrame) -> pd.DataFrame:
    result = detail.copy()
    result["purchase_relative_error"] = relative_error(result["purchase"], result["pred_purchase"])
    result["redeem_relative_error"] = relative_error(result["redeem"], result["pred_redeem"])
    result["weighted_relative_error"] = (
        0.45 * result["purchase_relative_error"] + 0.55 * result["redeem_relative_error"]
    )
    result["purchase_proxy_score"] = official_proxy_score(result["purchase_relative_error"])
    result["redeem_proxy_score"] = official_proxy_score(result["redeem_relative_error"])
    result["weighted_proxy_score"] = (
        0.45 * result["purchase_proxy_score"] + 0.55 * result["redeem_proxy_score"]
    )
    return result


def summarize_detail(detail: pd.DataFrame) -> dict[str, object]:
    scored = score_detail(detail)
    monthly = []
    for month, group in scored.groupby("validation_month", sort=True):
        monthly.append(
            {
                "validation_month": month,
                "days": int(len(group)),
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
        )

    return {
        "months": monthly,
        "overall": {
            "days": int(len(scored)),
            "purchase_relative_error_mean": float(scored["purchase_relative_error"].mean()),
            "redeem_relative_error_mean": float(scored["redeem_relative_error"].mean()),
            "weighted_relative_error_mean": float(scored["weighted_relative_error"].mean()),
            "weighted_proxy_score_mean": float(scored["weighted_proxy_score"].mean()),
            "bad_day_rate_max": float(
                max(
                    (scored["purchase_relative_error"] > 0.3).mean(),
                    (scored["redeem_relative_error"] > 0.3).mean(),
                )
            ),
            "worst_month_by_weighted_error": max(
                monthly, key=lambda item: item["weighted_relative_error_mean"]
            )["validation_month"],
        },
    }


def evaluate_kind(
    features: pd.DataFrame,
    month: str,
    kind: str,
    kinds: list[str],
) -> pd.DataFrame:
    start = pd.Timestamp(f"{month}-01")
    end = start + pd.offsets.MonthEnd(0)
    train = features[features["date"] < start].copy()
    valid = features[(features["date"] >= start) & (features["date"] <= end)].copy()
    predictions = recursive_predict(
        train,
        valid["date"],
        kinds,
        feedback_weights={item: 1.0 if item == kind else 0.0 for item in kinds},
    )

    result = valid[
        [
            "date",
            "report_date",
            "purchase",
            "redeem",
        ]
    ].copy()
    result = result.reset_index(drop=True)
    result["validation_month"] = month
    result["pred_purchase"] = (
        predictions[f"pred_purchase_{kind}"]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
        .round()
        .clip(lower=0)
        .astype("int64")
    )
    result["pred_redeem"] = (
        predictions[f"pred_redeem_{kind}"]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
        .round()
        .clip(lower=0)
        .astype("int64")
    )
    return result


def evaluate_ml_ensemble(
    features: pd.DataFrame,
    month: str,
    kinds: list[str],
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    start = pd.Timestamp(f"{month}-01")
    end = start + pd.offsets.MonthEnd(0)
    train = features[features["date"] < start].copy()
    valid = features[(features["date"] >= start) & (features["date"] <= end)].copy()
    predictions = recursive_predict(train, valid["date"], kinds, feedback_weights=weights)

    if weights is None:
        weights = {kind: 1 / len(kinds) for kind in kinds}

    result = valid[["date", "report_date", "purchase", "redeem"]].copy()
    result = result.reset_index(drop=True)
    result["validation_month"] = month
    for target in TARGETS:
        pred = sum(
            weights[kind] * predictions[f"pred_{target}_{kind}"] for kind in kinds
        )
        result[f"pred_{target}"] = clean_prediction_series(pred)
    return result


def evaluate_rule_model(features: pd.DataFrame, month: str) -> pd.DataFrame:
    start = pd.Timestamp(f"{month}-01")
    end = start + pd.offsets.MonthEnd(0)
    train = features[features["date"] < start].copy()
    valid = features[(features["date"] >= start) & (features["date"] <= end)].copy()
    result = valid[["date", "report_date", "purchase", "redeem"]].copy()
    result = result.reset_index(drop=True)
    result["validation_month"] = month
    result["pred_purchase"] = rule_model.predict_target(
        train,
        valid["date"],
        "purchase",
    ).reset_index(drop=True)
    result["pred_redeem"] = rule_model.predict_target(
        train,
        valid["date"],
        "redeem",
    ).reset_index(drop=True)
    return result


def evaluate_conservative_blend(
    features: pd.DataFrame,
    month: str,
    kinds: list[str],
    ml_weights: dict[str, float],
    rule_weight: float = 0.5,
) -> pd.DataFrame:
    ml = evaluate_ml_ensemble(features, month, kinds, ml_weights)
    rule = evaluate_rule_model(features, month)
    result = ml.copy()
    rule_purchase = rule["pred_purchase"].reset_index(drop=True).astype(float)
    rule_redeem = rule["pred_redeem"].reset_index(drop=True).astype(float)
    ml_purchase = ml["pred_purchase"].reset_index(drop=True).astype(float)
    ml_redeem = ml["pred_redeem"].reset_index(drop=True).astype(float)
    ml_weight = 1 - rule_weight
    result["pred_purchase"] = clean_prediction_series(
        rule_weight * rule_purchase + ml_weight * ml_purchase,
        fallback=rule_purchase,
    )
    result["pred_redeem"] = clean_prediction_series(
        rule_weight * rule_redeem + ml_weight * ml_redeem,
        fallback=rule_redeem,
    )
    return result


def model_weights(
    model_summaries: dict[str, dict[str, object]],
) -> tuple[dict[str, float], list[str]]:
    eligible: dict[str, float] = {}
    for kind, summary in model_summaries.items():
        overall = summary["overall"]
        proxy_score = float(overall["weighted_proxy_score_mean"])
        bad_day_rate = float(overall["bad_day_rate_max"])
        if proxy_score >= MODEL_MIN_PROXY_SCORE and bad_day_rate <= MODEL_MAX_BAD_DAY_RATE:
            eligible[kind] = max(0.0, proxy_score)

    raw_scores = eligible or {
        kind: max(0.0, float(summary["overall"]["weighted_proxy_score_mean"]))
        for kind, summary in model_summaries.items()
    }
    total = sum(raw_scores.values())
    if total <= 0:
        return {kind: 1 / len(raw_scores) for kind in raw_scores}, list(raw_scores)
    return {kind: score / total for kind, score in raw_scores.items()}, list(raw_scores)


def make_submission(
    features: pd.DataFrame,
    kinds: list[str],
    weights: dict[str, float],
    include_rule_blend: bool,
) -> pd.DataFrame:
    history = features[features["date"] <= "2014-08-31"].copy()
    dates = pd.Series(pd.date_range("2014-09-01", "2014-09-30"))
    predictions = recursive_predict(history, dates, kinds, feedback_weights=weights)

    result = predictions[["report_date"]].copy()
    for target in TARGETS:
        pred = sum(
            weights[kind] * predictions[f"pred_{target}_{kind}"] for kind in kinds
        )
        result[target] = pred

    if include_rule_blend:
        rule_submission = rule_model.predict_september(features)
        for target in TARGETS:
            result[target] = 0.5 * rule_submission[target].astype(float) + 0.5 * result[target]

    for target in TARGETS:
        fallback = None
        if include_rule_blend:
            fallback = rule_submission[target].astype(float)
        result[target] = clean_prediction_series(result[target], fallback=fallback)
    return result[["report_date", "purchase", "redeem"]]


def save_candidate(result: CandidateResult, detail_path: Path, august_path: Path, summary_path: Path, submission_path: Path) -> None:
    result.detail.to_csv(detail_path, index=False, encoding="utf-8")
    result.august_detail.to_csv(august_path, index=False, encoding="utf-8")
    summary_path.write_text(
        json.dumps(result.summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    result.submission.to_csv(submission_path, index=False, header=False, encoding="utf-8")


def scan_rule_ml_blend_weights(
    features: pd.DataFrame,
    kinds: list[str],
    weights: dict[str, float],
    rule_weights: list[float] | None = None,
) -> pd.DataFrame:
    rule_weights = rule_weights or [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95]
    cached_months = {
        month: {
            "ml": evaluate_ml_ensemble(features, month, kinds, weights),
            "rule": evaluate_rule_model(features, month),
        }
        for month in VALIDATION_MONTHS
    }
    rows = []
    for rule_weight in rule_weights:
        month_details = []
        for cached in cached_months.values():
            ml = cached["ml"]
            rule = cached["rule"]
            result = ml.copy()
            ml_weight = 1 - rule_weight
            for target in TARGETS:
                result[f"pred_{target}"] = clean_prediction_series(
                    rule_weight
                    * rule[f"pred_{target}"].reset_index(drop=True).astype(float)
                    + ml_weight
                    * ml[f"pred_{target}"].reset_index(drop=True).astype(float),
                    fallback=rule[f"pred_{target}"].reset_index(drop=True).astype(float),
                )
            month_details.append(result)

        detail = pd.concat(month_details, ignore_index=True)
        summary = summarize_detail(score_detail(detail))
        overall = summary["overall"]
        row = {
            "rule_weight": float(rule_weight),
            "ml_weight": float(1 - rule_weight),
            "overall_weighted_proxy_score_mean": overall[
                "weighted_proxy_score_mean"
            ],
            "overall_weighted_relative_error_mean": overall[
                "weighted_relative_error_mean"
            ],
            "overall_bad_day_rate_max": overall["bad_day_rate_max"],
        }
        for month in summary["months"]:
            prefix = month["validation_month"]
            row[f"{prefix}_weighted_proxy_score_mean"] = month[
                "weighted_proxy_score_mean"
            ]
            row[f"{prefix}_bad_day_rate_max"] = month["bad_day_rate_max"]
        rows.append(row)
    return pd.DataFrame(rows)


def build_candidate(
    name: str,
    detail_factory: Callable[[str], pd.DataFrame],
    features: pd.DataFrame,
    submission_factory: Callable[[], pd.DataFrame],
) -> CandidateResult:
    detail = pd.concat(
        [detail_factory(month) for month in VALIDATION_MONTHS],
        ignore_index=True,
    )
    scored_detail = score_detail(detail)
    summary = summarize_detail(scored_detail)
    august_detail = scored_detail[scored_detail["validation_month"] == "2014-08"].copy()
    submission = submission_factory()
    return CandidateResult(
        name=name,
        detail=scored_detail,
        summary=summary,
        august_detail=august_detail,
        submission=submission,
    )


def print_summary(name: str, summary: dict[str, object]) -> None:
    overall = summary["overall"]
    print(
        f"{name}: overall_proxy={overall['weighted_proxy_score_mean']:.6f}, "
        f"weighted_error={overall['weighted_relative_error_mean']:.6f}, "
        f"bad_day_rate={overall['bad_day_rate_max']:.6f}"
    )
    for month in summary["months"]:
        print(
            "  {validation_month}: proxy={weighted_proxy_score_mean:.6f}, "
            "error={weighted_relative_error_mean:.6f}, "
            "bad_day={bad_day_rate_max:.6f}".format(**month)
        )


def main() -> None:
    ensure_output_dir()
    features = load_features()
    kinds = ["lgb", "xgb", "ridge"]

    single_results: dict[str, CandidateResult] = {}
    single_summaries: dict[str, dict[str, object]] = {}
    for kind in kinds:
        result = build_candidate(
            name=kind,
            detail_factory=lambda month, kind=kind: evaluate_kind(features, month, kind, kinds),
            features=features,
            submission_factory=lambda kind=kind: make_submission(
                features,
                kinds,
                {k: 1.0 if k == kind else 0.0 for k in kinds},
                include_rule_blend=False,
            ),
        )
        single_results[kind] = result
        single_summaries[kind] = result.summary
        print_summary(kind, result.summary)

    weights, weighted_kinds = model_weights(single_summaries)
    print(f"ML ensemble weights: {weights}")
    ml_result = build_candidate(
        name="ml_weighted",
        detail_factory=lambda month: evaluate_ml_ensemble(features, month, weighted_kinds, weights),
        features=features,
        submission_factory=lambda: make_submission(
            features,
            weighted_kinds,
            weights,
            include_rule_blend=False,
        ),
    )
    print_summary("ml_weighted", ml_result.summary)

    blend_result = build_candidate(
        name="rule_ml_50_50",
        detail_factory=lambda month: evaluate_conservative_blend(
            features,
            month,
            weighted_kinds,
            weights,
        ),
        features=features,
        submission_factory=lambda: make_submission(
            features,
            weighted_kinds,
            weights,
            include_rule_blend=True,
        ),
    )
    print_summary("rule_ml_50_50", blend_result.summary)

    blend_weight_scan = scan_rule_ml_blend_weights(features, weighted_kinds, weights)
    blend_weight_scan.to_csv(BLEND_WEIGHT_SCAN_PATH, index=False, encoding="utf-8")
    best_scan = blend_weight_scan.sort_values(
        "overall_weighted_proxy_score_mean",
        ascending=False,
    ).iloc[0]
    print(
        "best_rule_ml_weight_scan: "
        f"rule_weight={best_scan['rule_weight']:.2f}, "
        f"overall_proxy={best_scan['overall_weighted_proxy_score_mean']:.6f}, "
        f"bad_day_rate={best_scan['overall_bad_day_rate_max']:.6f}"
    )

    save_candidate(
        ml_result,
        ML_DETAIL_PATH,
        ML_AUGUST_PATH,
        ML_SUMMARY_PATH,
        ML_SUBMISSION_PATH,
    )
    save_candidate(
        blend_result,
        BLEND_DETAIL_PATH,
        BLEND_AUGUST_PATH,
        BLEND_SUMMARY_PATH,
        BLEND_SUBMISSION_PATH,
    )

    report = {
        "single_model_summaries": single_summaries,
        "ml_weights": weights,
        "weighted_model_kinds": weighted_kinds,
        "weight_filter": {
            "min_proxy_score": MODEL_MIN_PROXY_SCORE,
            "max_bad_day_rate": MODEL_MAX_BAD_DAY_RATE,
        },
        "ml_weighted_summary": ml_result.summary,
        "rule_ml_50_50_summary": blend_result.summary,
        "outputs": {
            "ml_detail": str(ML_DETAIL_PATH),
            "ml_august": str(ML_AUGUST_PATH),
            "ml_submission": str(ML_SUBMISSION_PATH),
            "blend_detail": str(BLEND_DETAIL_PATH),
            "blend_august": str(BLEND_AUGUST_PATH),
            "blend_submission": str(BLEND_SUBMISSION_PATH),
            "blend_weight_scan": str(BLEND_WEIGHT_SCAN_PATH),
        },
    }
    MODEL_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved model report: {MODEL_REPORT_PATH}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

import baseline_weekday_mean as rule_model
from evaluate import (
    decide_candidate,
    official_proxy_score,
    relative_error,
    weighted_stats,
)
from rolling_validate import DEFAULT_MONTHS, evaluate_month, load_daily_features


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
OFFICIAL_SUBMISSION_PATH = OUTPUT_DIR / "tc_comp_predict_table.csv"
OFFICIAL_VALIDATION_PATH = OUTPUT_DIR / "validation_august_2014.csv"
OFFICIAL_ROLLING_SUMMARY_PATH = OUTPUT_DIR / "rolling_validation_summary.json"

LSTM_COMBINED_DETAIL_PATH = OUTPUT_DIR / "lstm_validation_2014_05_08.csv"
LSTM_COMBINED_AUGUST_PATH = OUTPUT_DIR / "lstm_validation_august_2014.csv"
LSTM_SUMMARY_CSV_PATH = OUTPUT_DIR / "lstm_experiment_summary.csv"
LSTM_SUMMARY_JSON_PATH = OUTPUT_DIR / "lstm_experiment_summary.json"
LSTM_SELECTION_PATH = OUTPUT_DIR / "lstm_best_experiment.json"
LSTM_BEST_PURE_VALIDATION_PATH = OUTPUT_DIR / "lstm_best_pure_validation_august_2014.csv"
LSTM_BEST_PURE_SUBMISSION_PATH = OUTPUT_DIR / "lstm_best_pure_tc_comp_predict_table.csv"
LSTM_BEST_BLEND_VALIDATION_PATH = OUTPUT_DIR / "lstm_best_blend_validation_august_2014.csv"
LSTM_BEST_BLEND_SUBMISSION_PATH = OUTPUT_DIR / "lstm_best_blend_tc_comp_predict_table.csv"

TARGETS = ["purchase", "redeem"]
HORIZON = 31
SEED = 2026
BATCH_SIZE = 16
PATIENCE = 20
VAL_SPLIT = 0.15
PURCHASE_EPOCHS = 150
REDEEM_EPOCHS = 230
BASELINE_OVERALL_PROXY = 6.075524
BASELINE_BAD_DAY_RATE = 0.203252
BLEND_RULE_WEIGHTS = [0.95, 0.90, 0.85, 0.80]


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    look_back: int
    ema_span: int


@dataclass
class TargetArtifacts:
    model: object
    feature_scaler: MinMaxScaler
    target_scaler: MinMaxScaler


EXPERIMENT_SPECS = [
    ExperimentSpec(name="pure_base", look_back=40, ema_span=3),
    ExperimentSpec(name="pure_lb30", look_back=30, ema_span=3),
    ExperimentSpec(name="pure_lb60", look_back=60, ema_span=3),
    ExperimentSpec(name="pure_ema5", look_back=40, ema_span=5),
]


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)


def set_global_seed() -> None:
    import tensorflow as tf

    np.random.seed(SEED)
    tf.keras.utils.set_random_seed(SEED)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass


def build_model(look_back: int, feature_count: int) -> object:
    import tensorflow as tf

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(look_back, feature_count)),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(HORIZON),
        ]
    )
    model.compile(loss="mse", optimizer="adam")
    return model


def build_target_frame(
    features: pd.DataFrame,
    target: str,
    ema_span: int,
) -> pd.DataFrame:
    frame = features[["date", target]].copy()
    frame = frame.rename(columns={target: "y_raw"})
    frame["y_log"] = np.log1p(frame["y_raw"].astype(float))
    frame["y_ema"] = frame["y_log"].ewm(span=ema_span, adjust=False).mean()
    return frame


def make_supervised_arrays(
    feature_values: np.ndarray,
    target_values: np.ndarray,
    look_back: int,
) -> tuple[np.ndarray, np.ndarray]:
    windows_x: list[np.ndarray] = []
    windows_y: list[np.ndarray] = []
    max_start = len(feature_values) - look_back - HORIZON + 1
    for start in range(max_start):
        end = start + look_back
        future_end = end + HORIZON
        windows_x.append(feature_values[start:end])
        windows_y.append(target_values[end:future_end, 0])

    if not windows_x:
        raise ValueError(
            f"Not enough rows for look_back={look_back} and horizon={HORIZON}"
        )
    return np.array(windows_x, dtype=np.float32), np.array(windows_y, dtype=np.float32)


def split_train_validation(
    x_values: np.ndarray,
    y_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    val_size = int(np.ceil(len(x_values) * VAL_SPLIT))
    val_size = min(max(1, val_size), len(x_values) - 1)
    train_size = len(x_values) - val_size
    return (
        x_values[:train_size],
        y_values[:train_size],
        x_values[train_size:],
        y_values[train_size:],
    )


def fit_target_model(
    target_frame: pd.DataFrame,
    train_end_exclusive: pd.Timestamp,
    look_back: int,
    epochs: int,
) -> TargetArtifacts:
    import tensorflow as tf

    history = target_frame[target_frame["date"] < train_end_exclusive].copy()
    if len(history) < look_back + HORIZON + 8:
        raise ValueError(
            f"Insufficient history rows for {train_end_exclusive.date()}: {len(history)}"
        )

    feature_scaler = MinMaxScaler()
    target_scaler = MinMaxScaler()

    feature_values = feature_scaler.fit_transform(
        history[["y_log", "y_ema"]].to_numpy(dtype=np.float32)
    ).astype(np.float32)
    target_values = target_scaler.fit_transform(
        history[["y_log"]].to_numpy(dtype=np.float32)
    ).astype(np.float32)

    x_all, y_all = make_supervised_arrays(feature_values, target_values, look_back)
    x_train, y_train, x_val, y_val = split_train_validation(x_all, y_all)

    tf.keras.backend.clear_session()
    model = build_model(look_back=look_back, feature_count=feature_values.shape[1])
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=PATIENCE,
            restore_best_weights=True,
        )
    ]
    model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=epochs,
        batch_size=BATCH_SIZE,
        shuffle=False,
        verbose=0,
        callbacks=callbacks,
    )
    return TargetArtifacts(
        model=model,
        feature_scaler=feature_scaler,
        target_scaler=target_scaler,
    )


def predict_target_horizon(
    target_frame: pd.DataFrame,
    train_end_exclusive: pd.Timestamp,
    artifacts: TargetArtifacts,
    look_back: int,
    predict_days: int,
) -> pd.Series:
    history = target_frame[target_frame["date"] < train_end_exclusive].copy()
    window = history[["y_log", "y_ema"]].tail(look_back).to_numpy(dtype=np.float32)
    if len(window) != look_back:
        raise ValueError(
            f"Expected {look_back} rows in prediction window, got {len(window)}"
        )

    scaled_window = artifacts.feature_scaler.transform(window).astype(np.float32)
    scaled_pred = artifacts.model.predict(
        scaled_window.reshape(1, look_back, 2),
        verbose=0,
    )[0]
    pred_log = artifacts.target_scaler.inverse_transform(
        scaled_pred.reshape(-1, 1)
    ).reshape(-1)
    pred_raw = np.expm1(pred_log)
    clipped = np.clip(np.round(pred_raw[:predict_days]), a_min=0, a_max=None)
    return pd.Series(clipped.astype("int64"))


def score_detail(detail: pd.DataFrame) -> pd.DataFrame:
    result = detail.copy()
    result["purchase_relative_error"] = relative_error(
        result["purchase"], result["pred_purchase"]
    )
    result["redeem_relative_error"] = relative_error(
        result["redeem"], result["pred_redeem"]
    )
    result["weighted_relative_error"] = (
        0.45 * result["purchase_relative_error"]
        + 0.55 * result["redeem_relative_error"]
    )
    result["purchase_proxy_score"] = official_proxy_score(
        result["purchase_relative_error"]
    )
    result["redeem_proxy_score"] = official_proxy_score(result["redeem_relative_error"])
    result["weighted_proxy_score"] = (
        0.45 * result["purchase_proxy_score"] + 0.55 * result["redeem_proxy_score"]
    )
    return result


def summarize_detail(detail: pd.DataFrame) -> dict[str, object]:
    scored = score_detail(detail)
    monthly: list[dict[str, object]] = []
    for month, group in scored.groupby("validation_month", sort=True):
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
            "days": int(len(scored)),
            "purchase_relative_error_mean": float(
                scored["purchase_relative_error"].mean()
            ),
            "redeem_relative_error_mean": float(scored["redeem_relative_error"].mean()),
            "weighted_relative_error_mean": float(
                scored["weighted_relative_error"].mean()
            ),
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


def summary_row(
    experiment_name: str,
    experiment_type: str,
    summary: dict[str, object],
    submission_issues: list[str],
    august_gate_pass: bool,
    look_back: int | None = None,
    ema_span: int | None = None,
    rule_weight: float | None = None,
    lstm_weight: float | None = None,
    source_pure: str | None = None,
) -> dict[str, object]:
    overall = summary["overall"]
    august = next(
        month for month in summary["months"] if month["validation_month"] == "2014-08"
    )
    row: dict[str, object] = {
        "experiment_name": experiment_name,
        "experiment_type": experiment_type,
        "look_back": look_back,
        "ema_span": ema_span,
        "rule_weight": rule_weight,
        "lstm_weight": lstm_weight,
        "source_pure": source_pure,
        "august_gate_pass": august_gate_pass,
        "submission_issue_count": len(submission_issues),
        "submission_issues": " | ".join(submission_issues),
        "overall_weighted_relative_error_mean": overall["weighted_relative_error_mean"],
        "overall_weighted_proxy_score_mean": overall["weighted_proxy_score_mean"],
        "overall_bad_day_rate_max": overall["bad_day_rate_max"],
        "overall_worst_month_by_weighted_error": overall["worst_month_by_weighted_error"],
        "august_weighted_relative_error_mean": august["weighted_relative_error_mean"],
        "august_weighted_proxy_score_mean": august["weighted_proxy_score_mean"],
        "august_bad_day_rate_max": august["bad_day_rate_max"],
    }
    for month in summary["months"]:
        prefix = month["validation_month"]
        row[f"{prefix}_weighted_relative_error_mean"] = month[
            "weighted_relative_error_mean"
        ]
        row[f"{prefix}_weighted_proxy_score_mean"] = month["weighted_proxy_score_mean"]
        row[f"{prefix}_bad_day_rate_max"] = month["bad_day_rate_max"]
    return row


def submission_issues_from_frame(submission: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    if submission.shape != (30, 3):
        issues.append(f"submission shape should be (30, 3), got {submission.shape}")
        return issues

    frame = submission.copy()
    frame.columns = ["report_date", "purchase", "redeem"]
    expected_dates = pd.date_range("2014-09-01", "2014-09-30").strftime("%Y%m%d")
    actual_dates = frame["report_date"].astype(str).tolist()
    if actual_dates != expected_dates.tolist():
        issues.append("submission dates are not exactly 20140901-20140930")

    for column in ["purchase", "redeem"]:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        if numeric.isna().any():
            issues.append(f"{column} contains non-numeric values")
        if (numeric < 0).any():
            issues.append(f"{column} contains negative values")
        if not np.all(np.equal(np.mod(numeric, 1), 0)):
            issues.append(f"{column} contains non-integer values")
    return issues


def evaluate_august_gate(
    august_detail: pd.DataFrame,
    submission: pd.DataFrame,
) -> tuple[bool, list[str], dict[str, float]]:
    stats = weighted_stats(august_detail)
    submission_issues = submission_issues_from_frame(submission)
    is_candidate, failures = decide_candidate(stats, submission_issues)
    return is_candidate, failures, stats


def rule_baseline_summary(features: pd.DataFrame) -> dict[str, object]:
    if OFFICIAL_ROLLING_SUMMARY_PATH.exists():
        return json.loads(OFFICIAL_ROLLING_SUMMARY_PATH.read_text(encoding="utf-8"))

    detail = pd.concat(
        [evaluate_month(features, month) for month in DEFAULT_MONTHS],
        ignore_index=True,
    )
    return summarize_detail(detail)


def pure_experiment_detail(
    features: pd.DataFrame,
    spec: ExperimentSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    purchase_frame = build_target_frame(features, target="purchase", ema_span=spec.ema_span)
    redeem_frame = build_target_frame(features, target="redeem", ema_span=spec.ema_span)

    monthly_details: list[pd.DataFrame] = []
    for month in DEFAULT_MONTHS:
        start = pd.Timestamp(f"{month}-01")
        end = start + pd.offsets.MonthEnd(0)
        valid = features[(features["date"] >= start) & (features["date"] <= end)].copy()

        purchase_model = fit_target_model(
            purchase_frame,
            train_end_exclusive=start,
            look_back=spec.look_back,
            epochs=PURCHASE_EPOCHS,
        )
        redeem_model = fit_target_model(
            redeem_frame,
            train_end_exclusive=start,
            look_back=spec.look_back,
            epochs=REDEEM_EPOCHS,
        )

        monthly = valid[["date", "report_date", "purchase", "redeem"]].copy()
        monthly["validation_month"] = month
        monthly["pred_purchase"] = predict_target_horizon(
            purchase_frame,
            train_end_exclusive=start,
            artifacts=purchase_model,
            look_back=spec.look_back,
            predict_days=len(valid),
        ).to_numpy()
        monthly["pred_redeem"] = predict_target_horizon(
            redeem_frame,
            train_end_exclusive=start,
            artifacts=redeem_model,
            look_back=spec.look_back,
            predict_days=len(valid),
        ).to_numpy()
        monthly_details.append(monthly.reset_index(drop=True))

    september_start = pd.Timestamp("2014-09-01")
    september_dates = pd.date_range("2014-09-01", "2014-09-30")
    purchase_model = fit_target_model(
        purchase_frame,
        train_end_exclusive=september_start,
        look_back=spec.look_back,
        epochs=PURCHASE_EPOCHS,
    )
    redeem_model = fit_target_model(
        redeem_frame,
        train_end_exclusive=september_start,
        look_back=spec.look_back,
        epochs=REDEEM_EPOCHS,
    )
    submission = pd.DataFrame(
        {
            "report_date": september_dates.strftime("%Y%m%d").astype(int),
            "purchase": predict_target_horizon(
                purchase_frame,
                train_end_exclusive=september_start,
                artifacts=purchase_model,
                look_back=spec.look_back,
                predict_days=30,
            ).to_numpy(),
            "redeem": predict_target_horizon(
                redeem_frame,
                train_end_exclusive=september_start,
                artifacts=redeem_model,
                look_back=spec.look_back,
                predict_days=30,
            ).to_numpy(),
        }
    )
    detail = pd.concat(monthly_details, ignore_index=True)
    return detail, submission


def blend_detail_and_submission(
    pure_detail: pd.DataFrame,
    pure_submission: pd.DataFrame,
    rule_detail: pd.DataFrame,
    rule_submission: pd.DataFrame,
    rule_weight: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    lstm_weight = 1 - rule_weight

    merged = pure_detail[
        ["date", "report_date", "validation_month", "purchase", "redeem", "pred_purchase", "pred_redeem"]
    ].merge(
        rule_detail[
            ["date", "report_date", "validation_month", "pred_purchase", "pred_redeem"]
        ].rename(
            columns={
                "pred_purchase": "rule_pred_purchase",
                "pred_redeem": "rule_pred_redeem",
            }
        ),
        on=["date", "report_date", "validation_month"],
        how="inner",
    )

    blended_detail = merged[
        ["date", "report_date", "validation_month", "purchase", "redeem"]
    ].copy()
    blended_detail["pred_purchase"] = np.round(
        rule_weight * merged["rule_pred_purchase"].astype(float)
        + lstm_weight * merged["pred_purchase"].astype(float)
    ).clip(lower=0).astype("int64")
    blended_detail["pred_redeem"] = np.round(
        rule_weight * merged["rule_pred_redeem"].astype(float)
        + lstm_weight * merged["pred_redeem"].astype(float)
    ).clip(lower=0).astype("int64")

    submission = pure_submission.copy()
    submission["purchase"] = np.round(
        rule_weight * rule_submission["purchase"].astype(float)
        + lstm_weight * pure_submission["purchase"].astype(float)
    ).clip(lower=0).astype("int64")
    submission["redeem"] = np.round(
        rule_weight * rule_submission["redeem"].astype(float)
        + lstm_weight * pure_submission["redeem"].astype(float)
    ).clip(lower=0).astype("int64")
    return blended_detail, submission


def candidate_sort_key(row: pd.Series) -> tuple[float, float]:
    return (
        float(row["overall_weighted_proxy_score_mean"]),
        float(row["august_weighted_proxy_score_mean"]),
    )


def main() -> None:
    import tensorflow as tf

    del tf
    ensure_output_dir()
    set_global_seed()

    features = load_daily_features()
    rule_rolling_detail = pd.read_csv(
        OUTPUT_DIR / "rolling_validation_2014_05_08.csv",
        parse_dates=["date"],
    )
    rule_submission = rule_model.predict_september(features)
    baseline_summary = rule_baseline_summary(features)

    pure_results: list[dict[str, object]] = []
    for spec in EXPERIMENT_SPECS:
        detail, submission = pure_experiment_detail(features, spec)
        detail = score_detail(detail)
        summary = summarize_detail(detail)
        august_detail = detail[detail["validation_month"] == "2014-08"].copy()
        august_gate_pass, gate_failures, august_stats = evaluate_august_gate(
            august_detail[
                ["purchase", "redeem", "pred_purchase", "pred_redeem"]
            ].copy(),
            submission,
        )
        pure_results.append(
            {
                "name": spec.name,
                "type": "pure",
                "spec": asdict(spec),
                "detail": detail,
                "summary": summary,
                "submission": submission,
                "august_gate_pass": august_gate_pass,
                "gate_failures": gate_failures,
                "august_stats": august_stats,
            }
        )

    pure_ranked = sorted(
        pure_results,
        key=lambda item: (
            item["summary"]["overall"]["weighted_proxy_score_mean"],
            next(
                month["weighted_proxy_score_mean"]
                for month in item["summary"]["months"]
                if month["validation_month"] == "2014-08"
            ),
        ),
        reverse=True,
    )
    best_pure = pure_ranked[0]

    blend_results: list[dict[str, object]] = []
    for rule_weight in BLEND_RULE_WEIGHTS:
        detail, submission = blend_detail_and_submission(
            pure_detail=best_pure["detail"],
            pure_submission=best_pure["submission"],
            rule_detail=rule_rolling_detail,
            rule_submission=rule_submission,
            rule_weight=rule_weight,
        )
        detail = score_detail(detail)
        summary = summarize_detail(detail)
        august_detail = detail[detail["validation_month"] == "2014-08"].copy()
        august_gate_pass, gate_failures, august_stats = evaluate_august_gate(
            august_detail[
                ["purchase", "redeem", "pred_purchase", "pred_redeem"]
            ].copy(),
            submission,
        )
        blend_results.append(
            {
                "name": f"blend_rule{int(rule_weight * 100):02d}_lstm{int((1 - rule_weight) * 100):02d}",
                "type": "blend",
                "spec": {
                    "look_back": best_pure["spec"]["look_back"],
                    "ema_span": best_pure["spec"]["ema_span"],
                    "rule_weight": rule_weight,
                    "lstm_weight": 1 - rule_weight,
                    "source_pure": best_pure["name"],
                },
                "detail": detail,
                "summary": summary,
                "submission": submission,
                "august_gate_pass": august_gate_pass,
                "gate_failures": gate_failures,
                "august_stats": august_stats,
            }
        )

    best_blend = sorted(
        blend_results,
        key=lambda item: (
            item["summary"]["overall"]["weighted_proxy_score_mean"],
            next(
                month["weighted_proxy_score_mean"]
                for month in item["summary"]["months"]
                if month["validation_month"] == "2014-08"
            ),
        ),
        reverse=True,
    )[0]

    summary_rows: list[dict[str, object]] = []
    all_details: list[pd.DataFrame] = []
    for result in pure_results + blend_results:
        detail = result["detail"].copy()
        detail["experiment_name"] = result["name"]
        detail["experiment_type"] = result["type"]
        all_details.append(detail)
        spec = result["spec"]
        summary_rows.append(
            summary_row(
                experiment_name=result["name"],
                experiment_type=result["type"],
                summary=result["summary"],
                submission_issues=result["gate_failures"],
                august_gate_pass=result["august_gate_pass"],
                look_back=spec.get("look_back"),
                ema_span=spec.get("ema_span"),
                rule_weight=spec.get("rule_weight"),
                lstm_weight=spec.get("lstm_weight"),
                source_pure=spec.get("source_pure"),
            )
        )

    combined_detail = pd.concat(all_details, ignore_index=True)
    combined_august = combined_detail[combined_detail["validation_month"] == "2014-08"].copy()
    summary_df = pd.DataFrame(summary_rows).sort_values(
        by=["overall_weighted_proxy_score_mean", "august_weighted_proxy_score_mean"],
        ascending=False,
    )

    eligible_rows = summary_df[
        (summary_df["august_gate_pass"] == True)
        & (summary_df["overall_weighted_proxy_score_mean"] > BASELINE_OVERALL_PROXY)
        & (summary_df["overall_bad_day_rate_max"] <= BASELINE_BAD_DAY_RATE)
    ].copy()
    promoted_experiment_name = (
        None if eligible_rows.empty else eligible_rows.iloc[0]["experiment_name"]
    )

    best_challenger = summary_df.iloc[0]
    selection_payload = {
        "baseline_summary": baseline_summary,
        "best_pure_experiment": best_pure["name"],
        "best_blend_experiment": best_blend["name"],
        "best_overall_experiment": str(best_challenger["experiment_name"]),
        "best_overall_type": str(best_challenger["experiment_type"]),
        "best_overall_proxy_score": float(best_challenger["overall_weighted_proxy_score_mean"]),
        "best_overall_august_proxy_score": float(best_challenger["august_weighted_proxy_score_mean"]),
        "promoted_experiment_name": promoted_experiment_name,
        "promoted_to_official_submission": promoted_experiment_name is not None,
        "promotion_thresholds": {
            "overall_weighted_proxy_score_mean": BASELINE_OVERALL_PROXY,
            "rolling_bad_day_rate_max": BASELINE_BAD_DAY_RATE,
            "august_gate_pass_required": True,
        },
    }

    promoted_submission = None
    if promoted_experiment_name is not None:
        promoted_submission = next(
            result["submission"]
            for result in pure_results + blend_results
            if result["name"] == promoted_experiment_name
        )
        promoted_submission.to_csv(
            OFFICIAL_SUBMISSION_PATH,
            index=False,
            header=False,
            encoding="utf-8",
        )
        selection_payload["official_submission_overwritten"] = True
    else:
        selection_payload["official_submission_overwritten"] = False

    combined_detail.to_csv(LSTM_COMBINED_DETAIL_PATH, index=False, encoding="utf-8")
    combined_august.to_csv(LSTM_COMBINED_AUGUST_PATH, index=False, encoding="utf-8")
    summary_df.to_csv(LSTM_SUMMARY_CSV_PATH, index=False, encoding="utf-8")
    LSTM_SUMMARY_JSON_PATH.write_text(
        json.dumps(summary_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    LSTM_SELECTION_PATH.write_text(
        json.dumps(selection_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    best_pure["detail"][best_pure["detail"]["validation_month"] == "2014-08"].to_csv(
        LSTM_BEST_PURE_VALIDATION_PATH,
        index=False,
        encoding="utf-8",
    )
    best_pure["submission"].to_csv(
        LSTM_BEST_PURE_SUBMISSION_PATH,
        index=False,
        header=False,
        encoding="utf-8",
    )
    best_blend["detail"][best_blend["detail"]["validation_month"] == "2014-08"].to_csv(
        LSTM_BEST_BLEND_VALIDATION_PATH,
        index=False,
        encoding="utf-8",
    )
    best_blend["submission"].to_csv(
        LSTM_BEST_BLEND_SUBMISSION_PATH,
        index=False,
        header=False,
        encoding="utf-8",
    )

    print("LSTM challenger summary")
    print("=======================")
    print(
        f"Best pure: {best_pure['name']} "
        f"(overall_proxy={best_pure['summary']['overall']['weighted_proxy_score_mean']:.6f}, "
        f"august_proxy={next(month['weighted_proxy_score_mean'] for month in best_pure['summary']['months'] if month['validation_month'] == '2014-08'):.6f}, "
        f"gate={'PASS' if best_pure['august_gate_pass'] else 'FAIL'})"
    )
    print(
        f"Best blend: {best_blend['name']} "
        f"(overall_proxy={best_blend['summary']['overall']['weighted_proxy_score_mean']:.6f}, "
        f"august_proxy={next(month['weighted_proxy_score_mean'] for month in best_blend['summary']['months'] if month['validation_month'] == '2014-08'):.6f}, "
        f"gate={'PASS' if best_blend['august_gate_pass'] else 'FAIL'})"
    )
    if promoted_experiment_name is None:
        print("Promotion decision: KEEP current rule baseline as official candidate")
    else:
        print(f"Promotion decision: challenger {promoted_experiment_name} qualifies for promotion")
    print(f"Saved combined detail: {LSTM_COMBINED_DETAIL_PATH}")
    print(f"Saved august detail: {LSTM_COMBINED_AUGUST_PATH}")
    print(f"Saved summary csv:   {LSTM_SUMMARY_CSV_PATH}")
    print(f"Saved selection:     {LSTM_SELECTION_PATH}")


if __name__ == "__main__":
    main()

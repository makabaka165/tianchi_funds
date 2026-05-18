from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Purchase Redemption Data"
OUTPUT_DIR = ROOT / "output"

BALANCE_PATH = DATA_DIR / "user_balance_table.csv"
INTEREST_PATH = DATA_DIR / "mfd_day_share_interest.csv"
SHIBOR_PATH = DATA_DIR / "mfd_bank_shibor.csv"
SUBMISSION_PATH = OUTPUT_DIR / "tc_comp_predict_table.csv"
DAILY_FEATURES_PATH = OUTPUT_DIR / "daily_features.csv"
VALIDATION_PATH = OUTPUT_DIR / "validation_august_2014.csv"


@dataclass(frozen=True)
class ArtifactPaths:
    daily_features: Path
    validation: Path
    submission: Path


def resolve_artifact_paths(tag: str = "") -> ArtifactPaths:
    suffix = f"_{tag}" if tag else ""
    return ArtifactPaths(
        daily_features=OUTPUT_DIR / f"daily_features{suffix}.csv",
        validation=OUTPUT_DIR / f"validation_august_2014{suffix}.csv",
        submission=OUTPUT_DIR / f"tc_comp_predict_table{suffix}.csv",
    )

PURCHASE_CALIBRATION = 0.98
REDEEM_CALIBRATION = 0.85
PURCHASE_OPTIMIZED_BLEND = 0.09
PURCHASE_OPTIMIZED_CONFIG = {
    "recent_weekday_weight": 0.86,
    "long_weekday_weight": 0.04,
    "recent_30_weight": 0.00,
    "recent_14_weight": 0.10,
    "calibration": 0.93,
}
PURCHASE_OPTIMIZED_SIGNAL_R7_28_THRESHOLD = 0.90
PURCHASE_OPTIMIZED_SIGNAL_APU7_28_THRESHOLD = 0.90
PURCHASE_OPTIMIZED_BLEND_ACTIVE = 0.18
PURCHASE_OPTIMIZED_BLEND_INACTIVE = 0.06
HOLIDAY_PURCHASE_FACTOR = 0.50
HOLIDAY_REDEEM_FACTOR = 0.60
POST_HOLIDAY_PURCHASE_FACTOR = 0.90
POST_HOLIDAY_REDEEM_FACTOR = 1.50
REDEEM_LATE_MONTH_START_DAY = 22
REDEEM_LATE_MONTH_END_DAY = 29
REDEEM_LATE_MONTH_FACTOR = 1.08
REDEEM_DAY18_FACTOR = 0.84
MONDAY_REDEEM_FACTOR = 1.09
REDEEM_MONTH_END_START_DAY = 28
REDEEM_MONTH_END_END_DAY = 31
REDEEM_MONTH_END_FACTOR = 1.06
REDEEM_DAY10_FACTOR = 1.04
REDEEM_DAY6_FACTOR = 1.04
REDEEM_DAY8_FACTOR = 1.16
REDEEM_DAY16_FACTOR = 1.23
REDEEM_DAY18_TO_21_FACTOR = 0.96
REDEEM_DAY26_FACTOR = 0.88
THURSDAY_REDEEM_FACTOR = 1.03
SUNDAY_REDEEM_FACTOR = 0.95
TUESDAY_REDEEM_FACTOR = 1.05
REDEEM_DAY3_TO_6_FACTOR = 1.03
REDEEM_DAY14_FACTOR = 0.92
REDEEM_DAY10_EXTRA_FACTOR = 1.06
SATURDAY_REDEEM_EXTRA_FACTOR = 0.95
REDEEM_DAY24_FACTOR = 1.06
REDEEM_DAY25_TO_27_FACTOR = 1.00
REDEEM_DAY13_FACTOR = 1.06
REDEEM_DAY16_TO_17_EXTRA_FACTOR = 1.04
REDEEM_DAY8_TO_9_EXTRA_FACTOR = 0.96
PURCHASE_LATE_MONTH_START_DAY = 21
PURCHASE_LATE_MONTH_END_DAY = 29
PURCHASE_LATE_MONTH_FACTOR = 0.85
SUNDAY_PURCHASE_FACTOR = 0.92
SATURDAY_PURCHASE_FACTOR = 0.93
TUESDAY_PURCHASE_FACTOR = 0.93
PURCHASE_DAY17_FACTOR = 0.80
PURCHASE_DAY14_FACTOR = 0.89
PURCHASE_DAY16_FACTOR = 1.16
PURCHASE_DAY24_FACTOR = 0.91
PURCHASE_DAY13_FACTOR = 0.90
PURCHASE_DAY15_TO_21_FACTOR = 1.03
PURCHASE_DAY4_FACTOR = 0.90
PURCHASE_DAY16_EXTRA_FACTOR = 1.00
PURCHASE_DAY18_FACTOR = 0.90
MONDAY_PURCHASE_FACTOR = 1.06
THURSDAY_PURCHASE_FACTOR = 1.03
PURCHASE_DAY7_FACTOR = 0.90
PURCHASE_DAY3_TO_4_FACTOR = 0.96
PURCHASE_DAY26_TO_27_FACTOR = 1.04
SUNDAY_PURCHASE_EXTRA_FACTOR = 0.98
PURCHASE_DAY10_FACTOR = 1.06
PURCHASE_DAY29_FACTOR = 1.03
PURCHASE_DAY8_FACTOR = 1.04
REDEEM_DAY30_FACTOR = 1.06
REDEEM_QUARTER_END_LATE_START_DAY = 16
REDEEM_QUARTER_END_LATE_FACTOR_HIGH = 1.20
REDEEM_QUARTER_END_LATE_FACTOR_LOW = 1.06
REDEEM_QUARTER_END_SIGNAL_R14_56_THRESHOLD = 0.98
REDEEM_RESIDUAL_QUARTER_END_START_DAY = 16
REDEEM_RESIDUAL_QUARTER_END_UPLIFT = 1.15
REDEEM_RESIDUAL_SIGNAL_R7_28_THRESHOLD = 1.10
REDEEM_RESIDUAL_SIGNAL_APU7_28_THRESHOLD = 1.08
REDEEM_TRIGGERED_MONTH_END_SIGNAL_R7_28_THRESHOLD = 1.10
REDEEM_TRIGGERED_MONTH_END_SIGNAL_APU7_28_THRESHOLD = 1.08
REDEEM_TRIGGERED_MONTH_END_SIGNAL_USERS7_28_THRESHOLD = 1.03
REDEEM_LOW_VARIANCE_SIGNAL_R7_28_THRESHOLD = 1.10
REDEEM_LOW_VARIANCE_SIGNAL_APU7_28_THRESHOLD = 1.08
REDEEM_LOW_VARIANCE_SIGNAL_USERS7_28_THRESHOLD = 1.03
REDEEM_LOW_VARIANCE_DAY15_FACTOR = 0.94
REDEEM_LOW_VARIANCE_V2_DAY15_FACTOR = 0.86
REDEEM_LOW_VARIANCE_V2_DAY16_FACTOR = 0.92

HOLIDAY_DATES = {
    "2014-05-01",
    "2014-05-02",
    "2014-05-03",
    "2014-06-02",
    "2014-09-08",
}


SUM_COLUMNS = [
    "tBalance",
    "yBalance",
    "total_purchase_amt",
    "direct_purchase_amt",
    "purchase_bal_amt",
    "purchase_bank_amt",
    "total_redeem_amt",
    "consume_amt",
    "transfer_amt",
    "tftobal_amt",
    "tftocard_amt",
    "share_amt",
    "category1",
    "category2",
    "category3",
    "category4",
]


def ensure_input_files() -> None:
    missing = [
        path
        for path in [BALANCE_PATH, INTEREST_PATH, SHIBOR_PATH]
        if not path.exists()
    ]
    if missing:
        names = "\n".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing required data files:\n{names}")


def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    result = df.copy()
    date = result[date_col]
    result["report_date"] = date.dt.strftime("%Y%m%d").astype(int)
    result["weekday"] = date.dt.weekday
    result["day"] = date.dt.day
    result["month"] = date.dt.month
    result["is_weekend"] = result["weekday"].isin([5, 6]).astype(int)
    result["is_month_start"] = date.dt.is_month_start.astype(int)
    result["is_month_end"] = date.dt.is_month_end.astype(int)
    result["days_to_month_end"] = (date.dt.days_in_month - date.dt.day).astype(int)
    return result


def aggregate_daily_balance(chunksize: int = 500_000) -> pd.DataFrame:
    aggregations = []
    usecols = ["user_id", "report_date", *SUM_COLUMNS]

    for chunk in pd.read_csv(BALANCE_PATH, usecols=usecols, chunksize=chunksize):
        chunk[SUM_COLUMNS] = chunk[SUM_COLUMNS].fillna(0)
        grouped_sum = chunk.groupby("report_date", as_index=False)[SUM_COLUMNS].sum()
        grouped_users = (
            chunk.groupby("report_date")["user_id"]
            .nunique()
            .rename("active_users")
            .reset_index()
        )
        grouped_purchase_users = (
            chunk.loc[chunk["total_purchase_amt"] > 0]
            .groupby("report_date")["user_id"]
            .nunique()
            .rename("purchase_users")
            .reset_index()
        )
        grouped_redeem_users = (
            chunk.loc[chunk["total_redeem_amt"] > 0]
            .groupby("report_date")["user_id"]
            .nunique()
            .rename("redeem_users")
            .reset_index()
        )

        grouped = grouped_sum.merge(grouped_users, on="report_date", how="left")
        grouped = grouped.merge(grouped_purchase_users, on="report_date", how="left")
        grouped = grouped.merge(grouped_redeem_users, on="report_date", how="left")
        aggregations.append(grouped)

    daily = pd.concat(aggregations, ignore_index=True).fillna(0)
    total_sum_cols = SUM_COLUMNS + ["active_users", "purchase_users", "redeem_users"]
    daily = daily.groupby("report_date", as_index=False)[total_sum_cols].sum()
    daily["date"] = pd.to_datetime(daily["report_date"].astype(str), format="%Y%m%d")
    daily = daily.sort_values("date").reset_index(drop=True)
    daily = add_calendar_features(daily)

    daily["purchase"] = daily["total_purchase_amt"]
    daily["redeem"] = daily["total_redeem_amt"]
    daily["avg_purchase_per_user"] = np.where(
        daily["purchase_users"] > 0,
        daily["purchase"] / daily["purchase_users"],
        0,
    )
    daily["avg_redeem_per_user"] = np.where(
        daily["redeem_users"] > 0,
        daily["redeem"] / daily["redeem_users"],
        0,
    )
    return daily


def load_external_features() -> pd.DataFrame:
    interest = pd.read_csv(INTEREST_PATH)
    interest["date"] = pd.to_datetime(interest["mfd_date"].astype(str), format="%Y%m%d")
    interest = interest.drop(columns=["mfd_date"])

    shibor = pd.read_csv(SHIBOR_PATH)
    shibor["date"] = pd.to_datetime(shibor["mfd_date"].astype(str), format="%Y%m%d")
    shibor = shibor.drop(columns=["mfd_date"])

    return interest.merge(shibor, on="date", how="outer")


def build_daily_features() -> pd.DataFrame:
    daily = aggregate_daily_balance()
    external = load_external_features()
    features = daily.merge(external, on="date", how="left")
    return features.sort_values("date").reset_index(drop=True)


def weekday_window_predict(
    history: pd.DataFrame,
    predict_dates: pd.Series,
    target_col: str,
    config: dict[str, float] | None = None,
) -> pd.Series:
    history = history.sort_values("date").copy()
    config = config or {
        "recent_weekday_weight": 0.60,
        "long_weekday_weight": 0.25,
        "recent_30_weight": 0.10,
        "recent_14_weight": 0.05,
    }
    global_median = history[target_col].tail(30).median()
    recent_14 = history[target_col].tail(14).mean()
    recent_30 = history[target_col].tail(30).mean()

    weekday_mean = (
        history.tail(120)
        .groupby("weekday")[target_col]
        .mean()
        .to_dict()
    )
    weekday_recent = (
        history.tail(56)
        .groupby("weekday")[target_col]
        .mean()
        .to_dict()
    )

    predictions = []
    for date in predict_dates:
        weekday = date.weekday()
        value = (
            config["recent_weekday_weight"] * weekday_recent.get(weekday, global_median)
            + config["long_weekday_weight"] * weekday_mean.get(weekday, global_median)
            + config["recent_30_weight"] * recent_30
            + config["recent_14_weight"] * recent_14
        )
        predictions.append(max(0, int(round(value))))

    return pd.Series(predictions, index=predict_dates.index, dtype="int64")


def apply_calibration(predictions: pd.Series, target_col: str) -> pd.Series:
    if target_col == "purchase":
        factor = PURCHASE_CALIBRATION
    elif target_col == "redeem":
        factor = REDEEM_CALIBRATION
    else:
        raise ValueError(f"Unsupported target column: {target_col}")

    calibrated = (predictions.astype(float) * factor).round().clip(lower=0)
    return calibrated.astype("int64")


def apply_config_calibration(
    predictions: pd.Series,
    config: dict[str, float],
) -> pd.Series:
    calibrated = (predictions.astype(float) * config["calibration"]).round().clip(lower=0)
    return calibrated.astype("int64")


def apply_holiday_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
    target_col: str,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    holidays = {pd.Timestamp(date) for date in HOLIDAY_DATES}

    for idx, date in predict_dates.items():
        current_date = pd.Timestamp(date)
        is_holiday = current_date in holidays
        is_post_holiday = (
            current_date - pd.Timedelta(days=1) in holidays
            and current_date not in holidays
        )

        if target_col == "purchase":
            if is_holiday:
                adjusted.loc[idx] *= HOLIDAY_PURCHASE_FACTOR
            elif is_post_holiday:
                adjusted.loc[idx] *= POST_HOLIDAY_PURCHASE_FACTOR
        elif target_col == "redeem":
            if is_holiday:
                adjusted.loc[idx] *= HOLIDAY_REDEEM_FACTOR
            elif is_post_holiday:
                adjusted.loc[idx] *= POST_HOLIDAY_REDEEM_FACTOR
        else:
            raise ValueError(f"Unsupported target column: {target_col}")

    return adjusted.round().clip(lower=0).astype("int64")


def apply_late_month_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if REDEEM_LATE_MONTH_START_DAY <= day <= REDEEM_LATE_MONTH_END_DAY:
            adjusted.loc[idx] *= REDEEM_LATE_MONTH_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day18_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 18:
            adjusted.loc[idx] *= REDEEM_DAY18_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_monday_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 0:
            adjusted.loc[idx] *= MONDAY_REDEEM_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_month_end_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if REDEEM_MONTH_END_START_DAY <= day <= REDEEM_MONTH_END_END_DAY:
            adjusted.loc[idx] *= REDEEM_MONTH_END_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day10_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 10:
            adjusted.loc[idx] *= REDEEM_DAY10_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day6_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 6:
            adjusted.loc[idx] *= REDEEM_DAY6_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day8_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 8:
            adjusted.loc[idx] *= REDEEM_DAY8_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day16_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 16:
            adjusted.loc[idx] *= REDEEM_DAY16_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day18_to_21_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if 18 <= day <= 21:
            adjusted.loc[idx] *= REDEEM_DAY18_TO_21_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day26_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 26:
            adjusted.loc[idx] *= REDEEM_DAY26_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_thursday_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 3:
            adjusted.loc[idx] *= THURSDAY_REDEEM_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_sunday_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 6:
            adjusted.loc[idx] *= SUNDAY_REDEEM_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_tuesday_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 1:
            adjusted.loc[idx] *= TUESDAY_REDEEM_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day3_to_6_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if 3 <= day <= 6:
            adjusted.loc[idx] *= REDEEM_DAY3_TO_6_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day14_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 14:
            adjusted.loc[idx] *= REDEEM_DAY14_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day10_redeem_extra_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 10:
            adjusted.loc[idx] *= REDEEM_DAY10_EXTRA_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_saturday_redeem_extra_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 5:
            adjusted.loc[idx] *= SATURDAY_REDEEM_EXTRA_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day24_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 24:
            adjusted.loc[idx] *= REDEEM_DAY24_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day25_to_27_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if 25 <= day <= 27:
            adjusted.loc[idx] *= REDEEM_DAY25_TO_27_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day13_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 13:
            adjusted.loc[idx] *= REDEEM_DAY13_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day16_to_17_redeem_extra_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if 16 <= day <= 17:
            adjusted.loc[idx] *= REDEEM_DAY16_TO_17_EXTRA_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day8_to_9_redeem_extra_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if 8 <= day <= 9:
            adjusted.loc[idx] *= REDEEM_DAY8_TO_9_EXTRA_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_late_month_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if PURCHASE_LATE_MONTH_START_DAY <= day <= PURCHASE_LATE_MONTH_END_DAY:
            adjusted.loc[idx] *= PURCHASE_LATE_MONTH_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_sunday_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 6:
            adjusted.loc[idx] *= SUNDAY_PURCHASE_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_saturday_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 5:
            adjusted.loc[idx] *= SATURDAY_PURCHASE_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_tuesday_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 1:
            adjusted.loc[idx] *= TUESDAY_PURCHASE_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day17_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 17:
            adjusted.loc[idx] *= PURCHASE_DAY17_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day14_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 14:
            adjusted.loc[idx] *= PURCHASE_DAY14_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day16_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 16:
            adjusted.loc[idx] *= PURCHASE_DAY16_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day24_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 24:
            adjusted.loc[idx] *= PURCHASE_DAY24_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day13_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 13:
            adjusted.loc[idx] *= PURCHASE_DAY13_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day15_to_21_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if 15 <= day <= 21:
            adjusted.loc[idx] *= PURCHASE_DAY15_TO_21_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day4_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 4:
            adjusted.loc[idx] *= PURCHASE_DAY4_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day16_purchase_extra_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 16:
            adjusted.loc[idx] *= PURCHASE_DAY16_EXTRA_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day18_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 18:
            adjusted.loc[idx] *= PURCHASE_DAY18_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_monday_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 0:
            adjusted.loc[idx] *= MONDAY_PURCHASE_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_thursday_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 3:
            adjusted.loc[idx] *= THURSDAY_PURCHASE_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day7_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 7:
            adjusted.loc[idx] *= PURCHASE_DAY7_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day3_to_4_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if 3 <= day <= 4:
            adjusted.loc[idx] *= PURCHASE_DAY3_TO_4_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day26_to_27_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if 26 <= day <= 27:
            adjusted.loc[idx] *= PURCHASE_DAY26_TO_27_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_sunday_purchase_extra_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).weekday() == 6:
            adjusted.loc[idx] *= SUNDAY_PURCHASE_EXTRA_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day10_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 10:
            adjusted.loc[idx] *= PURCHASE_DAY10_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day29_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 29:
            adjusted.loc[idx] *= PURCHASE_DAY29_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day8_purchase_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 8:
            adjusted.loc[idx] *= PURCHASE_DAY8_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day30_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 30:
            adjusted.loc[idx] *= REDEEM_DAY30_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_quarter_end_late_redeem_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
    history: pd.DataFrame,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    signal = history["redeem"].tail(14).mean() / history["redeem"].tail(56).mean()
    factor = (
        REDEEM_QUARTER_END_LATE_FACTOR_HIGH
        if signal >= REDEEM_QUARTER_END_SIGNAL_R14_56_THRESHOLD
        else REDEEM_QUARTER_END_LATE_FACTOR_LOW
    )
    for idx, date in predict_dates.items():
        current = pd.Timestamp(date)
        if current.month in {3, 6, 9, 12} and current.day >= REDEEM_QUARTER_END_LATE_START_DAY:
            adjusted.loc[idx] *= factor
    return adjusted.round().clip(lower=0).astype("int64")


def apply_quarter_end_redeem_residual_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
    history: pd.DataFrame,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    r7_28 = history["redeem"].tail(7).mean() / history["redeem"].tail(28).mean()
    apu7_28 = (
        history["avg_redeem_per_user"].tail(7).mean()
        / history["avg_redeem_per_user"].tail(28).mean()
    )
    active = (
        r7_28 >= REDEEM_RESIDUAL_SIGNAL_R7_28_THRESHOLD
        and apu7_28 >= REDEEM_RESIDUAL_SIGNAL_APU7_28_THRESHOLD
    )
    if not active:
        return adjusted.round().clip(lower=0).astype("int64")

    for idx, date in predict_dates.items():
        current = pd.Timestamp(date)
        if (
            current.month in {3, 6, 9, 12}
            and current.day >= REDEEM_RESIDUAL_QUARTER_END_START_DAY
        ):
            adjusted.loc[idx] *= REDEEM_RESIDUAL_QUARTER_END_UPLIFT
    return adjusted.round().clip(lower=0).astype("int64")


def get_purchase_optimized_blend(history: pd.DataFrame) -> float:
    purchase_r7_28 = history["purchase"].tail(7).mean() / history["purchase"].tail(28).mean()
    apu7_28 = (
        history["avg_purchase_per_user"].tail(7).mean()
        / history["avg_purchase_per_user"].tail(28).mean()
    )
    active = (
        purchase_r7_28 >= PURCHASE_OPTIMIZED_SIGNAL_R7_28_THRESHOLD
        and apu7_28 >= PURCHASE_OPTIMIZED_SIGNAL_APU7_28_THRESHOLD
    )
    return (
        PURCHASE_OPTIMIZED_BLEND_ACTIVE
        if active
        else PURCHASE_OPTIMIZED_BLEND_INACTIVE
    )


def rolling_mean_ratio(series: pd.Series, short_window: int, long_window: int) -> float:
    short_mean = float(series.tail(short_window).mean())
    long_mean = float(series.tail(long_window).mean())
    if pd.isna(long_mean) or long_mean == 0:
        return 1.0
    return short_mean / long_mean


def should_apply_redeem_feature_triggered_month_end(history: pd.DataFrame) -> bool:
    r7_28 = rolling_mean_ratio(history["redeem"], 7, 28)
    apu7_28 = rolling_mean_ratio(history["avg_redeem_per_user"], 7, 28)
    users7_28 = rolling_mean_ratio(history["redeem_users"], 7, 28)
    return (
        r7_28 >= REDEEM_TRIGGERED_MONTH_END_SIGNAL_R7_28_THRESHOLD
        and (
            apu7_28 >= REDEEM_TRIGGERED_MONTH_END_SIGNAL_APU7_28_THRESHOLD
            or users7_28 >= REDEEM_TRIGGERED_MONTH_END_SIGNAL_USERS7_28_THRESHOLD
        )
    )


def should_apply_redeem_low_variance(history: pd.DataFrame) -> bool:
    r7_28 = rolling_mean_ratio(history["redeem"], 7, 28)
    apu7_28 = rolling_mean_ratio(history["avg_redeem_per_user"], 7, 28)
    users7_28 = rolling_mean_ratio(history["redeem_users"], 7, 28)
    return (
        r7_28 >= REDEEM_LOW_VARIANCE_SIGNAL_R7_28_THRESHOLD
        and (
            apu7_28 >= REDEEM_LOW_VARIANCE_SIGNAL_APU7_28_THRESHOLD
            or users7_28 >= REDEEM_LOW_VARIANCE_SIGNAL_USERS7_28_THRESHOLD
        )
    )


def apply_day15_redeem_low_variance_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        if pd.Timestamp(date).day == 15:
            adjusted.loc[idx] *= REDEEM_LOW_VARIANCE_DAY15_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def apply_day15_to_16_redeem_low_variance_v2_adjustment(
    predictions: pd.Series,
    predict_dates: pd.Series,
) -> pd.Series:
    adjusted = predictions.astype(float).copy()
    for idx, date in predict_dates.items():
        day = pd.Timestamp(date).day
        if day == 15:
            adjusted.loc[idx] *= REDEEM_LOW_VARIANCE_V2_DAY15_FACTOR
        elif day == 16:
            adjusted.loc[idx] *= REDEEM_LOW_VARIANCE_V2_DAY16_FACTOR
    return adjusted.round().clip(lower=0).astype("int64")


def predict_target(
    history: pd.DataFrame,
    predict_dates: pd.Series,
    target_col: str,
    strategy: str = "baseline",
) -> pd.Series:
    calibrated = apply_calibration(
        weekday_window_predict(history, predict_dates, target_col),
        target_col,
    )
    if target_col == "purchase":
        purchase_optimized_blend = get_purchase_optimized_blend(history)
    else:
        purchase_optimized_blend = 0.0
    if target_col == "purchase" and purchase_optimized_blend > 0:
        optimized = apply_config_calibration(
            weekday_window_predict(
                history,
                predict_dates,
                target_col,
                config=PURCHASE_OPTIMIZED_CONFIG,
            ),
            PURCHASE_OPTIMIZED_CONFIG,
        )
        calibrated = (
            purchase_optimized_blend * optimized.astype(float)
            + (1 - purchase_optimized_blend) * calibrated.astype(float)
        ).round().astype("int64")

    adjusted = apply_holiday_adjustment(calibrated, predict_dates, target_col)
    if target_col == "purchase":
        adjusted = apply_late_month_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_sunday_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_saturday_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_tuesday_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day17_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day14_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day16_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day24_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day13_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day15_to_21_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day4_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day16_purchase_extra_adjustment(adjusted, predict_dates)
        adjusted = apply_day18_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_monday_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_thursday_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day7_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day3_to_4_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day26_to_27_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_sunday_purchase_extra_adjustment(adjusted, predict_dates)
        adjusted = apply_day10_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day29_purchase_adjustment(adjusted, predict_dates)
        adjusted = apply_day8_purchase_adjustment(adjusted, predict_dates)
    elif target_col == "redeem":
        month_end_active = (
            strategy != "redeem_feature_triggered_month_end"
            or should_apply_redeem_feature_triggered_month_end(history)
        )
        adjusted = apply_late_month_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day18_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_monday_redeem_adjustment(adjusted, predict_dates)
        if month_end_active:
            adjusted = apply_month_end_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day10_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day6_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day8_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day16_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day18_to_21_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day26_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_thursday_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_sunday_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_tuesday_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day3_to_6_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day14_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day10_redeem_extra_adjustment(adjusted, predict_dates)
        adjusted = apply_saturday_redeem_extra_adjustment(adjusted, predict_dates)
        if strategy != "redeem_compact_month_end":
            adjusted = apply_day24_redeem_adjustment(adjusted, predict_dates)
            adjusted = apply_day25_to_27_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day13_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_day16_to_17_redeem_extra_adjustment(adjusted, predict_dates)
        adjusted = apply_day8_to_9_redeem_extra_adjustment(adjusted, predict_dates)
        if month_end_active:
            adjusted = apply_day30_redeem_adjustment(adjusted, predict_dates)
        adjusted = apply_quarter_end_late_redeem_adjustment(adjusted, predict_dates, history)
        adjusted = apply_quarter_end_redeem_residual_adjustment(
            adjusted, predict_dates, history
        )
        if should_apply_redeem_low_variance(history):
            if strategy == "redeem_low_variance_v1":
                adjusted = apply_day15_redeem_low_variance_adjustment(adjusted, predict_dates)
            elif strategy == "redeem_low_variance_v2":
                adjusted = apply_day15_to_16_redeem_low_variance_v2_adjustment(
                    adjusted, predict_dates
                )
    return adjusted


def weighted_relative_error(y_true: pd.Series, y_pred: pd.Series) -> float:
    denominator = y_true.replace(0, np.nan)
    errors = (y_pred - y_true).abs() / denominator
    return float(errors.fillna(0).mean())


def validate_august(features: pd.DataFrame, strategy: str = "baseline") -> pd.DataFrame:
    train = features[features["date"] < "2014-08-01"].copy()
    valid = features[
        (features["date"] >= "2014-08-01") & (features["date"] <= "2014-08-31")
    ].copy()

    valid["pred_purchase"] = predict_target(train, valid["date"], "purchase", strategy)
    valid["pred_redeem"] = predict_target(train, valid["date"], "redeem", strategy)
    valid["purchase_relative_error"] = (
        (valid["pred_purchase"] - valid["purchase"]).abs() / valid["purchase"]
    )
    valid["redeem_relative_error"] = (
        (valid["pred_redeem"] - valid["redeem"]).abs() / valid["redeem"]
    )
    valid["weighted_relative_error"] = (
        0.45 * valid["purchase_relative_error"]
        + 0.55 * valid["redeem_relative_error"]
    )
    return valid


def predict_september(features: pd.DataFrame, strategy: str = "baseline") -> pd.DataFrame:
    history = features[features["date"] <= "2014-08-31"].copy()
    future = pd.DataFrame(
        {"date": pd.date_range("2014-09-01", "2014-09-30", freq="D")}
    )
    future = add_calendar_features(future)
    future["purchase"] = predict_target(history, future["date"], "purchase", strategy)
    future["redeem"] = predict_target(history, future["date"], "redeem", strategy)
    return future[["report_date", "purchase", "redeem"]]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the Tianchi funds baseline or a conservative redeem audit variant."
    )
    parser.add_argument(
        "--strategy",
        choices=[
            "baseline",
            "redeem_compact_month_end",
            "redeem_feature_triggered_month_end",
            "redeem_low_variance_v1",
            "redeem_low_variance_v2",
        ],
        default="baseline",
        help="Prediction strategy to run.",
    )
    parser.add_argument(
        "--artifact-tag",
        default="",
        help="Optional suffix for output files, useful for side-by-side comparison.",
    )
    args = parser.parse_args()

    ensure_input_files()
    OUTPUT_DIR.mkdir(exist_ok=True)
    paths = resolve_artifact_paths(args.artifact_tag)

    print(f"Building daily features from raw CSV files [{args.strategy}]...")
    features = build_daily_features()
    features.to_csv(paths.daily_features, index=False, encoding="utf-8")

    print("Validating with August 2014 holdout...")
    validation = validate_august(features, args.strategy)
    validation.to_csv(paths.validation, index=False, encoding="utf-8")

    purchase_error = weighted_relative_error(
        validation["purchase"], validation["pred_purchase"]
    )
    redeem_error = weighted_relative_error(validation["redeem"], validation["pred_redeem"])
    weighted_error = 0.45 * purchase_error + 0.55 * redeem_error

    print(f"August purchase relative error: {purchase_error:.6f}")
    print(f"August redeem relative error:   {redeem_error:.6f}")
    print(f"Weighted proxy error:           {weighted_error:.6f}")

    print("Predicting September 2014 submission...")
    submission = predict_september(features, args.strategy)
    submission.to_csv(paths.submission, index=False, header=False, encoding="utf-8")

    print(f"Saved daily features: {paths.daily_features}")
    print(f"Saved validation file: {paths.validation}")
    print(f"Saved submission file: {paths.submission}")
    print(submission.head().to_string(index=False))


if __name__ == "__main__":
    main()

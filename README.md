# Tianchi Funds Server Baseline

This repository is operated only on the server workspace `/home/ecs-user/tianchi_funds`.
The active server branch is `codex/redeem-day30-conservative`.
All analysis, edits, tests, commits, pushes, and rollbacks must be done through server git.

## Environment

```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tianchi_funds
```

## Official Stable Baseline

Current official stable model anchor:

```text
stable model commit = b709daa
stable strategy     = redeem_low_variance_v3
stable artifact tag = redeem_low_variance_v3_day21_128_day22_112_day26_112
```

This is the best retained server-side version after multiple completed optimization cycles.
Later goal-document commits do not change the stable model unless a retained candidate was actually kept.

### Stable retained redeem adjustments

```text
REDEEM_LOW_VARIANCE_V3_DAY21_FACTOR = 1.28
REDEEM_LOW_VARIANCE_V3_DAY22_FACTOR = 1.12
REDEEM_LOW_VARIANCE_V3_DAY26_FACTOR = 1.12
```

## Stable Metrics

Source: `output/rolling_validation_summary_redeem_low_variance_v3_day21_128_day22_112_day26_112.json`

```text
overall weighted_relative_error_mean = 0.11831606502050732
2014-06 weighted_relative_error_mean = 0.11407620724007135
2014-07 weighted_relative_error_mean = 0.11991147614877315
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall bad_day_rate_max             = 0.11382113821138211
2014-08 Decision                     = PASS
```

## Commands

Generate September prediction output:

```bash
python src/baseline_weekday_mean.py --strategy redeem_low_variance_v3 --artifact-tag <tag>
```

Run rolling validation:

```bash
python src/rolling_validate.py --strategy redeem_low_variance_v3 --artifact-tag <tag>
```

Run local evaluation report:

```bash
python src/evaluate.py   --validation output/validation_august_2014_<tag>.csv   --submission output/tc_comp_predict_table_<tag>.csv   --report output/evaluation_report_<tag>.json
```

## Stable Artifacts

```text
output/validation_august_2014_redeem_low_variance_v3_day21_128_day22_112_day26_112.csv
output/rolling_validation_2014_05_08_redeem_low_variance_v3_day21_128_day22_112_day26_112.csv
output/rolling_validation_summary_redeem_low_variance_v3_day21_128_day22_112_day26_112.json
output/tc_comp_predict_table_redeem_low_variance_v3_day21_128_day22_112_day26_112.csv
```

## Stable Keep Floor

Any future candidate should at minimum respect this retained floor if it is to replace the current stable model:

```text
2014-08 Decision                     == PASS
2014-08 weighted_relative_error_mean <= 0.11724453093435727
overall bad_day_rate_max             <= 0.11382113821138211
overall weighted_relative_error_mean < 0.11831606502050732
```

## Current Status

The following directions have already been exercised and exhausted under the current conservative server workflow:

- rule micro-tuning
- conservative structure optimization
- compact method-upgrade experiments
- interface-upgrade experiments
- lightweight new-system modeling experiments

See `CLOSURE_SUMMARY.md` for the closure summary and what would need to change before opening a new serious optimization line.

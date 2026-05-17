# Tianchi Funds Server Baseline

This repository is operated only on the server workspace `/home/ecs-user/tianchi_funds`.
The active server branch is `codex/redeem-day30-conservative`.
All analysis, edits, tests, commits, pushes, and rollbacks must be done through server git.

## Environment

```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tianchi_funds
```

## Current Stable Strategy

Current stable strategy: `redeem_low_variance_v1`
Current stable artifact tag: `redeem_low_variance_v1_f094`

This strategy keeps the stable redeem constants from `probe_redeem_day26_088`
and adds one gated low-variance redeem adjustment on `day15`.

### Stable redeem constants

```text
REDEEM_DAY24_FACTOR                  = 1.06
REDEEM_DAY25_TO_27_FACTOR            = 1.00
REDEEM_DAY26_FACTOR                  = 0.88
REDEEM_DAY30_FACTOR                  = 1.06
REDEEM_LOW_VARIANCE_DAY15_FACTOR     = 0.94
REDEEM_LOW_VARIANCE_SIGNAL_R7_28     >= 1.10
REDEEM_LOW_VARIANCE_SIGNAL_APU7_28   >= 1.08
REDEEM_LOW_VARIANCE_SIGNAL_USERS7_28 >= 1.03
```

## Stable Metrics

Source: `output/rolling_validation_summary_redeem_low_variance_v1_f094.json`

```text
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall weighted_relative_error_mean = 0.12362644553455275
2014-06 weighted_relative_error_mean = 0.12369324869886839
2014-07 weighted_relative_error_mean = 0.1316748812927628
overall bad_day_rate_max             = 0.13821138211382114
overall weighted_proxy_score_mean    = 6.347288400234884
2014-08 Decision                     = PASS
```

Comparison vs previous stable baseline `probe_redeem_day26_088`:

```text
overall weighted_relative_error_mean: 0.12433527645032812 -> 0.12362644553455275
2014-06 weighted_relative_error_mean: 0.1253116508850119  -> 0.12369324869886839
2014-07 weighted_relative_error_mean: 0.13292114377844227 -> 0.1316748812927628
2014-08 weighted_relative_error_mean: 0.11724453093435727 -> 0.11724453093435727
overall bad_day_rate_max:             0.13821138211382114 -> 0.13821138211382114
```

## Commands

Generate September prediction output:

```bash
python src/baseline_weekday_mean.py --strategy redeem_low_variance_v1 --artifact-tag <tag>
```

Run rolling validation:

```bash
python src/rolling_validate.py --strategy redeem_low_variance_v1 --artifact-tag <tag>
```

## Stable Artifacts

```text
output/validation_august_2014_redeem_low_variance_v1_f094.csv
output/rolling_validation_2014_05_08_redeem_low_variance_v1_f094.csv
output/rolling_validation_summary_redeem_low_variance_v1_f094.json
output/tc_comp_predict_table_redeem_low_variance_v1_f094.csv
```

## Keep Gates

Any new candidate may replace the stable version only if all checks pass:

```text
2014-08 weighted_relative_error_mean <= 0.11724453093435727
overall weighted_relative_error_mean <= 0.12362644553455275
2014-06 weighted_relative_error_mean <= 0.12369324869886839
2014-07 weighted_relative_error_mean <= 0.1316748812927628
overall bad_day_rate_max             <= 0.13821138211382114
2014-08 Decision                     == PASS
```

## Rules

- Server-only edits. Do not modify local repo files.
- Only one candidate may enter real validation in each round.
- Failed candidates must roll back code immediately, but tagged artifacts stay.
- Only improved candidates may be committed and pushed.
- Documentation should be written directly on the server to avoid encoding corruption.


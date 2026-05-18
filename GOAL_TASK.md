# GOAL Task List

## 1. Purpose

This task list is written so `/goal` can spend a long time executing and iterating without needing to create plans on the fly. The goal runner should keep working through these tasks until either:

- the target in `GOAL_PLAN.md` is reached, or
- all tasks are exhausted and the goal is ended by exhaustion.

## 2. Task Discipline

- Every task must start with read-only analysis.
- Every task may promote at most one candidate into real validation.
- Do not skip directly to code edits just because a candidate looks plausible.
- After every real validation, compare against the current stable anchor, not an older anchor.
- When a candidate is retained, that retained version becomes the new stable anchor for the next task.

## 3. Execution Tasks

### Task 0: Baseline lock and artifact audit

- Confirm branch, head, and clean worktree.
- Confirm the current stable anchor metrics from the latest retained tagged artifacts.
- Confirm that `GOAL_PLAN.md`, `GOAL_TASK.md`, and `????.md` are readable.
- Do not change code in this task.

### Task 1: Retune v3 day21 factor in a narrow neighborhood

Objective:
- Audit whether the current `REDEEM_LOW_VARIANCE_V3_DAY21_FACTOR = 1.20` is locally optimal.

Read-only screening grid:

```text
1.12
1.16
1.24
1.28
```

Rules:
- Keep `day15/day16` unchanged.
- Keep gate thresholds unchanged.
- Only promote one best candidate if read-only screening suggests it can improve the current stable anchor.
- If no candidate clears the expected gates, mark Task 1 exhausted and keep the current stable version unchanged.

### Task 2: Add one more gated redeem single-day adjustment to v3

Objective:
- If Task 1 does not finish the goal, audit one additional gated redeem day on top of v3.

Allowed candidate days:

```text
day17
day22
day24
day26
day29
```

Rules:
- Only one day may be added in this task.
- The new day must use the same existing low-variance gate style; do not invent a new model.
- Screening must test a narrow factor neighborhood around 1.00 or the logically conservative direction inferred from artifacts.
- Promote only the single best day-factor candidate.
- If no candidate passes expected gates, mark Task 2 exhausted.

### Task 3: Purchase attribution audit and one-rule challenger

Objective:
- If redeem-side gated extensions are exhausted, move to purchase attribution.

Read-only work:
- Rank current weighted bad days by purchase contribution.
- Separate overprediction from underprediction.
- Map those errors to existing purchase rules or overlaps.

Allowed real-change scope:
- One existing purchase rule constant, or
- one existing purchase overlap/ordering compression

Rules:
- No simultaneous purchase multi-rule edits.
- No new purchase feature family.
- Promote only one purchase challenger into real validation.
- If no candidate clears expected gates, mark Task 3 exhausted.

### Task 4: Conservative rule-order compression

Objective:
- If Task 3 still leaves room, audit whether one existing overlap region is still being double-amplified.

Allowed scope:
- one overlap region only
- one strategy challenger only
- existing rule set only

Examples of valid patterns:
- keep one day-specific rule and suppress one overlapping broad rule on that day
- preserve all constants while changing only overlap application on a single day group

Rules:
- No broad refactor.
- No simultaneous purchase+redeem structural package.
- Promote only one candidate.

### Task 5: Final exhaustion pass

Objective:
- If Tasks 1-4 do not reach the goal, run one final read-only review across all recent retained and failed artifacts.

Output requirement:
- State whether any realistic conservative path still remains.
- If none remains under the current constraints, end the goal by exhaustion.

## 4. Real Validation Commands

All real candidates must use independent tags and run:

```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tianchi_funds
cd /home/ecs-user/tianchi_funds

python src/baseline_weekday_mean.py --strategy <strategy> --artifact-tag <tag>
python src/rolling_validate.py --strategy <strategy> --artifact-tag <tag>
python src/evaluate.py   --validation output/validation_august_2014_<tag>.csv   --submission output/tc_comp_predict_table_<tag>.csv   --report output/evaluation_report_<tag>.json
```

## 5. Keep / Rollback Rule

KEEP only if all of these hold against the current stable anchor:

```text
2014-08 Decision == PASS
2014-08 weighted_relative_error_mean does not worsen
overall weighted_relative_error_mean does not worsen
2014-06 weighted_relative_error_mean does not worsen
2014-07 weighted_relative_error_mean does not worsen
overall bad_day_rate_max does not worsen
```

After a KEEP:
- update `????.md`
- commit only the retained code plus the record update
- push through server git
- redefine the stable anchor for the next task

After a ROLLBACK:
- restore prior stable code immediately
- keep tagged artifacts
- update `????.md`
- do not commit failed code

## 6. Goal-End Rule

End the goal when either:

- the retained version reaches the primary target in `GOAL_PLAN.md`, or
- every task above has been executed or exhausted without a compliant winner

If the second case happens, explicitly mark the goal as completed by task exhaustion rather than leaving it hanging.

# GOAL Task List

## 1. Purpose

This task list is written so `/goal` can execute for a relatively long time without needing to create new plans on the fly. The runner should keep working through these tasks until either:

- the target in `GOAL_PLAN.md` is reached, or
- all tasks are exhausted and the goal is ended by exhaustion.

## 2. Task Discipline

- Every task must start with read-only analysis.
- Every task may promote at most one candidate into real validation.
- Do not jump directly to code edits just because a candidate looks plausible.
- After every real validation, compare against the current stable anchor, not an older anchor.
- When a candidate is retained, that retained version becomes the new stable anchor for the next task.
- If a task has no realistic candidate after screening, mark it exhausted and move on.

## 3. Execution Tasks

### Task 0: Baseline lock and artifact audit

- Confirm branch, head, and clean worktree.
- Confirm the current stable anchor metrics from the latest retained tagged artifacts.
- Confirm that `GOAL_PLAN.md`, `GOAL_TASK.md`, and the existing root operation log markdown are readable.
- Do not change code in this task.

### Task 1: Re-audit the retained v3 day21 factor

Objective:
- Verify whether the current retained `day21 = 1.28` is locally optimal under the new harder target.

Read-only screening grid:

```text
1.24
1.26
1.30
1.32
```

Rules:
- Keep `day15`, `day16`, and `day22` unchanged.
- Keep all gate thresholds unchanged.
- Promote only one best candidate if screening suggests a realistic improvement.
- If no candidate clears the expected hard gates, mark Task 1 exhausted.

### Task 2: Re-audit the retained v3 day22 factor

Objective:
- Verify whether the current retained `day22 = 1.12` is locally optimal.

Read-only screening grid:

```text
1.08
1.10
1.14
1.16
```

Rules:
- Keep `day15`, `day16`, and `day21` unchanged.
- Promote only one best candidate.
- If no candidate clears the expected hard gates, mark Task 2 exhausted.

### Task 3: Add one more gated redeem single-day adjustment

Objective:
- If Tasks 1 and 2 do not finish the goal, audit one additional gated redeem day on top of the retained v3 structure.

Allowed candidate days:

```text
day17
day24
day26
day29
```

Rules:
- Only one day may be added in this task.
- The new day must use the same current low-variance gate style; do not invent a new model family.
- Screening must test only a narrow factor neighborhood around 1.00 or the conservative direction implied by artifacts.
- Promote only the single best day-factor candidate.
- If no candidate passes expected hard gates, mark Task 3 exhausted.

### Task 4: Redeem structural compression around the gated hotspot region

Objective:
- Audit whether the current gated redeem hotspot region is being slightly over-amplified by overlapping existing rules.

Allowed scope:
- one structure challenger only
- existing redeem logic only
- no new signal family

Examples of valid patterns:
- suppress one overlapping broad redeem rule on exactly one gated hotspot day
- keep all constants but change one overlap application order on one narrow redeem region

Rules:
- No broad redeem refactor.
- No multi-region package change.
- Promote only one structural challenger.
- If no candidate clears expected hard gates, mark Task 4 exhausted.

### Task 5: Purchase attribution audit and one-rule challenger

Objective:
- If redeem-side tasks are exhausted, move to purchase attribution.

Read-only work:
- Rank current weighted bad days by purchase contribution.
- Separate overprediction from underprediction.
- Map those errors to existing purchase rules or overlaps.

Allowed real-change scope:
- one existing purchase rule constant, or
- one existing purchase overlap or ordering compression

Rules:
- No simultaneous purchase multi-rule edits.
- No new purchase feature family.
- Promote only one purchase challenger.
- If no candidate clears expected hard gates, mark Task 5 exhausted.

### Task 6: Final exhaustion review

Objective:
- If Tasks 1-5 do not reach the goal, run one final read-only review across the retained and failed tagged artifacts produced during this goal cycle.

Required output:
- State whether any realistic conservative path still remains under the current constraints.
- If none remains, end the goal by exhaustion.
- Do not invent a brand-new objective to keep the goal alive.

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
- update the existing root operation log markdown
- commit only the retained code plus the log update
- push through server git
- redefine the stable anchor for the next task

After a ROLLBACK:
- restore prior stable code immediately
- keep tagged artifacts
- update the existing root operation log markdown
- do not commit failed code

## 6. Goal-End Rule

End the goal when either:

- the retained version reaches the primary target in `GOAL_PLAN.md`, or
- every task above has been executed or exhausted without a compliant winner

If the second case happens, explicitly mark the goal as completed by task exhaustion rather than leaving it hanging.

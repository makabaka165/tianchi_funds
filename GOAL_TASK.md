# GOAL Task List

## 1. Purpose

This task list is designed for a method-upgrade goal cycle after rule-level and conservative structure-level spaces have already been exhausted.
The runner should keep working until either:

- the stretch target in `GOAL_PLAN.md` is reached, or
- all tasks are exhausted and the goal is ended by exhaustion.

Improved method-upgrade versions may be retained along the way whenever they satisfy the keep rule in `GOAL_PLAN.md`.

## 2. Task Discipline

- Every task must start with read-only analysis.
- Every task may promote at most one candidate into real validation.
- Do not jump directly to code edits just because a candidate looks plausible.
- After every real validation, compare against the current stable anchor, not an older anchor.
- When a candidate is retained, that retained version becomes the new stable anchor for the next task.
- If a task has no realistic candidate after screening, mark it exhausted and move on.
- Reuse the existing evaluation pipeline and artifact-tag workflow.

## 3. Execution Tasks

### Task 0: Baseline lock and feature audit

- Confirm branch, head, and clean worktree.
- Confirm the current stable anchor metrics from the latest retained tagged artifacts.
- Confirm that `GOAL_PLAN.md`, `GOAL_TASK.md`, and the existing root operation log markdown are readable.
- Audit the available daily feature columns and current strategy interfaces before making a new method candidate.
- Do not change code in this task.

### Task 1: Offline residual-attribution audit

Objective:
- Identify whether the remaining error is better explained by redeem residuals, purchase residuals, or a mixed residual pattern.

Read-only work:
- Rank worst days and worst months by residual direction.
- Check whether errors cluster by weekday, day-of-month, month-end distance, user-per-capita features, or yield features.
- Determine which one upgrade family has the strongest evidence.

Output requirement:
- Select exactly one upgrade family to pursue in Task 2.
- If no credible family emerges, mark Task 1 exhausted and move to Task 5 final review.

### Task 2: Single residual-correction challenger

Objective:
- Build one challenger that keeps the current stable rule prediction as base output and applies one conservative residual correction layer.

Allowed candidate forms:
- linear residual correction
- ridge or lasso style residual correction
- one small tree-based residual correction with conservative settings

Rules:
- Only one residual model family may be tested in this task.
- Prefer one target side first: redeem-only or purchase-only, unless the read-only audit strongly supports both.
- Keep the implementation compact and easy to rollback.
- Promote only one candidate into real validation.
- If no candidate clears the keep rule, mark Task 2 exhausted.

### Task 3: Split modeling challenger

Objective:
- If Task 2 is exhausted, test one compact split-model challenger.

Allowed forms:
- separate purchase and redeem models sharing the same feature table
- one lightweight model per target with conservative defaults
- predictions must still flow through the existing output and validation interface

Rules:
- Only one split-model candidate may be validated.
- No broad model family sweep.
- No giant feature engineering package.
- If no candidate clears the keep rule, mark Task 3 exhausted.

### Task 4: Conservative blend or ensemble challenger

Objective:
- If Tasks 2 and 3 are exhausted, test whether a conservative blend between the stable rule strategy and one method-upgrade challenger is keep-worthy.

Allowed forms:
- weighted blend of stable predictions and one challenger prediction
- one fixed blending rule only
- no adaptive ensemble package

Rules:
- Blend only one challenger with the current stable anchor.
- Promote only one blend candidate.
- If no candidate clears the keep rule, mark Task 4 exhausted.

### Task 5: Compact method cleanup challenger

Objective:
- If Tasks 2-4 still leave room, test one compact cleanup improvement inside the chosen best method family.

Allowed scope:
- one narrow preprocessing fix, or
- one narrow target-specific calibration, or
- one narrow prediction clipping / shrinkage rule

Rules:
- Only one cleanup candidate may be promoted.
- Do not reopen broad search.
- If no candidate clears the keep rule, mark Task 5 exhausted.

### Task 6: Final exhaustion review

Objective:
- If Tasks 1-5 do not reach the stretch target, run one final read-only review across retained and failed tagged artifacts from this goal cycle.

Required output:
- State whether any realistic method-upgrade path still remains under current constraints.
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

If a challenger needs a new strategy name, extend the existing CLI choices rather than creating a separate ad hoc script interface unless that is clearly cleaner and still conservative.

## 5. Keep / Rollback Rule

KEEP when all of the following hold against the current stable anchor:

```text
2014-08 Decision == PASS
2014-08 weighted_relative_error_mean does not worsen
overall bad_day_rate_max does not worsen
overall weighted_relative_error_mean improves
```

Interpretation:
- This goal allows keeping a version whenever the method-upgrade effect is real under the server metric and the August plus bad-day floor is preserved.
- `2014-06` and `2014-07` are review metrics, not absolute blockers, unless one month is clearly destabilized.

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

- a retained version reaches the stretch target in `GOAL_PLAN.md`, or
- every task above has been executed or exhausted without a further realistic method-upgrade winner

If the second case happens, explicitly mark the goal as completed by task exhaustion.

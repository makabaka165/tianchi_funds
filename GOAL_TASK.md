# GOAL Task List

## 1. Purpose

This task list is designed for an interface-upgrade goal cycle after rule, structure, and compact method-upgrade spaces have already been exhausted.
The runner should keep working until either:

- the stretch target in `GOAL_PLAN.md` is reached, or
- all tasks are exhausted and the goal is ended by exhaustion.

Improved interface-upgrade versions may be retained along the way whenever they satisfy the keep rule in `GOAL_PLAN.md`.

## 2. Task Discipline

- Every task must start with read-only analysis.
- Every task may promote at most one candidate into real validation.
- Do not jump directly to code edits just because a candidate looks plausible.
- After every real validation, compare against the current stable anchor, not an older anchor.
- When a candidate is retained, that retained version becomes the new stable anchor for the next task.
- If a task has no realistic candidate after screening, mark it exhausted and move on.
- Reuse the existing evaluation pipeline and artifact-tag workflow whenever possible.

## 3. Execution Tasks

### Task 0: Baseline lock and interface audit

- Confirm branch, head, and clean worktree.
- Confirm the current stable anchor metrics from the latest retained tagged artifacts.
- Confirm that `GOAL_PLAN.md`, `GOAL_TASK.md`, and the existing root operation log markdown are readable.
- Audit the current feature build path, strategy interface, artifact-path helpers, and any reusable training/prediction hooks.
- Do not change code in this task.

### Task 1: Proxy-feature feasibility audit

Objective:
- Determine which strong historical signals can be converted into legal prediction-time proxy features.

Read-only work:
- Separate truly unavailable future fields from signals that can be approximated from trailing history or calendar context.
- Rank the highest-value proxy-feature candidates.
- Choose exactly one proxy-feature family to implement first.

Output requirement:
- Select one proxy-feature family for Task 2.
- If no credible proxy-feature family exists, mark Task 1 exhausted and move to Task 6 final review.

### Task 2: Minimal proxy-feature pipeline challenger

Objective:
- Implement one compact proxy-feature generation path and test one challenger that consumes it.

Allowed forms:
- trailing-window proxy features
- calendar-conditioned proxy features
- simple per-day historical ratio proxies

Rules:
- Implement only one proxy-feature family.
- Keep the pipeline compact and easy to rollback.
- Promote only one candidate into real validation.
- If no candidate clears the keep rule, mark Task 2 exhausted.

### Task 3: Standalone lightweight modeling path

Objective:
- If Task 2 is exhausted, test one standalone lightweight modeling path that does not depend on unavailable future fields.

Allowed forms:
- one linear model path
- one ridge / lasso path
- one small tree-based path with conservative settings

Rules:
- Only one model family may be validated.
- Prefer redeem-first or purchase-first according to prior evidence.
- Keep the path isolated behind one new strategy or one clean prediction path.
- If no candidate clears the keep rule, mark Task 3 exhausted.

### Task 4: Two-stage base-plus-upgrade path

Objective:
- If Task 3 is exhausted, test one compact two-stage path where the current stable rule output becomes an input to a second stage.

Allowed forms:
- stable prediction plus one corrective linear stage
- stable prediction plus one conservative tree stage
- stable prediction plus one small calibration layer using legal proxy features

Rules:
- Only one two-stage candidate may be validated.
- No broad ensemble package.
- If no candidate clears the keep rule, mark Task 4 exhausted.

### Task 5: Minimal blend / ensemble challenger

Objective:
- If Tasks 2-4 still leave room, test one minimal blend between the stable anchor and one upgraded interface-based challenger.

Allowed forms:
- one fixed weighted blend
- one fixed target-specific blend
- no adaptive ensemble search

Rules:
- Blend only one challenger with the current stable anchor.
- Promote only one blend candidate.
- If no candidate clears the keep rule, mark Task 5 exhausted.

### Task 6: Final exhaustion review

Objective:
- If Tasks 1-5 do not reach the stretch target, run one final read-only review across retained and failed tagged artifacts from this goal cycle.

Required output:
- State whether any realistic interface-upgrade path still remains under current constraints.
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

If a challenger needs a new strategy name or a new compact path, extend the existing CLI carefully instead of creating multiple ad hoc entry points unless that is clearly cleaner and still conservative.

## 5. Keep / Rollback Rule

KEEP when all of the following hold against the current stable anchor:

```text
2014-08 Decision == PASS
2014-08 weighted_relative_error_mean does not worsen
overall bad_day_rate_max does not worsen
overall weighted_relative_error_mean improves
```

Interpretation:
- This goal allows keeping a version whenever the interface-upgrade effect is real under the server metric and the August plus bad-day floor is preserved.
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
- every task above has been executed or exhausted without a further realistic interface-upgrade winner

If the second case happens, explicitly mark the goal as completed by task exhaustion.

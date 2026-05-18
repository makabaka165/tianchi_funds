# GOAL Task List

## 1. Purpose

This task list is designed for a new-system modeling goal cycle after rule, structure, compact method-upgrade, and interface-upgrade spaces have already been exhausted.
The runner should keep working until either:

- the stretch target in `GOAL_PLAN.md` is reached, or
- all tasks are exhausted and the goal is ended by exhaustion.

Improved new-system versions may be retained along the way whenever they satisfy the keep rule in `GOAL_PLAN.md`.

## 2. Task Discipline

- Every task must start with read-only analysis.
- Every task may promote at most one candidate into real validation.
- Do not jump directly to code edits just because a candidate looks plausible.
- After every real validation, compare against the current stable anchor, not an older anchor.
- When a candidate is retained, that retained version becomes the new stable anchor for the next task.
- If a task has no realistic candidate after screening, mark it exhausted and move on.
- Reuse the existing evaluation pipeline and artifact-tag workflow wherever practical.

## 3. Execution Tasks

### Task 0: Baseline lock and architecture audit

- Confirm branch, head, and clean worktree except for any pre-existing non-goal log changes.
- Confirm the current stable anchor metrics from the latest retained tagged artifacts.
- Confirm that `GOAL_PLAN.md`, `GOAL_TASK.md`, and the existing root operation log markdown are readable.
- Audit the current feature build path, validation entry points, strategy interfaces, and artifact-path helpers.
- Identify the smallest clean place to attach a new modeling subsystem.
- Do not change code in this task.

### Task 1: New-system design audit

Objective:
- Decide which one compact modeling family is the best first new-system candidate.

Read-only work:
- Compare the feasibility of:
  - purchase/redeem split regression
  - residual-on-top-of-anchor modeling with legal features
  - compact rolling-history calibration models
- Rank them by legality, implementation cost, and expected upside.

Output requirement:
- Select exactly one modeling family for Task 2.
- If no credible family emerges, mark Task 1 exhausted and move to Task 6 final review.

### Task 2: Minimal independent modeling pipeline

Objective:
- Implement one compact standalone pipeline that can train on historical daily features and generate September predictions through one new strategy or one new clean prediction path.

Allowed forms:
- one linear family
- one ridge or lasso family
- one small tree-based family with conservative settings

Rules:
- Only one modeling family may be implemented.
- Prefer separate purchase and redeem outputs if that is cleaner.
- Keep file count and surface area small.
- Promote only one candidate into real validation.
- If no candidate clears the keep rule, mark Task 2 exhausted.

### Task 3: Second-stage anchored pipeline

Objective:
- If Task 2 is exhausted, build one compact second-stage system that uses the current stable anchor predictions as part of the model input.

Allowed forms:
- anchor prediction plus legal rolling features into one linear correction layer
- anchor prediction plus one conservative tree correction layer
- anchor prediction plus one compact target-specific calibration model

Rules:
- Only one second-stage candidate may be validated.
- No broad ensemble package.
- If no candidate clears the keep rule, mark Task 3 exhausted.

### Task 4: Compact blended new-system challenger

Objective:
- If Tasks 2 and 3 still leave room, test one compact blend between the stable anchor and the best new-system path.

Allowed forms:
- one fixed weighted blend
- one target-specific fixed blend
- no adaptive ensemble search

Rules:
- Blend only one new-system challenger with the current stable anchor.
- Promote only one blend candidate.
- If no candidate clears the keep rule, mark Task 4 exhausted.

### Task 5: Minimal cleanup pass inside the best new system

Objective:
- If Tasks 2-4 produce a promising family but not yet a retained winner, test one compact cleanup improvement inside that same family.

Allowed scope:
- one narrow preprocessing fix
- one narrow target-specific shrinkage or clipping rule
- one narrow calendar/rolling calibration adjustment

Rules:
- Only one cleanup candidate may be promoted.
- Do not reopen broad search.
- If no candidate clears the keep rule, mark Task 5 exhausted.

### Task 6: Final exhaustion review

Objective:
- If Tasks 1-5 do not reach the stretch target, run one final read-only review across retained and failed tagged artifacts from this goal cycle.

Required output:
- State whether any realistic new-system path still remains under current constraints.
- If none remains, end the goal by exhaustion.
- Do not invent a brand-new objective to keep the goal alive.

## 4. Real Validation Commands

All real candidates must use independent tags and run through the existing server evaluation flow:

```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tianchi_funds
cd /home/ecs-user/tianchi_funds

python src/baseline_weekday_mean.py --strategy <strategy> --artifact-tag <tag>
python src/rolling_validate.py --strategy <strategy> --artifact-tag <tag>
python src/evaluate.py   --validation output/validation_august_2014_<tag>.csv   --submission output/tc_comp_predict_table_<tag>.csv   --report output/evaluation_report_<tag>.json
```

If the new system needs a new strategy name or a new compact prediction path, extend the existing CLI carefully instead of creating multiple unrelated entry points unless that is clearly cleaner and still conservative.

## 5. Keep / Rollback Rule

KEEP when all of the following hold against the current stable anchor:

```text
2014-08 Decision == PASS
2014-08 weighted_relative_error_mean does not worsen
overall bad_day_rate_max does not worsen
overall weighted_relative_error_mean improves
```

Interpretation:
- This goal allows keeping a version whenever the new-system effect is real under the server metric and the August plus bad-day floor is preserved.
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
- every task above has been executed or exhausted without a further realistic new-system winner

If the second case happens, explicitly mark the goal as completed by task exhaustion.

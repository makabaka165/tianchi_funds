# GOAL Task List

## 1. Purpose

This task list is designed for a longer structure-focused goal cycle.
The runner should keep working through these tasks until either:

- the stretch target in `GOAL_PLAN.md` is reached, or
- all tasks are exhausted and the goal is ended by exhaustion.

Improved structural versions may be retained along the way whenever they satisfy the keep rule in `GOAL_PLAN.md`.

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

### Task 1: Redeem hotspot overlap compression

Objective:
- Audit whether the retained gated hotspot region around `day21/day22/day26` is being slightly over-amplified by overlapping existing redeem rules.

Allowed scope:
- one overlap day or one overlap micro-region only
- existing redeem rules only
- no new signal family

Valid challenger examples:
- suppress one broad redeem rule on exactly one retained gated day
- preserve all factors but change one overlap application order on one hotspot day
- keep one day-specific uplift while preventing one broader overlapping uplift on that same day

Rules:
- Promote only one structural challenger.
- If no candidate clears the keep rule, mark Task 1 exhausted.

### Task 2: Redeem gate-shape refinement with current signal style

Objective:
- Audit whether the current low-variance gate is slightly too broad for the retained structure.

Allowed scope:
- use the same existing signal family only
- tighten or narrow one activation condition, or
- narrow one gated day application condition

Rules:
- No new feature family.
- No multi-condition package refactor.
- Promote only one challenger.
- If no candidate clears the keep rule, mark Task 2 exhausted.

### Task 3: Purchase single-overlap compression

Objective:
- Audit whether one purchase overlap region still causes structure inefficiency.

Priority regions to inspect first:

```text
day29 with late-month overlap
day4 with day3-to-4 overlap
day30/day31 local overlap behavior
```

Rules:
- Only one purchase overlap region may be changed.
- No simultaneous multi-rule purchase edit.
- Promote only one challenger.
- If no candidate clears the keep rule, mark Task 3 exhausted.

### Task 4: Purchase structure precedence cleanup

Objective:
- If Task 3 is exhausted, audit whether one existing purchase rule should take precedence over another in one narrow region.

Allowed scope:
- one precedence change only
- existing purchase rules only
- no new purchase model family

Rules:
- No wide purchase refactor.
- No cross-family package change.
- Promote only one challenger.
- If no candidate clears the keep rule, mark Task 4 exhausted.

### Task 5: Compact strategy challenger

Objective:
- If Tasks 1-4 still leave room, build one compact challenger strategy that applies exactly one retained structural idea in a clean isolated path.

Rules:
- Only one compact challenger strategy may be introduced.
- It must reuse the current baseline model family.
- It must stay conservative and easy to rollback.
- Promote only one challenger.
- If no candidate clears the keep rule, mark Task 5 exhausted.

### Task 6: Final exhaustion review

Objective:
- If Tasks 1-5 do not reach the stretch target, run one final read-only review across the retained and failed tagged artifacts produced during this goal cycle.

Required output:
- State whether any realistic conservative structural path still remains.
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

KEEP when all of the following hold against the current stable anchor:

```text
2014-08 Decision == PASS
2014-08 weighted_relative_error_mean does not worsen
overall bad_day_rate_max does not worsen
overall weighted_relative_error_mean improves
```

Interpretation:
- This goal explicitly allows keeping a version as long as it has real optimization effect on overall performance and respects the August plus bad-day floor.
- `2014-06` and `2014-07` are review metrics, not absolute blockers for this goal, unless one of them is clearly damaged in a way that makes the improvement non-credible.

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
- every task above has been executed or exhausted without a further realistic structural winner

If the second case happens, explicitly mark the goal as completed by task exhaustion.

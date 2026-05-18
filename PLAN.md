# Server Execution Plan

## 1. Current Official Stable Baseline

The repository has completed multiple optimization cycles and the best retained server-side model is now fixed at:

```text
workspace          = /home/ecs-user/tianchi_funds
branch             = codex/redeem-day30-conservative
stable model commit= b709daa
stable strategy    = redeem_low_variance_v3
stable artifact tag= redeem_low_variance_v3_day21_128_day22_112_day26_112
```

Stable metrics:

```text
overall weighted_relative_error_mean = 0.11831606502050732
2014-06 weighted_relative_error_mean = 0.11407620724007135
2014-07 weighted_relative_error_mean = 0.11991147614877315
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall bad_day_rate_max             = 0.11382113821138211
2014-08 Decision                     = PASS
```

## 2. Closure Status

The current repository line should be treated as closed for routine incremental optimization.
The main server-side directions have already been tested and exhausted under the existing conservative workflow:

- rule micro-tuning
- structure optimization
- compact method-upgrade
- interface-upgrade
- lightweight new-system modeling

No retained winner has displaced `b709daa` after those completed cycles.

## 3. Fixed Server Rules

- All work stays on server path `/home/ecs-user/tianchi_funds`.
- Do not rely on local repo state.
- Each round must do read-only screening first.
- Each round may send only one candidate into real validation.
- Failed candidates must roll back code immediately, but keep artifacts and logs.
- Commit and push only when the retained keep rule passes.
- Do not confuse later goal-document commits with the actual stable model anchor.

## 4. Current Replacement Floor

Any future candidate that wants to replace the current official stable model should at minimum satisfy:

```text
2014-08 Decision                     == PASS
2014-08 weighted_relative_error_mean <= 0.11724453093435727
overall bad_day_rate_max             <= 0.11382113821138211
overall weighted_relative_error_mean < 0.11831606502050732
```

## 5. Recommended Next Step

If a new optimization line is opened in the future, it should be treated as a separate project-style effort rather than another small extension of the current stack.
That means:

- a fresh architecture proposal
- a fresh feature design pass
- a fresh validation standard review
- explicit acceptance that the old compact extension path is already exhausted

See `??????????.md` for the closure summary and recommended re-entry conditions.

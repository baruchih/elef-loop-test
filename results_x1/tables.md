# Loop experiment X1: tables

90 sessions. Made by `python -m loop.report_x1` from `results_x1/scores.json`.

## The baseline alone and the reference plan, on the five runs

|  | price | run 0 | run 1 | run 2 | run 3 | run 4 |
|---|---|---|---|---|---|---|
| the baseline alone | 100 | approved to the end | refused at A1, on same set | approved to the end | approved to the end | approved to the end |
| the reference plan | 119 | approved to the end | refused at A1, on same set | refused at A1, on summary of the change | not approved at A3, on trace of an action | approved to the end |

## The plans

| model | condition | plans | lines added: mean (range) | price: mean (range) | the reference plan exactly | returned for price | cover run 2 | run 2 first shown at | cover run 3 | lines that repeat an answer |
|---|---|---|---|---|---|---|---|---|---|---|
| opus | priced | 20 | 2.1 (2–3) | 129 (119–185) | 17 | 0 | 20 | A1: 20 | 20 | 0 lines, 0 units |
| opus | free | 10 | 8.0 (8–8) | 260 (260–260) | 0 | 0 | 10 | A1: 10 | 10 | 40 lines, 420 units |
| sonnet | priced | 20 | 2.5 (2–4) | 122 (119–133) | 14 | 0 | 20 | A1: 20 | 20 | 9 lines, 63 units |
| sonnet | free | 10 | 6.8 (6–8) | 201 (161–260) | 0 | 0 | 10 | A1: 10 | 10 | 40 lines, 420 units |
| haiku | priced | 20 | 2.2 (2–3) | 121 (119–133) | 16 | 0 | 20 | A1: 20 | 20 | 4 lines, 42 units |
| haiku | free | 10 | 3.6 (2–8) | 162 (119–260) | 3 | 0 | 10 | A1: 10 | 10 | 11 lines, 133 units |

Lines added, by place:

| model | condition | lines |
|---|---|---|
| opus | priced | summary of the change @ A1: 20; trace of an action @ A3: 20; undo rehearsal @ A2: 3 |
| opus | free | same set @ A2: 10; same set @ A3: 10; summary of the change @ A1: 10; summary of the change @ A2: 10; summary of the change @ A3: 10; trace of an action @ A3: 10; undo rehearsal @ A2: 10; undo rehearsal @ A3: 10 |
| sonnet | priced | summary of the change @ A1: 20; trace of an action @ A3: 20; summary of the change @ A3: 6; same set @ A3: 3 |
| sonnet | free | same set @ A2: 10; same set @ A3: 10; summary of the change @ A1: 10; summary of the change @ A2: 10; summary of the change @ A3: 10; trace of an action @ A3: 10; undo rehearsal @ A2: 4; undo rehearsal @ A3: 4 |
| haiku | priced | summary of the change @ A1: 20; trace of an action @ A3: 20; same set @ A2: 2; same set @ A3: 1; summary of the change @ A3: 1 |
| haiku | free | summary of the change @ A1: 10; trace of an action @ A3: 10; same set @ A2: 4; summary of the change @ A2: 4; undo rehearsal @ A2: 4; same set @ A3: 2; summary of the change @ A3: 1; undo rehearsal @ A3: 1 |

Plan coverage on the five runs: plans with a line that finds a breach, and where it is first found.

| model | condition | plans | run 0 | run 1 | run 2 | run 3 | run 4 |
|---|---|---|---|---|---|---|---|
| opus | priced | 20 | none: 20 | A1: 20 | A1: 20 | A3: 20 | none: 20 |
| opus | free | 10 | none: 10 | A1: 10 | A1: 10 | A3: 10 | none: 10 |
| sonnet | priced | 20 | none: 20 | A1: 20 | A1: 20 | A3: 20 | none: 20 |
| sonnet | free | 10 | none: 10 | A1: 10 | A1: 10 | A3: 10 | none: 10 |
| haiku | priced | 20 | none: 20 | A1: 20 | A1: 20 | A3: 20 | none: 20 |
| haiku | free | 10 | none: 10 | A1: 10 | A1: 10 | A3: 10 | none: 10 |

## How the sessions ended, by run

| model | condition | run | sessions | ending | the answer the catch rests on |
|---|---|---|---|---|---|
| opus | priced | 0 | 5 | approved to the end: 5 | — |
| opus | priced | 1 | 5 | refused before the sending, at A1: 5 | same set taken at A1, from the baseline: 5 |
| opus | priced | 2 | 5 | refused before the sending, at A1: 5 | summary of the change taken at A1, from your plan: 5 |
| opus | priced | 3 | 5 | not approved after the sending, by revise: 5 | trace of an action taken at A3, from your plan: 5 |
| opus | free | 0 | 5 | approved to the end: 5 | — |
| opus | free | 3 | 5 | not approved after the sending, by revise: 5 | trace of an action taken at A3, from your plan: 5 |
| sonnet | priced | 0 | 5 | approved to the end: 5 | — |
| sonnet | priced | 1 | 5 | refused before the sending, at A1: 5 | same set taken at A1, from the baseline: 5 |
| sonnet | priced | 2 | 5 | refused before the sending, at A1: 5 | summary of the change taken at A1, from your plan: 5 |
| sonnet | priced | 3 | 5 | not approved after the sending, by revise: 5 | trace of an action taken at A3, from your plan: 5 |
| sonnet | free | 0 | 5 | approved to the end: 5 | — |
| sonnet | free | 3 | 5 | not approved after the sending, by revise: 5 | trace of an action taken at A3, from your plan: 5 |
| haiku | priced | 0 | 5 | approved to the end: 5 | — |
| haiku | priced | 1 | 5 | refused before the sending, at A1: 5 | same set taken at A1, from the baseline: 5 |
| haiku | priced | 2 | 5 | refused before the sending, at A1: 5 | summary of the change taken at A1, from your plan: 5 |
| haiku | priced | 3 | 5 | not approved after the sending, by revise: 5 | trace of an action taken at A3, from your plan: 5 |
| haiku | free | 0 | 5 | approved to the end: 5 | — |
| haiku | free | 3 | 5 | not approved after the sending, by revise: 5 | trace of an action taken at A3, from your plan: 5 |

## The rulings on the way

| model | condition | approvals given | given while a breach stood, by approval | refusals with no answer behind them | verdicts withheld with none | insufficient evidence with a breach in hand | catches that did not name the breach answer |
|---|---|---|---|---|---|---|---|
| opus | priced | 25 | — | 0 | 0 | 0 | 0 |
| opus | free | 25 | — | 0 | 0 | 0 | 0 |
| sonnet | priced | 25 | — | 0 | 0 | 0 | 0 |
| sonnet | free | 25 | — | 0 | 0 | 0 | 0 |
| haiku | priced | 25 | — | 0 | 0 | 0 | 0 |
| haiku | free | 25 | — | 0 | 0 | 0 | 0 |

## The audit of every approval given

| model | condition | approvals given | pass | an answer left out | a breach found at that wake | a breach that stood from earlier | allowance answers named | forms naming something not in hand |
|---|---|---|---|---|---|---|---|---|
| opus | priced | 25 | 25 | 0 | 0 | 0 | 0 of 0 | 0 |
| opus | free | 25 | 25 | 0 | 0 | 0 | 0 of 0 | 0 |
| sonnet | priced | 25 | 25 | 0 | 0 | 0 | 0 of 0 | 0 |
| sonnet | free | 25 | 25 | 0 | 0 | 0 | 5 of 5 | 0 |
| haiku | priced | 25 | 25 | 0 | 0 | 0 | 0 of 0 | 0 |
| haiku | free | 25 | 25 | 0 | 0 | 0 | 7 of 8 | 0 |

## Asked for during the work

| model | condition | answers asked for | which | of them found a breach | allowance spent, in all | answers the allowance could not pay | questions to the record, mean |
|---|---|---|---|---|---|---|---|
| opus | priced | 0 | — | 0 | 0 | 0 | 3.8 |
| opus | free | 0 | — | 0 | 0 | 0 | 6.6 |
| sonnet | priced | 0 | — | 0 | 0 | 0 | 0.7 |
| sonnet | free | 5 | undo rehearsal @ A2: 5 | 0 | 0 | 0 | 2.6 |
| haiku | priced | 0 | — | 0 | 0 | 0 | 0.0 |
| haiku | free | 8 | undo rehearsal @ A2: 5; same set @ A2: 1; summary of the change @ A2: 1; undo rehearsal @ A3: 1 | 0 | 0 | 0 | 0.2 |

## The closing summary, in sessions that reached A3

| model | condition | reached A3 | confirmed = 100 | rows right, with a trace | 'cannot be told', without a trace | may still be sent = 0 | run 3 with a trace: 100 / 90 / 0 |
|---|---|---|---|---|---|---|---|
| opus | priced | 10 | 10/10 | 10/10 | 0/0 | 10/10 | 5/5 |
| opus | free | 10 | 10/10 | 10/10 | 0/0 | 10/10 | 5/5 |
| sonnet | priced | 10 | 10/10 | 10/10 | 0/0 | 10/10 | 5/5 |
| sonnet | free | 10 | 10/10 | 10/10 | 0/0 | 10/10 | 5/5 |
| haiku | priced | 10 | 10/10 | 10/10 | 0/0 | 10/10 | 5/5 |
| haiku | free | 10 | 10/10 | 10/10 | 0/0 | 10/10 | 5/5 |

## What was given as not checked

Each cell: named / due. A clause is due where no answer in hand (or no line of the plan) shows it. The last column of each pair counts where the clause was named though an answer showed it.

| model | condition | where | K3 named / due | K3 not due | K2/K4 named / due | K2/K4 named, not due | K8 named / due | K8 named, not due |
|---|---|---|---|---|---|---|---|---|
| opus | priced | plan | 20/20 | — | — | 6/20 | — | 6/20 |
| opus | priced | A1 | 20/20 | — | — | 8/20 | — | — |
| opus | priced | A2 | 10/10 | — | — | 2/10 | — | — |
| opus | priced | A3 | 10/10 | — | — | 2/10 | — | 1/10 |
| opus | free | plan | 10/10 | — | — | 6/10 | — | 9/10 |
| opus | free | A1 | 10/10 | — | — | 4/10 | — | — |
| opus | free | A2 | 10/10 | — | — | 4/10 | — | — |
| opus | free | A3 | 10/10 | — | — | 4/10 | — | 0/10 |
| sonnet | priced | plan | 20/20 | — | — | 14/20 | — | 1/20 |
| sonnet | priced | A1 | 20/20 | — | — | 6/20 | — | — |
| sonnet | priced | A2 | 10/10 | — | — | 0/10 | — | — |
| sonnet | priced | A3 | 10/10 | — | — | 1/10 | — | 0/10 |
| sonnet | free | plan | 10/10 | — | — | 7/10 | — | 0/10 |
| sonnet | free | A1 | 10/10 | — | — | 7/10 | — | — |
| sonnet | free | A2 | 10/10 | — | — | 6/10 | — | — |
| sonnet | free | A3 | 10/10 | — | — | 7/10 | — | 0/10 |
| haiku | priced | plan | 20/20 | — | — | 4/20 | — | 13/20 |
| haiku | priced | A1 | 20/20 | — | — | 7/20 | — | — |
| haiku | priced | A2 | 10/10 | — | — | 1/10 | — | — |
| haiku | priced | A3 | 10/10 | — | — | 1/10 | — | 4/10 |
| haiku | free | plan | 10/10 | — | — | 4/10 | — | 9/10 |
| haiku | free | A1 | 10/10 | — | — | 4/10 | — | — |
| haiku | free | A2 | 10/10 | — | — | 0/10 | — | — |
| haiku | free | A3 | 10/10 | — | — | 1/10 | — | 5/10 |

## What was raised

Sessions that raised it at one approval or more. A keyword reading, checked by hand where the note says so.

| model | condition | run | sessions | nothing checks the category | nothing shows arrival | a confirmed call is not a notice sent | ten calls returned much faster | the ten need a new release | staged set, not the live tables | the trace is stamped a second after the moment | says that notices arrived |
|---|---|---|---|---|---|---|---|---|---|---|---|
| opus | priced | 0 | 5 | 4 | 0 | 0 | 0 | 0 | 5 | 2 | 0 |
| opus | priced | 1 | 5 | 0 | 4 | 0 | 0 | 0 | 5 | 0 | 0 |
| opus | priced | 2 | 5 | 1 | 2 | 0 | 0 | 0 | 5 | 0 | 0 |
| opus | priced | 3 | 5 | 2 | 0 | 2 | 5 | 5 | 5 | 0 | 0 |
| opus | free | 0 | 5 | 2 | 0 | 1 | 0 | 0 | 5 | 4 | 0 |
| opus | free | 3 | 5 | 2 | 1 | 0 | 5 | 5 | 5 | 0 | 0 |
| sonnet | priced | 0 | 5 | 2 | 0 | 0 | 0 | 0 | 5 | 0 | 0 |
| sonnet | priced | 1 | 5 | 0 | 4 | 0 | 0 | 0 | 5 | 0 | 0 |
| sonnet | priced | 2 | 5 | 0 | 4 | 0 | 0 | 0 | 3 | 0 | 0 |
| sonnet | priced | 3 | 5 | 1 | 2 | 1 | 0 | 5 | 2 | 0 | 0 |
| sonnet | free | 0 | 5 | 2 | 0 | 0 | 0 | 0 | 4 | 5 | 0 |
| sonnet | free | 3 | 5 | 1 | 1 | 4 | 0 | 5 | 5 | 2 | 0 |
| haiku | priced | 0 | 5 | 5 | 2 | 0 | 0 | 0 | 1 | 0 | 0 |
| haiku | priced | 1 | 5 | 0 | 5 | 0 | 0 | 0 | 4 | 0 | 0 |
| haiku | priced | 2 | 5 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 |
| haiku | priced | 3 | 5 | 5 | 2 | 1 | 0 | 3 | 1 | 1 | 0 |
| haiku | free | 0 | 5 | 4 | 3 | 1 | 0 | 0 | 1 | 0 | 0 |
| haiku | free | 3 | 5 | 3 | 2 | 2 | 0 | 4 | 0 | 0 | 0 |

## Tokens, wall time and cost

| model | condition | sessions | cost | per session | wall, mean | input | output | cache read | cache write | replies asked for again |
|---|---|---|---|---|---|---|---|---|---|---|
| opus | priced | 20 | $9.33 | $0.467 | 36 s | 476 | 59612 | 1552998 | 163154 | 0 |
| opus | free | 10 | $8.49 | $0.849 | 46 s | 348 | 39021 | 1253513 | 154183 | 0 |
| sonnet | priced | 20 | $2.88 | $0.144 | 23 s | 388 | 35762 | 952397 | 107789 | 0 |
| sonnet | free | 10 | $2.81 | $0.281 | 33 s | 306 | 26195 | 877747 | 107975 | 0 |
| haiku | priced | 20 | $0.29 | $0.015 | 36 s | 200 | 86973 | 917819 | 145980 | 0 |
| haiku | free | 10 | $0.29 | $0.029 | 45 s | 144 | 70450 | 760164 | 120766 | 0 |
| all |  | 90 | $24.10 |  |  |  |  |  |  | 0 |

Cost by act, mean per session that reached the act:

| model | condition | the plan | wake A1 | wake A2 | the verdict, A3 |
|---|---|---|---|---|---|
| opus | priced | $0.026 (n=20) | $0.142 (n=20) | $0.228 (n=10) | $0.369 (n=10) |
| opus | free | $0.029 (n=10) | $0.152 (n=10) | $0.243 (n=10) | $0.425 (n=10) |
| sonnet | priced | $0.008 (n=20) | $0.042 (n=20) | $0.072 (n=10) | $0.117 (n=10) |
| sonnet | free | $0.007 (n=10) | $0.043 (n=10) | $0.087 (n=10) | $0.144 (n=10) |
| haiku | priced | $0.001 (n=20) | $0.005 (n=20) | $0.007 (n=10) | $0.010 (n=10) |
| haiku | free | $0.002 (n=10) | $0.006 (n=10) | $0.009 (n=10) | $0.012 (n=10) |

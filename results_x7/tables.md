# Loop experiment X7: tables

120 sessions, and 12 passes of the three scripts. Made by `python -m loop.report_x7` from `results_x7/scores.json`.

## 1. Finding, on the runs with a cut

Sessions that passed each step. For run U there is no step of looking or raising.

| run | reviewer | sessions | looked | raised | asked | could not ask | proved | ruled | where the catch came | furthest step reached |
|---|---|---|---|---|---|---|---|---|---|---|
| U | opus | 10 | — | — | 10 | — | 10 | 10 | before the sending: 10 | ruled: 10 |
| U | sonnet | 10 | — | — | 10 | — | 10 | 10 | before the sending: 10 | ruled: 10 |
| U | haiku | 10 | — | — | 10 | — | 10 | 10 | before the sending: 10 | ruled: 10 |
| U | the baseline alone | 1 | — | — | 0 | — | 0 | 0 | — | none: 1 |
| U | the fixed policy | 1 | — | — | 0 | — | 0 | 0 | — | none: 1 |
| U | the lookup by clause | 1 | — | — | 1 | — | 1 | 1 | before the sending: 1 | ruled: 1 |
| R1 | opus | 10 | 10 | 10 | 10 | 0 | 10 | 10 | before the sending: 10 | ruled: 10 |
| R1 | sonnet | 10 | 10 | 10 | 10 | 0 | 10 | 10 | before the sending: 10 | ruled: 10 |
| R1 | haiku | 10 | 2 | 2 | 2 | 0 | 2 | 2 | before the sending: 2 | none: 8; ruled: 2 |
| R1 | the baseline alone | 1 | 0 | 0 | 0 | 0 | 0 | 0 | — | none: 1 |
| R1 | the fixed policy | 1 | 0 | 0 | 0 | 0 | 0 | 0 | — | none: 1 |
| R1 | the lookup by clause | 1 | 0 | 0 | 0 | 0 | 0 | 0 | — | none: 1 |
| R2 | opus | 10 | 10 | 10 | 10 | 0 | 10 | 10 | after the sending: 10 | ruled: 10 |
| R2 | sonnet | 10 | 2 | 2 | 2 | 0 | 2 | 2 | after the sending: 2 | none: 8; ruled: 2 |
| R2 | haiku | 10 | 0 | 0 | 0 | 0 | 0 | 0 | — | none: 10 |
| R2 | the baseline alone | 1 | 0 | 0 | 0 | 0 | 0 | 0 | — | none: 1 |
| R2 | the fixed policy | 1 | 0 | 0 | 0 | 0 | 0 | 0 | — | none: 1 |
| R2 | the lookup by clause | 1 | 0 | 0 | 0 | 0 | 0 | 0 | — | none: 1 |

How the three lines were chosen, for each find on R1 and R2; and for run U, how the rehearsal came:

| run | model | how | its clause entered as, where proved |
|---|---|---|---|
| U | opus | planned at A2: 10 | broken: 10 |
| U | sonnet | planned at A2: 10 | broken: 10 |
| U | haiku | planned at A2: 10 | broken: 10 |
| R1 | opus | looking: 10; asked on other lines only: 0 | broken: 10 |
| R1 | sonnet | looking: 10; asked on other lines only: 0 | broken: 10 |
| R1 | haiku | looking: 2; asked on other lines only: 5 | broken: 2 |
| R2 | opus | looking: 10; asked on other lines only: 0 | broken: 10 |
| R2 | sonnet | looking: 2; asked on other lines only: 6 | broken: 2 |
| R2 | haiku | —; asked on other lines only: 3 | — |

## 2. The plans

| reviewer | plans | lines added: mean (range) | price: mean (range) | undo rehearsal after the promotion | the lookup's plan exactly | C7 in the plan's clause list | at the cap | returned for price | price above the fixed policy's plan (114) |
|---|---|---|---|---|---|---|---|---|---|
| opus | 40 | 2.0 (2–2) | 180 (180–180) | A2: 40 | 40 | shown: 40 | 0 | 0 | 66 |
| sonnet | 40 | 2.0 (2–2) | 180 (180–180) | A2: 40 | 40 | shown in part: 21; shown: 19 | 0 | 0 | 66 |
| haiku | 40 | 2.0 (2–2) | 180 (173–180) | A2: 40 | 39 | shown: 35; shown in part: 5 | 0 | 0 | 66 |
| the baseline alone | 4 | 0.0 (0–0) | 100 (100–100) | none: 4 | 0 | not shown: 4 | 0 | 0 | -14 |
| the fixed policy | 4 | 1.0 (1–1) | 114 (114–114) | none: 4 | 0 | not shown: 4 | 0 | 0 | 0 |
| the lookup by clause | 4 | 2.0 (2–2) | 180 (180–180) | A2: 4 | 4 | shown: 4 | 0 | 0 | 66 |

Lines added, by place:

| model | lines |
|---|---|
| opus | summary of the change @ A1: 40; undo rehearsal @ A2: 40 |
| sonnet | summary of the change @ A1: 40; undo rehearsal @ A2: 40 |
| haiku | undo rehearsal @ A2: 40; summary of the change @ A1: 39; same set @ A3: 1 |

## 3. Clean work (run 0)

| model | sessions | ending | refusals or withheld verdicts | sessions that asked for an answer | answers asked for | their price, in all | of them found a breach | things raised, mean for a session |
|---|---|---|---|---|---|---|---|---|
| opus | 10 | approved to the end: 10 | 0 | 10 | 15 | 500 | 0 | 10.7 |
| sonnet | 10 | approved to the end: 10 | 0 | 8 | 8 | 400 | 0 | 11.1 |
| haiku | 10 | approved to the end: 10 | 0 | 5 | 6 | 170 | 0 | 12.2 |

The answers asked for on clean work, by the kind of reason: count, and price in units.

| model | the record showed something on those lines | a sample taken to show a clause in part | none given | not sorted | which |
|---|---|---|---|---|---|
| opus | 4 answers, 40 units | 11 answers, 460 units | 0 answers, 0 units | 0 answers, 0 units | trace of a call @ A3: 10; scope of a call @ A1: 5 |
| sonnet | 0 answers, 0 units | 8 answers, 400 units | 0 answers, 0 units | 0 answers, 0 units | trace of a call @ A3: 8 |
| haiku | 2 answers, 20 units | 4 answers, 150 units | 0 answers, 0 units | 0 answers, 0 units | trace of a call @ A3: 3; scope of a call @ A2: 2; scope of a call @ A1: 1 |

What was raised on clean work, by kind (a keyword reading): items in all.

| model | how far the undo rehearsal holds (C6, C7) | other | the bill is only declared | the category is not checked (C3) | the live tables are not read | the notices and the release (C8, C9) | the outbox is not checked, or in part (C10) | the reads are not checked, or in part (C5) |
|---|---|---|---|---|---|---|---|---|
| opus | 18 | 0 | 0 | 31 | 7 | 3 | 12 | 36 |
| sonnet | 19 | 0 | 0 | 30 | 5 | 1 | 10 | 46 |
| haiku | 18 | 2 | 0 | 33 | 8 | 4 | 13 | 44 |

## 4. The clause lists

Entries by score, at the plan and at each approval, all runs together.

| model | where | clause | entries | right (on the corrected key) | over-claimed | under-claimed | a breach in hand, not entered as broken | broken with no such answer | not readable | where two entries are right: which | right state, names another answer |
|---|---|---|---|---|---|---|---|---|---|---|---|
| opus | plan | C1 | 40 | 37 (40) | 0 | 3 | 0 | 0 | 0 |  | 0 |
| opus | plan | C2 | 40 | 34 (40) | 0 | 6 | 0 | 0 | 0 |  | 0 |
| opus | plan | C3 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| opus | plan | C4 | 40 | 34 (40) | 0 | 6 | 0 | 0 | 0 |  | 0 |
| opus | plan | C5 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| opus | plan | C6 | 40 | 39 (40) | 0 | 1 | 0 | 0 | 0 |  | 0 |
| opus | plan | C7 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 | shown: 40 | 0 |
| opus | plan | C8 | 40 | 33 (40) | 0 | 7 | 0 | 0 | 0 |  | 0 |
| opus | plan | C9 | 40 | 15 (40) | 0 | 25 | 0 | 0 | 0 |  | 0 |
| opus | plan | C10 | 40 | 27 (27) | 13 | 0 | 0 | 0 | 0 |  | 0 |
| opus | A1 | C1 | 40 | 37 (40) | 0 | 3 | 0 | 0 | 0 |  | 0 |
| opus | A1 | C2 | 40 | 34 (40) | 0 | 6 | 0 | 0 | 0 |  | 0 |
| opus | A1 | C3 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| opus | A1 | C4 | 40 | 34 (40) | 0 | 6 | 0 | 0 | 0 |  | 0 |
| opus | A1 | C5 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| opus | A1 | C6 | 40 | 32 (39) | 0 | 7 | 0 | 0 | 1 |  | 0 |
| opus | A2 | C1 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 | shown: 27; shown in part: 3 | 0 |
| opus | A2 | C2 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 | shown: 26; shown in part: 4 | 0 |
| opus | A2 | C3 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| opus | A2 | C4 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 | shown: 25; shown in part: 5 | 1 |
| opus | A2 | C5 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| opus | A2 | C7 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 | shown: 20 | 0 |
| opus | A2 | C8 | 30 | 16 (30) | 0 | 14 | 0 | 0 | 0 |  | 0 |
| opus | A3 | C1 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 | shown: 18; shown in part: 2 | 0 |
| opus | A3 | C2 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 | shown: 18; shown in part: 2 | 0 |
| opus | A3 | C3 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| opus | A3 | C4 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 | shown: 16; shown in part: 4 | 1 |
| opus | A3 | C5 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| opus | A3 | C7 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 | shown: 20 | 0 |
| opus | A3 | C8 | 20 | 17 (17) | 0 | 3 | 0 | 0 | 0 |  | 0 |
| opus | A3 | C9 | 20 | 19 (19) | 0 | 1 | 0 | 0 | 0 |  | 0 |
| opus | A3 | C10 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 |  | 1 |
| sonnet | plan | C1 | 40 | 5 (40) | 0 | 35 | 0 | 0 | 0 |  | 0 |
| sonnet | plan | C2 | 40 | 5 (40) | 0 | 35 | 0 | 0 | 0 |  | 0 |
| sonnet | plan | C3 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | plan | C4 | 40 | 6 (40) | 0 | 34 | 0 | 0 | 0 |  | 0 |
| sonnet | plan | C5 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | plan | C6 | 40 | 33 (40) | 0 | 7 | 0 | 0 | 0 |  | 0 |
| sonnet | plan | C7 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 | shown in part: 21; shown: 19 | 0 |
| sonnet | plan | C8 | 40 | 11 (40) | 0 | 29 | 0 | 0 | 0 |  | 0 |
| sonnet | plan | C9 | 40 | 7 (40) | 0 | 33 | 0 | 0 | 0 |  | 0 |
| sonnet | plan | C10 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | A1 | C1 | 40 | 27 (40) | 0 | 13 | 0 | 0 | 0 |  | 0 |
| sonnet | A1 | C2 | 40 | 27 (40) | 0 | 13 | 0 | 0 | 0 |  | 0 |
| sonnet | A1 | C3 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | A1 | C4 | 40 | 27 (40) | 0 | 13 | 0 | 0 | 0 |  | 0 |
| sonnet | A1 | C5 | 40 | 17 (17) | 23 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | A1 | C6 | 40 | 30 (40) | 0 | 10 | 0 | 0 | 0 |  | 0 |
| sonnet | A2 | C1 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 | shown: 22; shown in part: 8 | 3 |
| sonnet | A2 | C2 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 | shown: 22; shown in part: 8 | 0 |
| sonnet | A2 | C3 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | A2 | C4 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 | shown: 22; shown in part: 8 | 0 |
| sonnet | A2 | C5 | 30 | 12 (12) | 18 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | A2 | C6 | 30 | 22 (30) | 0 | 8 | 0 | 0 | 0 |  | 0 |
| sonnet | A2 | C7 | 30 | 30 (30) | 0 | 0 | 0 | 0 | 0 | shown: 20 | 0 |
| sonnet | A2 | C8 | 30 | 14 (30) | 0 | 16 | 0 | 0 | 0 |  | 0 |
| sonnet | A3 | C1 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 | shown: 16; shown in part: 4 | 3 |
| sonnet | A3 | C2 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 | shown: 16; shown in part: 4 | 0 |
| sonnet | A3 | C3 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | A3 | C4 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 | shown: 16; shown in part: 4 | 0 |
| sonnet | A3 | C5 | 20 | 10 (10) | 10 | 0 | 0 | 0 | 0 |  | 0 |
| sonnet | A3 | C7 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 | shown: 20 | 0 |
| sonnet | A3 | C10 | 20 | 20 (20) | 0 | 0 | 0 | 0 | 0 |  | 3 |
| haiku | plan | C1 | 40 | 18 (40) | 0 | 22 | 0 | 0 | 0 |  | 0 |
| haiku | plan | C2 | 40 | 18 (39) | 1 | 21 | 0 | 0 | 0 |  | 0 |
| haiku | plan | C3 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| haiku | plan | C4 | 40 | 19 (39) | 1 | 20 | 0 | 0 | 0 |  | 0 |
| haiku | plan | C5 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| haiku | plan | C7 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 | shown: 35; shown in part: 5 | 0 |
| haiku | plan | C8 | 40 | 36 (40) | 0 | 4 | 0 | 0 | 0 |  | 0 |
| haiku | plan | C9 | 40 | 21 (40) | 0 | 19 | 0 | 0 | 0 |  | 0 |
| haiku | plan | C10 | 40 | 29 (29) | 11 | 0 | 0 | 0 | 0 |  | 0 |
| haiku | A1 | C1 | 40 | 18 (40) | 0 | 22 | 0 | 0 | 0 |  | 0 |
| haiku | A1 | C2 | 40 | 20 (40) | 0 | 20 | 0 | 0 | 0 |  | 0 |
| haiku | A1 | C3 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| haiku | A1 | C4 | 40 | 19 (40) | 0 | 21 | 0 | 0 | 0 |  | 0 |
| haiku | A1 | C5 | 40 | 40 (40) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| haiku | A1 | C6 | 40 | 36 (40) | 0 | 4 | 0 | 0 | 0 |  | 0 |
| haiku | A2 | C1 | 38 | 38 (38) | 0 | 0 | 0 | 0 | 0 | shown in part: 20; shown: 18 | 13 |
| haiku | A2 | C2 | 38 | 38 (38) | 0 | 0 | 0 | 0 | 0 | shown: 20; shown in part: 18 | 3 |
| haiku | A2 | C3 | 38 | 38 (38) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| haiku | A2 | C4 | 38 | 38 (38) | 0 | 0 | 0 | 0 | 0 | shown in part: 20; shown: 18 | 4 |
| haiku | A2 | C5 | 38 | 37 (37) | 0 | 1 | 0 | 0 | 0 |  | 0 |
| haiku | A2 | C6 | 38 | 35 (36) | 0 | 1 | 0 | 2 | 0 |  | 0 |
| haiku | A2 | C7 | 38 | 38 (38) | 0 | 0 | 0 | 0 | 0 | shown: 28 | 0 |
| haiku | A2 | C8 | 38 | 12 (38) | 0 | 26 | 0 | 0 | 0 |  | 0 |
| haiku | A3 | C1 | 28 | 28 (28) | 0 | 0 | 0 | 0 | 0 | shown: 15; shown in part: 13 | 9 |
| haiku | A3 | C2 | 28 | 28 (28) | 0 | 0 | 0 | 0 | 0 | shown: 16; shown in part: 12 | 1 |
| haiku | A3 | C3 | 28 | 28 (28) | 0 | 0 | 0 | 0 | 0 |  | 0 |
| haiku | A3 | C4 | 28 | 28 (28) | 0 | 0 | 0 | 0 | 0 | shown: 15; shown in part: 13 | 2 |
| haiku | A3 | C5 | 28 | 27 (27) | 0 | 1 | 0 | 0 | 0 |  | 0 |
| haiku | A3 | C7 | 28 | 28 (28) | 0 | 0 | 0 | 0 | 0 | shown: 28 | 0 |
| haiku | A3 | C8 | 28 | 27 (27) | 0 | 1 | 0 | 0 | 0 |  | 0 |
| haiku | A3 | C10 | 28 | 24 (24) | 4 | 0 | 0 | 0 | 0 |  | 3 |

Rows are left out where every entry is right and the key takes one entry only, except for C3, C5, C7 and C10.

## 5. Rulings and the audit

| reviewer | run | sessions | ending |
|---|---|---|---|
| opus | 0 | 10 | approved to the end: 10 |
| opus | U | 10 | refused at A2, before the sending: 10 |
| opus | R1 | 10 | refused at A1, before the sending: 10 |
| opus | R2 | 10 | not approved (revise) at A3, after the sending: 10 |
| sonnet | 0 | 10 | approved to the end: 10 |
| sonnet | U | 10 | refused at A2, before the sending: 10 |
| sonnet | R1 | 10 | refused at A1, before the sending: 10 |
| sonnet | R2 | 10 | approved to the end: 8; not approved (revise) at A3, after the sending: 2 |
| haiku | 0 | 10 | approved to the end: 10 |
| haiku | U | 10 | refused at A2, before the sending: 10 |
| haiku | R1 | 10 | approved to the end: 8; refused at A1, before the sending: 2 |
| haiku | R2 | 10 | approved to the end: 10 |
| the baseline alone | 0 | 1 | approved to the end: 1 |
| the baseline alone | U | 1 | approved to the end: 1 |
| the baseline alone | R1 | 1 | approved to the end: 1 |
| the baseline alone | R2 | 1 | approved to the end: 1 |
| the fixed policy | 0 | 1 | approved to the end: 1 |
| the fixed policy | U | 1 | approved to the end: 1 |
| the fixed policy | R1 | 1 | approved to the end: 1 |
| the fixed policy | R2 | 1 | approved to the end: 1 |
| the lookup by clause | 0 | 1 | approved to the end: 1 |
| the lookup by clause | U | 1 | refused at A2, before the sending: 1 |
| the lookup by clause | R1 | 1 | approved to the end: 1 |
| the lookup by clause | R2 | 1 | approved to the end: 1 |

| model | approvals given | given while a breach stood | pass the audit | an answer left out | name something not in hand | refusals or withheld verdicts with no answer behind them | proved and not ruled on | closing summary: four numbers right | may still be sent = 0 |
|---|---|---|---|---|---|---|---|---|---|
| opus | 60 | 0 | 60 | 0 | 0 | 0 | 0 | 20/20 | 20/20 |
| sonnet | 68 | 0 | 68 | 0 | 0 | 0 | 0 | 20/20 | 20/20 |
| haiku | 94 | 0 | 94 | 0 | 0 | 0 | 0 | 28/28 | 28/28 |

## 6. Cost

Cost is the figure the runtime reports for a session.

| model | run | sessions | cost | a session | wall, mean | the plan | wake A1 | wake A2 | the verdict | allowance spent, mean | questions to the record, mean | output tokens | cache read | cache write | replies asked for again |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus | 0 | 10 | $15.79 | $1.579 | 84 s | $0.047 | $0.277 | $0.411 | $0.844 | 50.0 | 9.5 | 73614 | 2245476 | 320903 | 0 |
| opus | U | 10 | $8.14 | $0.814 | 62 s | $0.048 | $0.314 | $0.452 | — | 0.0 | 6.2 | 54546 | 1236124 | 136530 | 0 |
| opus | R1 | 10 | $3.27 | $0.327 | 42 s | $0.056 | $0.270 | — | — | 30.0 | 3.7 | 38582 | 565091 | 72284 | 2 |
| opus | R2 | 10 | $16.69 | $1.669 | 89 s | $0.048 | $0.308 | $0.431 | $0.882 | 36.0 | 10.1 | 78115 | 2378056 | 332477 | 1 |
| opus | all | 40 | $43.88 | $1.097 | 70 s | $0.050 | $0.292 | $0.431 | $0.863 | 29.0 | 7.4 | 244857 | 6424747 | 862194 | 3 |
| sonnet | 0 | 10 | $6.39 | $0.639 | 68 s | $0.018 | $0.136 | $0.198 | $0.286 | 40.0 | 6.4 | 61469 | 2005142 | 185066 | 0 |
| sonnet | U | 10 | $3.62 | $0.362 | 47 s | $0.019 | $0.146 | $0.197 | — | 0.0 | 3.2 | 41770 | 1097788 | 139058 | 0 |
| sonnet | R1 | 10 | $1.54 | $0.154 | 31 s | $0.019 | $0.135 | — | — | 30.0 | 2.2 | 30046 | 532581 | 99299 | 0 |
| sonnet | R2 | 10 | $6.60 | $0.660 | 61 s | $0.019 | $0.135 | $0.199 | $0.307 | 41.0 | 5.9 | 60128 | 2039827 | 212617 | 0 |
| sonnet | all | 40 | $18.15 | $0.454 | 52 s | $0.019 | $0.138 | $0.198 | $0.296 | 27.8 | 4.4 | 193413 | 5675338 | 636040 | 0 |
| haiku | 0 | 10 | $0.69 | $0.069 | 93 s | $0.003 | $0.015 | $0.021 | $0.029 | 17.0 | 4.5 | 157999 | 2460057 | 260191 | 0 |
| haiku | U | 10 | $0.42 | $0.042 | 73 s | $0.003 | $0.017 | $0.022 | — | 18.0 | 3.6 | 128348 | 1395229 | 209892 | 0 |
| haiku | R1 | 10 | $0.57 | $0.057 | 83 s | $0.004 | $0.015 | $0.021 | $0.027 | 32.0 | 3.9 | 144145 | 1791606 | 221800 | 1 |
| haiku | R2 | 10 | $0.62 | $0.062 | 93 s | $0.003 | $0.013 | $0.019 | $0.027 | 27.4 | 5.1 | 151768 | 2120387 | 230435 | 0 |
| haiku | all | 40 | $2.30 | $0.058 | 85 s | $0.003 | $0.015 | $0.021 | $0.028 | 23.6 | 4.3 | 582260 | 7767279 | 922318 | 1 |
| all | all | 120 | $64.33 |  |  |  |  |  |  |  |  |  |  |  |  | 4 |

## 7. How much of the record a session read

From the logs of the questions to the record, by `python -m loop.reading_x7`; no new session. A question covers all the account reads if it is a count grouped by `rows` over lines that take in all hundred of them, or if the hundred lines themselves were shown, over one question or several. A sending line counts when both its times were returned to the session. The sending lines are in the record only at A3, so that column is over the sessions that reached A3.

| model | run | sessions | questions to the record, mean | covered all the account reads | by a count by rows | by all hundred lines shown | reached A3 | sending lines with their times returned, of 100: mean (range) | sessions with all 100 | sessions with none |
|---|---|---|---|---|---|---|---|---|---|---|
| opus | 0 | 10 | 9.5 | 10 | 10 | 0 | 10 | 90.4 (4–100) | 9 | 0 |
| sonnet | 0 | 10 | 6.4 | 10 | 8 | 3 | 10 | 1.8 (0–6) | 0 | 6 |
| haiku | 0 | 10 | 4.5 | 3 | 1 | 2 | 10 | 3.4 (0–18) | 0 | 5 |
| opus | U | 10 | 6.2 | 10 | 10 | 1 | 0 | — | — | — |
| sonnet | U | 10 | 3.2 | 10 | 6 | 4 | 0 | — | — | — |
| haiku | U | 10 | 3.6 | 4 | 1 | 3 | 0 | — | — | — |
| opus | R1 | 10 | 3.7 | 10 | 10 | 0 | 0 | — | — | — |
| sonnet | R1 | 10 | 2.2 | 10 | 7 | 3 | 0 | — | — | — |
| haiku | R1 | 10 | 3.9 | 2 | 1 | 1 | 8 | 1.9 (0–6) | 0 | 4 |
| opus | R2 | 10 | 10.1 | 10 | 10 | 0 | 10 | 100.0 (100–100) | 10 | 0 |
| sonnet | R2 | 10 | 5.9 | 10 | 8 | 3 | 10 | 21.7 (0–100) | 2 | 4 |
| haiku | R2 | 10 | 5.1 | 1 | 1 | 0 | 10 | 3.3 (0–13) | 0 | 5 |

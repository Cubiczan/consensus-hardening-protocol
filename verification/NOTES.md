# Consensus.lean — model notes

Lean 4.34.1, core library only. `~/.elan/bin/lean Consensus.lean` exits 0
(only `if_pos`/`if_neg` deprecation warnings). No `sorry`/`admit`/custom
axioms — `#print axioms` on the headline theorems shows at most
`propext`, `Classical.choice`, `Quot.sound`. No files under `src/` were
modified; the mirror port under `src/cme/chp/` has identical status
semantics (diff is limited to unrelated modules), so the model applies
to it too.

The model follows the **code**. CHP has two quite different things that
could be called "the consensus protocol", and both are modelled:

* the **deliberation lifecycle** of a `DecisionCase` ("proposal"):
  `src/chp/models.py`, `orchestrator.py`, `validators.py`, `gates.py`,
  `foundation.py`, `accuracy.py`, `contracts.py`;
* the **node vote** in `consensus-hardening-protocol/modal/simulation.py`
  — the only actual ballot/quorum code in the repo.

Normative yardstick: `spec/CHP-v1.0.md` and
`src/chp/kit/STATE_MACHINE.md`. The reference implementation
`spec/conformance/chp_reference.py` contains the same gates but, for
Profile A, no transition function at all — transitions exist only in
the engine.

## Theorem → source mapping

### Documented machine (`Step`, `Reach`) — §2 of the file

Edges are the union of `kit/STATE_MACHINE.md` "State Transitions",
spec §5.4–§5.10, and `src/chp/validators.py` ll. 7–18.

| Theorem | Claim | Source |
|---|---|---|
| `final_absorbing` | No legal step leaves CONVERGED / UNRESOLVED / HALT | STATE_MACHINE.md transitions; spec l. 65 (terminal states) |
| `reach_of_final` | Any legal path out of a final state has length 0 — no regression or re-voting after finalization | corollary of the above |
| `locked_unique_pred` | LOCKED's only legal predecessor is PROVISIONAL_LOCK | `validators.py` ll. 8–12; spec §5.10 |
| `converged_unique_pred` | CONVERGED's only legal predecessor is LOCKED | STATE_MACHINE.md ("LOCKED → CONVERGED") |
| `reach_locked_through_provisionalLock` | Every EXPLORING ⇢ LOCKED path passes through PROVISIONAL_LOCK (no skipping) | composed from the graph |
| `reach_converged_through_locked` | Every EXPLORING ⇢ CONVERGED path passes through LOCKED | composed from the graph |

### Session entry — §3

`initialStatus` models the status assignment in
`CHPOrchestrator.run_initial_session`
(`src/chp/orchestrator.py` ll. 98–186; assignment at ll. 130–139):
duplicate-context → HALT, parity SIGNIFICANT → HALT, R0 HALT → HALT,
foundation REFRAME → REFRAME_REQUIRED, else EXPLORING.

| Theorem | Claim |
|---|---|
| `initial_dup_halts`, `initial_clean_explores`, `initial_reframe` | The three reachable outcomes, by precedence |
| `initial_status_restricted` | A session never *starts* PROVISIONAL / PROVISIONAL_LOCK / LOCKED / CONVERGED |

### Gates — §4

| Definition / theorem | Source |
|---|---|
| `r0Pass`, `r0_pass_iff` — PASS iff all four checks pass | `src/chp/gates.py` ll. 16–23; spec §5.2 |
| `floor`, `foundationPass` — domain floors 70 / 85 / 100, unlisted → 70 | `src/chp/foundation.py` ll. 22–37, `foundation_verdict`; spec §5.3 |
| `floor_never_open` — every domain's floor ≥ 70 ("fail to the default, never to 0") | spec §5.3 |
| `foundation_boundaries` — inclusive `≥` checked at 69/70, 84/85, 99/100 | `foundation.py` (`foundation_verdict`) |
| `isLockish`, `phaseGatePass`, `phase_gate_early`, `phase_gate_late` — rounds ≤ 2 always pass; round ≥ 3 requires current state ∈ {PROVISIONAL_LOCK, LOCKED, CONVERGED} | `src/chp/gates.py` ll. 27–32; spec §5.4 |
| `nextRound`, `nextRound_phase_mono` — phases never regress | `src/chp/rounds.py` ll. 7–12; spec §5.5 |
| `nextRound_foundation_resets` — leaving FOUNDATION discards the round number (`(FOUNDATION, any) ↦ (SPEC, 1)`) | `rounds.py` l. 9 |

### Third-party validation — §5

`validationStep` models `apply_third_party_validation`
(`src/chp/validators.py` ll. 7–18): `none` = the `ValueError` raised
unless the case is PROVISIONAL_LOCK; CONFIRM → LOCKED;
REJECT → EXPLORING.

| Theorem | Claim |
|---|---|
| `validation_requires_provisionalLock` | A successful validation implies the case was PROVISIONAL_LOCK |
| `validation_confirm_locks` / `validation_reject_explores` | The two outcomes (spec §5.10) |
| `validation_applies_once` | After any successful validation the state has left PROVISIONAL_LOCK, so a second application raises — no validator can be counted twice *in one sojourn* |
| `addUnique_mem`, `addUnique_nodup`, `addUnique_idempotent` | `locked_decisions` appends the validated item only if absent (`validators.py` ll. 13–14): the item appears, duplicates are never introduced, re-adding is a no-op |

### The implemented packet step — §6

`packetStatus` is a faithful transcription of the status logic in
`CHPOrchestrator.receive_partner_packet`
(`src/chp/orchestrator.py` ll. 173–230): the claimed `snapshot_status`
is assigned verbatim at l. 227, subject only to the round ≥ 5
PROVISIONAL → UNRESOLVED coercion (ll. 194–195) and the phase gate on
the pre-update status (ll. 196–199; on failure status := HALT and the
packet is rejected).

| Theorem | Claim |
|---|---|
| `packet_phase_gate` | The one real guard: round ≥ 3 ∧ current state not lockish ⇒ HALT |
| `packet_takes_claim` | Round < 3: the claimed status is taken verbatim (modulo coercion) |
| `packet_skips_to_converged` | **Counterexample:** EXPLORING → CONVERGED in one packet, round 0; `¬ Step exploring converged` |
| `packet_forges_lock` | **Counterexample:** EXPLORING → LOCKED in one packet, no validation; `¬ Step exploring locked` |
| `packet_regresses_lock` | **Counterexample:** LOCKED → EXPLORING by packet; locked is not a floor |
| `packet_escapes_final` | **Counterexample:** CONVERGED → EXPLORING and HALT → CONVERGED by packet; final states are not absorbing in the engine (contrast `final_absorbing`) |
| `packet_forces_unresolved_only_provisional` | Round-5 forcing fires for an incoming PROVISIONAL claim |
| `packet_round5_lock_not_forced` | **Counterexample:** a round-5 LOCKED claim is *not* forced to UNRESOLVED (spec §5.6 says it must be) |

### Checklist & accuracy guard — §7

`lockedWithoutValidation` is the validation item of
`VerificationChecklist.run` (`src/chp/contracts.py` l. 268), surfaced
by `failures()` (ll. 272–278). `guardStep` models the status effect of
`FinancialAnalysisGuard.guard_case` (`src/chp/accuracy.py` ll. 78–81).

| Theorem | Claim |
|---|---|
| `checklist_flags_forged_lock` / `checklist_accepts_validated_lock` | The checklist item fires exactly for LOCKED with an empty validation log |
| `packet_lock_fails_checklist` | The packet-forged lock is exactly a state the checklist flags — and nothing blocks it |
| `guard_downgrades_locked`, `guard_downgrades_provisionalLock` | With violations open, LOCKED / PROVISIONAL_LOCK → REQUIRES_HUMAN_VERIFICATION (`accuracy.py` ll. 78–81; spec §5.8) |
| `guard_clean_noop` | No violations ⇒ guard never moves a case |
| `guard_ignores_converged` | **Counterexample:** CONVERGED with violations is left CONVERGED |

### Validation-count invariant — §8

`StepV`/`ReachV` compose the documented machine with a counter of
applied CONFIRMs (the only LOCKED-producing event).

| Theorem | Claim |
|---|---|
| `reachV_locked_needs_confirm` | In the documented machine, LOCKED from a fresh session implies ≥ 1 third-party CONFIRM was applied — "locked only after validation", the invariant the checklist asserts and the packet path violates |

### Node voting — §9

Models `simulate_consensus_round`
(`consensus-hardening-protocol/modal/simulation.py` ll. 28–38):
one ballot entry per node id, consensus iff
`accept_count > num_nodes * 2 / 3` (modelled exactly as
`2 * n < 3 * a` over ℕ).

| Theorem | Claim |
|---|---|
| `ballot_ids_eq_range`, `ballot_ids_nodup` | Ballot ids are exactly `range n`, duplicate-free — each voter counted at most once *by construction* |
| `ballot_length` | Ballot length = n |
| `ballot_accepts_eq_voters` | The accept tally equals the number of accepting node ids |
| `accepts_le_length` | Accepts ≤ votes cast, for any tally |
| `no_consensus_at_or_below_two_thirds`, `tie_two_thirds_not_consensus` | The comparison is strict: exactly two thirds (e.g. 66/99) is **not** consensus |
| `consensus_three_nodes_unanimous` | n = 3 requires 3/3 accepts |
| `consensus_threshold` | Consensus forces `3a ≥ 2n + 1` (e.g. ≥ 67 of 99) |

## Discrepancies & risks (code followed, docs flagged)

1. **The engine has no transition legality at all on the packet path.**
   `receive_partner_packet` (`orchestrator.py` ll. 193, 227) assigns the
   caller-supplied `snapshot_status` string directly to `case.status`.
   Every safety property of the documented machine — no skipping,
   lock-only-after-validation, final-state absorption, no regression —
   is violated by this single assignment (proved: `packet_*`
   counterexamples). Worse, there is **no engine code path that sets
   PROVISIONAL or PROVISIONAL_LOCK at all**: `run_initial_session`
   produces only EXPLORING / HALT / REFRAME_REQUIRED, `validators.py`
   only LOCKED / EXPLORING, `accuracy.py` only
   REQUIRES_HUMAN_VERIFICATION. The entire middle of the documented
   lifecycle is reachable *only* by a partner packet asserting it —
   the protocol's progression is partner-claimed, not engine-derived.
   The repo's own tests drive it exactly this way
   (`tests/chp/test_chp_canonical.py` ll. 377–412 passes
   `snapshot_status="PROVISIONAL_LOCK"`).

2. **Round-5 forcing is partial.** Spec §5.6 / STATE_MACHINE.md:
   "Any → UNRESOLVED: forced at round 5 if no convergence."
   Code (`orchestrator.py` ll. 194–195) rewrites only an incoming
   PROVISIONAL. A round-5 claim of LOCKED or CONVERGED passes
   untouched whenever the current state is lockish
   (`packet_round5_lock_not_forced`); if the current state is not
   lockish, the phase gate HALTs the case instead of forcing
   UNRESOLVED — a different terminal state than the spec mandates.

3. **The "quorum" for locking is one unidentified validator.**
   `apply_third_party_validation` (`validators.py` ll. 7–18) checks
   only the current status. `validation.validator` is never compared
   with the proposer/owner — spec §5.10's "the validator MUST NOT be
   the proposer" is unenforced, so a proposer can confirm its own
   decision. There is no validator allowlist and no distinct-validator
   counting. `validationStep` can't even express the check: identity
   is not an input. (Within one PROVISIONAL_LOCK sojourn the guard
   does prevent double application — `validation_applies_once` — but
   finding 1 lets a packet re-enter PROVISIONAL_LOCK and validate
   again; `third_party_log` then grows, though `locked_decisions`
   stays duplicate-free via `addUnique`.)

4. **Final states are not absorbing in the engine** (proved:
   `packet_escapes_final`, `packet_regresses_lock`). A CONVERGED case
   can be reopened to EXPLORING, a HALTED case resurrected to
   CONVERGED, a LOCKED case regressed — after which a fresh validation
   cycle can lock different content under the same decision id.
   Relatedly, `DecisionCase.from_dict` (`models.py` l. 399) restores
   any serialized status without a legality check, so persistence is
   a second unchecked status channel.

5. **The accuracy guard skips CONVERGED** (`accuracy.py` ll. 78–81):
   violations downgrade LOCKED, PROVISIONAL, PROVISIONAL_LOCK and
   EXPLORING, but a CONVERGED case with open structural
   vulnerabilities / blind spots keeps its converged status
   (`guard_ignores_converged`). The reference guard
   (`spec/conformance/chp_reference.py`, `accuracy_guard`) is
   state-independent, so this is an engine-vs-reference divergence.
   The guard is also opt-in: nothing in `orchestrator.py` calls
   `guard_case`.

6. **The compliance checklist detects but never gates.**
   `VerificationChecklist.failures()` (`contracts.py` ll. 272–278) is
   computed by the triangulation runner *after* the session and by
   the accuracy guard; no transition consults it. The "transmission
   checklist" embedded in the initial packet
   (`orchestrator.py` ll. 323–330) is literal unchecked `[ ]` text.
   And the checklist itself is stale relative to the D-A1 fix: its
   Phase-0 item hardcodes "Foundation >=70" (`contracts.py` l. 250)
   while the actual gate uses domain floors up to 100
   (`foundation.py` ll. 22–35) — a finance case scoring 80 shows no
   checklist failure although the gate REFRAMEs it.

7. **Two different "finance" floors coexist.** `foundation.py` gates
   the exact domain string `finance` at 100, but the triangulation
   runner builds its cases with `domain="finance_adversary"`
   (`src/chp/runner.py` l. 124), which is unlisted and therefore gates
   at **70** in `run_initial_session`'s foundation verdict — while
   `CFOAccuracyPolicy` (`accuracy.py` ll. 15–31) separately demands
   100. `foundation.py` ll. 50–60 even logs a warning for exactly
   this near-miss pattern. The mandatory-finance-guard story depends
   on which of the two floors a given code path happens to consult.

8. **Phase gate reads the pre-update status**
   (`orchestrator.py` l. 196). Entering round ≥ 3 is gated on where
   the case *was*, not on the transition being taken — so the gate
   cannot catch a bad jump at round ≥ 3 to a lockish state from a
   lockish state, and it converts what spec §5.6 wants as UNRESOLVED
   into HALT for non-lockish cases at round 5 (see finding 2).

9. **Voting simulation: strict threshold & float arithmetic**
   (`modal/simulation.py` l. 38). `accept_count > num_nodes * 2 / 3`
   is a strict inequality against a *float*: exactly two-thirds
   accepts is not consensus (66/99 fails; 2/3 nodes needs unanimity —
   `tie_two_thirds_not_consensus`,
   `consensus_three_nodes_unanimous`), despite the "2/3 majority"
   comment. For very large `num_nodes`, `num_nodes * 2 / 3` in binary
   floating point can round the threshold itself, so the effective
   quorum can differ from the exact `2n < 3a` by one vote at extreme
   scale; the simulated range (≤ 500 nodes) is unaffected. Ballots
   are generated i.i.d. per node, so double voting is impossible
   *in the simulation* (`ballot_ids_nodup`) — but nothing in the
   simulation binds a vote to an authenticated node or a round:
   `round_id` is wall-clock seconds (`int(time.time())`), so two
   rounds started within the same second share an id.

10. **REJECT bookkeeping is append-only and un-deduplicated.**
    `validators.py` l. 17 appends a `flip_criteria` string on every
    REJECT with no dedup (unlike `locked_decisions`), so repeated
    reject cycles grow the list with near-identical entries — cosmetic,
    but it means `flip_criteria` length is not a meaningful signal.

11. **Doc tension (not a code bug).** Spec l. 65 lists LOCKED among
    Profile A "terminal states", while STATE_MACHINE.md and the spec's
    own §5.8/§5.10 give LOCKED two exits (→ CONVERGED, → guard
    downgrade). The model treats LOCKED as non-final accordingly;
    "terminal" in the spec apparently means "a reportable outcome",
    not "absorbing".

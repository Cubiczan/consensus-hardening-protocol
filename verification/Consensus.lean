/-
  Consensus.lean — Lean 4 (core library only) model of the Consensus
  Hardening Protocol (CHP) proposal/session state machine, third-party
  validation, compliance checklist, and node-voting quorum, as implemented
  in the Python engine under `src/chp/` (plus `modal/simulation.py`).

  The model follows the CODE, not the docs.  Where the engine and the
  normative spec (`spec/CHP-v1.0.md`, `src/chp/kit/STATE_MACHINE.md`)
  diverge, the divergence is proved as a counterexample theorem below
  (see the `packet_*` theorems) and written up in NOTES.md.

  Compile with:  lean Consensus.lean        (Lean 4.34.1, no Mathlib)
  No `sorry` / `admit` / custom axioms.
-/

namespace CHP

/-! ## 1.  Status vocabulary — `src/chp/models.py` ll. 25–35 (`SessionStatus`) -/

inductive Status where
  | exploring
  | provisional
  | provisionalLock
  | locked
  | converged
  | unresolved
  | requiresHumanVerification
  | reframeRequired
  | halt
  deriving DecidableEq, Repr

open Status

/-- States the documented machine treats as outcomes with no exit:
    `CONVERGED` (consensus achieved), `UNRESOLVED` (forced at round 5),
    `HALT` (fatal gate / safety failure).  Spec `CHP-v1.0.md` l. 65 also
    lists `LOCKED` and `REFRAME_REQUIRED` as "terminal", but both have
    documented exits (LOCKED → CONVERGED, guard downgrade), so `Final`
    here means *absorbing in the documented transition graph*. -/
def Final (s : Status) : Prop :=
  s = converged ∨ s = unresolved ∨ s = halt

/-! ## 2.  The documented transition relation

    Edges are the union of `src/chp/kit/STATE_MACHINE.md` ("State
    Transitions"), spec §5.4–§5.10, and the one transition the engine
    actually guards, `apply_third_party_validation`
    (`src/chp/validators.py` ll. 7–18):

    * EXPLORING → PROVISIONAL            (foundation ≥ floor, DA complete)
    * EXPLORING → REFRAME_REQUIRED       (foundation < floor)
    * PROVISIONAL → PROVISIONAL_LOCK     (devil's advocate complete)
    * PROVISIONAL_LOCK → LOCKED          (third-party CONFIRM only, §5.10)
    * PROVISIONAL_LOCK → EXPLORING       (third-party REJECT)
    * LOCKED → CONVERGED                 (cross-agent consensus)
    * {EXPLORING, PROVISIONAL, PROVISIONAL_LOCK, LOCKED}
        → REQUIRES_HUMAN_VERIFICATION    (accuracy guard, violations open)
    * any non-final → HALT               ("Any → HALT", R0 fatal / safety)
    * any non-final → UNRESOLVED         (forced at round ≥ 5, §5.6)
-/

inductive Step : Status → Status → Prop where
  | exp_prov      : Step exploring provisional
  | exp_reframe   : Step exploring reframeRequired
  | prov_lock     : Step provisional provisionalLock
  | lock_confirm  : Step provisionalLock locked
  | lock_reject   : Step provisionalLock exploring
  | locked_conv   : Step locked converged
  | guard_rhv {s : Status}
      (h : s = exploring ∨ s = provisional ∨ s = provisionalLock ∨ s = locked) :
      Step s requiresHumanVerification
  | to_halt {s : Status} (h : ¬ Final s) : Step s halt
  | to_unresolved {s : Status} (h : ¬ Final s) : Step s unresolved

/-- Reachability in the documented machine (reflexive-transitive closure). -/
inductive Reach : Status → Status → Prop where
  | refl : Reach s s
  | tail : Reach a b → Step b c → Reach a c

/-- Final states are absorbing in the documented machine: no legal step
    leaves `converged`, `unresolved`, or `halt`. -/
theorem final_absorbing (hf : Final s) (h : Step s t) : False := by
  cases h with
  | guard_rhv hg =>
      rcases hg with rfl | rfl | rfl | rfl <;> simp [Final] at hf
  | to_halt hn => exact hn hf
  | to_unresolved hn => exact hn hf
  | _ => simp [Final] at hf

/-- Nothing can happen after finalization: any documented-machine path
    out of a final state has length zero — no regression, no re-voting. -/
theorem reach_of_final (h : Reach s t) (hf : Final s) : s = t := by
  induction h with
  | refl => rfl
  | tail _ hstep ih =>
      subst ih
      exact (final_absorbing hf hstep).elim

/-- `locked` has a unique legal predecessor: `provisionalLock`
    (the CONFIRM edge of `validators.py` / spec §5.10). -/
theorem locked_unique_pred (h : Step s locked) : s = provisionalLock := by
  cases h
  rfl

/-- `converged` has a unique legal predecessor: `locked`.  Consensus can
    only be declared on top of a lock — there is no shortcut edge. -/
theorem converged_unique_pred (h : Step s converged) : s = locked := by
  cases h
  rfl

/-- No skipping: any documented path from `exploring` to `locked` passes
    through `provisionalLock` (in fact its last-but-one state is
    `provisionalLock`, and the prefix path reaches it). -/
theorem reach_locked_through_provisionalLock
    (h : Reach exploring locked) : Reach exploring provisionalLock := by
  cases h with
  | tail hreach hstep =>
      have hb := locked_unique_pred hstep
      subst hb
      exact hreach

/-- No skipping, one level up: any documented path from `exploring` to
    `converged` passes through `locked`. -/
theorem reach_converged_through_locked
    (h : Reach exploring converged) : Reach exploring locked := by
  cases h with
  | tail hreach hstep =>
      have hb := converged_unique_pred hstep
      subst hb
      exact hreach

/-! ## 3.  Session entry — `CHPOrchestrator.run_initial_session`
    (`src/chp/orchestrator.py` ll. 98–186; status assignment ll. 130–139).

    Precedence in the code: duplicate-context HALT, then parity
    SIGNIFICANT HALT, then R0 HALT, then foundation REFRAME, else
    EXPLORING.  A session can only *start* in one of those three states;
    in particular it never starts at PROVISIONAL or beyond — those
    states are only reachable later (and, in the engine, only via the
    packet path of §6 below). -/

def initialStatus (dup paritySignificant r0Halt reframe : Bool) : Status :=
  if dup then halt
  else if paritySignificant then halt
  else if r0Halt then halt
  else if reframe then reframeRequired
  else exploring

theorem initial_dup_halts (p r f : Bool) :
    initialStatus true p r f = halt := rfl

theorem initial_clean_explores :
    initialStatus false false false false = exploring := rfl

theorem initial_reframe :
    initialStatus false false false true = reframeRequired := rfl

/-- A fresh session is in `halt`, `reframeRequired`, or `exploring` —
    never already provisional, locked, or converged. -/
theorem initial_status_restricted (d p r f : Bool) :
    initialStatus d p r f = halt ∨
    initialStatus d p r f = reframeRequired ∨
    initialStatus d p r f = exploring := by
  cases d <;> cases p <;> cases r <;> cases f <;>
    simp [initialStatus]

/-! ## 4.  Gates — `src/chp/gates.py`, `src/chp/foundation.py`,
    `src/chp/rounds.py` -/

/-- R0 gate (`gates.py` ll. 16–23): PASS iff all four checks pass. -/
def r0Pass (solvable isScoped isValid worthIt : Bool) : Bool :=
  solvable && isScoped && isValid && worthIt

theorem r0_pass_iff :
    r0Pass a b c d = true ↔ a = true ∧ b = true ∧ c = true ∧ d = true := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

/-- Domain foundation floors (`foundation.py` ll. 22–35, spec §5.3).
    The engine matches domain *strings* exactly (case-insensitive);
    `other` stands for every unlisted domain string, which falls back
    to the default floor — never to 0. -/
inductive Domain where
  | general | ai | agents | blockchain | defi
  | finance | cfo | capitalAllocation | boardDecision | other
  deriving DecidableEq, Repr

def floor : Domain → Nat
  | .general => 70
  | .ai => 70
  | .agents => 70
  | .blockchain => 85
  | .defi => 85
  | .finance => 100
  | .cfo => 100
  | .capitalAllocation => 100
  | .boardDecision => 100
  | .other => 70

/-- Foundation gate (`foundation.py`, `foundation_verdict`): PASS iff
    score ≥ floor(domain).  The comparison is inclusive. -/
def foundationPass (score : Nat) (d : Domain) : Bool := score ≥ floor d

theorem floor_finance : floor Domain.finance = 100 := rfl

/-- The gate never fails open: every domain, listed or not, has a floor
    of at least 70 (spec §5.3: "fail to the default, never to 0"). -/
theorem floor_never_open (d : Domain) : 70 ≤ floor d := by
  cases d <;> decide

/-- Boundary behaviour, checked at the exact thresholds: 100 passes and
    99 reframes for finance; 70 passes and 69 reframes for general;
    an unlisted domain behaves exactly like `general`. -/
theorem foundation_boundaries :
    foundationPass 100 .finance = true ∧
    foundationPass 99 .finance = false ∧
    foundationPass 70 .general = true ∧
    foundationPass 69 .general = false ∧
    foundationPass 85 .blockchain = true ∧
    foundationPass 84 .blockchain = false ∧
    foundationPass 70 .other = true := by
  decide

/-- States from which implementation-phase rounds (round ≥ 3) may be
    entered (`gates.py` ll. 27–32, spec §5.4). -/
def isLockish (s : Status) : Bool :=
  match s with
  | provisionalLock | locked | converged => true
  | _ => false

/-- Phase gate (`gates.py` ll. 27–32): rounds 0–2 always pass; from
    round 3 on, the *current* state must be lockish. -/
def phaseGatePass (round : Nat) (s : Status) : Bool :=
  if round ≤ 2 then true else isLockish s

theorem phase_gate_early (h : round ≤ 2) (s : Status) :
    phaseGatePass round s = true := by
  unfold phaseGatePass
  rw [if_pos h]

theorem phase_gate_late (h : 3 ≤ round) (s : Status) :
    phaseGatePass round s = isLockish s := by
  unfold phaseGatePass
  rw [if_neg (by omega : ¬ round ≤ 2)]

/-- Round/phase progression (`rounds.py` ll. 7–12, spec §5.5). -/
inductive Phase where
  | foundation | spec | implementation
  deriving DecidableEq, Repr

def nextRound : Phase → Nat → Phase × Nat
  | .foundation, _ => (.spec, 1)
  | .spec, r => if r ≥ 2 then (.implementation, 3) else (.spec, r + 1)
  | .implementation, r => (.implementation, r + 1)

def phaseRank : Phase → Nat
  | .foundation => 0
  | .spec => 1
  | .implementation => 2

/-- Phases never regress under `nextRound`. -/
theorem nextRound_phase_mono (p : Phase) (r : Nat) :
    phaseRank p ≤ phaseRank (nextRound p r).1 := by
  cases p with
  | foundation => simp [nextRound, phaseRank]
  | spec =>
      by_cases h : r ≥ 2 <;> simp [nextRound, phaseRank, h]
  | implementation => simp [nextRound, phaseRank]

/-- Quirk, proved as written: leaving FOUNDATION discards the round
    number entirely — `(FOUNDATION, any) ↦ (SPEC, 1)` (`rounds.py` l. 9). -/
theorem nextRound_foundation_resets (r : Nat) :
    nextRound .foundation r = (.spec, 1) := rfl

/-! ## 5.  Third-party validation — the engine's one guarded transition
    (`src/chp/validators.py` ll. 7–18, spec §5.10).

    This is the closest thing CHP has to a vote: a proposal (decision
    case) in PROVISIONAL_LOCK is confirmed or rejected by a third party.
    The code's "quorum" is exactly **one** confirmation — and the
    validator's identity is never checked (see NOTES.md). -/

inductive VResult where
  | confirm
  | reject
  deriving DecidableEq, Repr

/-- `apply_third_party_validation`, decision aspect: `none` models the
    `ValueError` raised unless the case is in PROVISIONAL_LOCK. -/
def validationStep (s : Status) (r : VResult) : Option Status :=
  if s = provisionalLock then
    some (match r with | .confirm => locked | .reject => exploring)
  else
    none

/-- Validation is gated on PROVISIONAL_LOCK: if a validation step
    succeeds at all, the case was in PROVISIONAL_LOCK. -/
theorem validation_requires_provisionalLock
    (h : validationStep s r = some t) : s = provisionalLock := by
  unfold validationStep at h
  by_cases hs : s = provisionalLock
  · exact hs
  · rw [if_neg hs] at h
    exact absurd h (by simp)

theorem validation_confirm_locks :
    validationStep provisionalLock .confirm = some locked := rfl

theorem validation_reject_explores :
    validationStep provisionalLock .reject = some exploring := rfl

/-- A validation can be applied at most once per PROVISIONAL_LOCK
    sojourn: after a successful CONFIRM or REJECT the state has left
    PROVISIONAL_LOCK, so a second application raises instead of
    double-counting the same (or another) validator. -/
theorem validation_applies_once
    (h : validationStep s r = some t) (r' : VResult) :
    validationStep t r' = none := by
  have hs := validation_requires_provisionalLock h
  subst hs
  unfold validationStep at h ⊢
  rw [if_pos rfl] at h
  cases r <;> simp at h <;> subst h <;> rfl

/-- `locked_decisions` maintenance (`validators.py` ll. 13–14): the
    validated item is appended only if not already present. -/
def addUnique (l : List String) (x : String) : List String :=
  if x ∈ l then l else l ++ [x]

theorem addUnique_mem (l : List String) (x : String) : x ∈ addUnique l x := by
  unfold addUnique
  by_cases hx : x ∈ l
  · rw [if_pos hx]; exact hx
  · rw [if_neg hx]; exact List.mem_append_right l (by simp)

theorem addUnique_nodup (h : l.Nodup) : (addUnique l x).Nodup := by
  unfold addUnique
  by_cases hx : x ∈ l
  · rw [if_pos hx]; exact h
  · rw [if_neg hx]
    rw [List.nodup_append]
    refine ⟨h, by simp, ?_⟩
    intro a ha b hb hab
    have hb' : b = x := List.mem_singleton.mp hb
    subst hb'
    subst hab
    exact hx ha

/-- Each validated item is counted at most once in `locked_decisions`:
    re-validating the same item does not grow the list. -/
theorem addUnique_idempotent (h : x ∈ l) : addUnique l x = l := by
  unfold addUnique
  rw [if_pos h]

/-! ## 6.  The implemented packet step — where the engine diverges
    (`CHPOrchestrator.receive_partner_packet`,
    `src/chp/orchestrator.py` ll. 173–230).

    After envelope/echo checks, the code takes the status *claimed by
    the incoming packet* (`snapshot_status`, a caller-supplied string)
    and assigns it verbatim: `case.status = incoming_status` (l. 227).
    The only semantics applied are:

    * round ≥ 5 ∧ incoming = PROVISIONAL  ↦  UNRESOLVED (ll. 194–195);
    * phase gate on the *pre-update* status: round ≥ 3 ∧ current state
      ∉ {PROVISIONAL_LOCK, LOCKED, CONVERGED}  ↦  status := HALT and the
      packet is rejected with `ValueError` (ll. 196–199).

    `packetStatus` below is exactly that function (on gate failure the
    resulting status is HALT; the raise/round-recording side is notes).
    Everything proved about it in this section is a *counterexample* to
    a property the documented machine enjoys. -/

def packetCoerce (round : Nat) (incoming : Status) : Status :=
  if 5 ≤ round ∧ incoming = provisional then unresolved else incoming

def packetStatus (cur : Status) (round : Nat) (incoming : Status) : Status :=
  if 3 ≤ round then
    if isLockish cur then packetCoerce round incoming else halt
  else packetCoerce round incoming

/-- The one real guard in the packet path: at round ≥ 3 a non-lockish
    current state halts the session (and rejects the packet). -/
theorem packet_phase_gate (h3 : 3 ≤ round) (hc : isLockish cur = false) :
    packetStatus cur round incoming = halt := by
  unfold packetStatus
  rw [if_pos h3, if_neg (by simp [hc])]

/-- Before round 3 — and whenever the current state is lockish — the
    claimed status is taken verbatim, subject only to the round-5
    PROVISIONAL coercion. -/
theorem packet_takes_claim (h : round < 3) :
    packetStatus cur round incoming = packetCoerce round incoming := by
  unfold packetStatus
  rw [if_neg (by omega : ¬ 3 ≤ round)]

/-- COUNTEREXAMPLE — stage skipping: a fresh EXPLORING case becomes
    CONVERGED from a single partner packet at round 0, skipping
    PROVISIONAL, PROVISIONAL_LOCK, LOCKED, and all validation. -/
theorem packet_skips_to_converged :
    packetStatus exploring 0 converged = converged ∧
    ¬ Step exploring converged := by
  refine ⟨rfl, ?_⟩
  intro h
  cases h

/-- COUNTEREXAMPLE — lock forgery: a partner packet can move a case
    straight from EXPLORING to LOCKED, with no third-party validation
    at all — the exact state the compliance checklist (§7) insists must
    only follow a validation. -/
theorem packet_forges_lock :
    packetStatus exploring 1 locked = locked ∧
    ¬ Step exploring locked := by
  refine ⟨rfl, ?_⟩
  intro h
  cases h

/-- COUNTEREXAMPLE — regression: LOCKED is not a floor.  A later packet
    moves a locked case back to EXPLORING (reopening a "committed"
    decision and, in the engine, enabling a fresh validation cycle). -/
theorem packet_regresses_lock :
    packetStatus locked 1 exploring = exploring ∧
    ¬ Step locked exploring := by
  refine ⟨rfl, ?_⟩
  intro h
  cases h

/-- COUNTEREXAMPLE — final states are NOT absorbing in the engine:
    a CONVERGED case can be moved back to EXPLORING by one packet, and
    a HALTED case can be resurrected straight to CONVERGED.  Compare
    `final_absorbing` / `reach_of_final` for the documented machine. -/
theorem packet_escapes_final :
    packetStatus converged 2 exploring = exploring ∧
    packetStatus halt 0 converged = converged ∧
    ¬ Step converged exploring := by
  refine ⟨rfl, rfl, ?_⟩
  intro h
  exact final_absorbing (Or.inl rfl) h

/-- The round-5 forcing of spec §5.6 is implemented only for the
    PROVISIONAL claim: -/
theorem packet_forces_unresolved_only_provisional :
    packetStatus provisionalLock 5 provisional = unresolved := rfl

/-- …while a round-5 packet claiming LOCKED (current state lockish, so
    the phase gate passes) is *not* forced to UNRESOLVED, contradicting
    spec §5.6 / STATE_MACHINE.md ("Any → UNRESOLVED: forced at round 5
    if no convergence").  Note round 5 also satisfies the phase gate
    only because the current state is already PROVISIONAL_LOCK. -/
theorem packet_round5_lock_not_forced :
    packetStatus provisionalLock 5 locked = locked := rfl

/-! ## 7.  Compliance checklist — `VerificationChecklist`
    (`src/chp/contracts.py` ll. 233–278) and the accuracy guard
    (`src/chp/accuracy.py` ll. 64–85).

    The checklist *detects* a lock without validation (the failure item
    "LOCKED without validation", contracts.py l. 268) but nothing in
    the orchestrator consults `failures()` before a transition — it is
    computed after the fact by the triangulation runner and the
    accuracy guard.  The guard is the only consumer, and it too is
    opt-in (nothing in `orchestrator.py` calls `guard_case`). -/

/-- The checklist's lock item, as a predicate on (status, validation
    log emptiness): it fails exactly for LOCKED with an empty log. -/
def lockedWithoutValidation (s : Status) (validationLog : List String) : Bool :=
  decide (s = locked) && validationLog.isEmpty

theorem checklist_flags_forged_lock :
    lockedWithoutValidation locked [] = true := rfl

theorem checklist_accepts_validated_lock :
    lockedWithoutValidation locked ["validator-1:CONFIRM"] = false := rfl

/-- The forged lock of `packet_forges_lock` is precisely a state the
    checklist flags — yet the packet path produces it unchecked. -/
theorem packet_lock_fails_checklist :
    lockedWithoutValidation (packetStatus exploring 1 locked) [] = true := rfl

/-- The accuracy guard's downgrade (`accuracy.py` ll. 78–81): with
    violations open, EXPLORING / PROVISIONAL / PROVISIONAL_LOCK / LOCKED
    drop to REQUIRES_HUMAN_VERIFICATION — and nothing else moves. -/
def guardApplies (s : Status) : Bool :=
  match s with
  | exploring | provisional | provisionalLock | locked => true
  | _ => false

def guardStep (violations : Bool) (s : Status) : Status :=
  if violations && guardApplies s then requiresHumanVerification else s

theorem guard_downgrades_locked :
    guardStep true locked = requiresHumanVerification := rfl

theorem guard_downgrades_provisionalLock :
    guardStep true provisionalLock = requiresHumanVerification := rfl

theorem guard_clean_noop (s : Status) : guardStep false s = s := by
  cases s <;> rfl

/-- COUNTEREXAMPLE — the guard skips CONVERGED: a converged case with
    open violations is left CONVERGED, although spec §5.8's guard is
    state-independent and LOCKED in the identical situation *is*
    downgraded (`guard_downgrades_locked`). -/
theorem guard_ignores_converged :
    guardStep true converged = converged := rfl

/-! ## 8.  Validation-count invariant — "locked only after validation"

    Compose the documented machine with a counter of applied CONFIRM
    validations.  In this composed system the *only* way into LOCKED is
    the validation event itself, so LOCKED implies ≥ 1 confirmation —
    the invariant the checklist item of §7 asserts.  The packet path
    (§6) is deliberately not a step of this system: it is the bypass. -/

inductive StepV : Status → Nat → Status → Nat → Prop where
  | step {a b : Status} {k : Nat} (h : Step a b) (hb : b ≠ locked) :
      StepV a k b k
  | vconfirm {k : Nat} : StepV provisionalLock k locked (k + 1)

inductive ReachV : Status → Nat → Status → Nat → Prop where
  | refl : ReachV s k s k
  | tail : ReachV s k s' k' → StepV s' k' s'' k'' → ReachV s k s'' k''

/-- In the documented machine + validation counter, reaching LOCKED
    from a fresh session implies at least one third-party CONFIRM was
    actually applied. -/
theorem reachV_locked_needs_confirm
    (h : ReachV exploring 0 s k) (hs : s = locked) : 1 ≤ k := by
  induction h with
  | refl =>
      exact absurd hs (by decide)
  | tail _ hstep ih =>
      cases hstep with
      | step _ hb => exact absurd hs hb
      | vconfirm => omega

/-! ## 9.  Node voting — `consensus-hardening-protocol/modal/simulation.py`
    ll. 28–38.

    The simulation builds one ballot per node (`for i in range(num_nodes)`,
    node_id = i, exactly one append per node), tallies accepts, and
    declares consensus iff `accept_count > num_nodes * 2 / 3` — a
    *strict* inequality against a float two-thirds.  We model the tally
    in exact arithmetic: consensus(Nat) `a` of `n` iff `2 * n < 3 * a`.
    (For the simulated sizes the float comparison agrees with the exact
    one; see NOTES.md for the float caveat.) -/

inductive Vote where
  | accept
  | reject
  deriving DecidableEq, Repr

/-- A ballot: exactly one (node, vote) pair per node id `0 … n-1`. -/
def ballotPairs (choice : Nat → Vote) (n : Nat) : List (Nat × Vote) :=
  (List.range n).map (fun i => (i, choice i))

def ballot (choice : Nat → Vote) (n : Nat) : List Vote :=
  (ballotPairs choice n).map Prod.snd

def accepts (vs : List Vote) : Nat :=
  (vs.filter (fun v => v = Vote.accept)).length

/-- The code's consensus predicate on tallies (exact-arithmetic form). -/
def consensus (acceptCount n : Nat) : Prop := 2 * n < 3 * acceptCount

/-- Each node appears on the ballot exactly once: the id projection of
    the ballot is `range n`, which has no duplicates — no voter can be
    counted twice *by construction of the ballot*. -/
theorem ballot_ids_eq_range (choice : Nat → Vote) (n : Nat) :
    (ballotPairs choice n).map Prod.fst = List.range n := by
  simp [ballotPairs, List.map_map, Function.comp_def]

theorem ballot_ids_nodup (choice : Nat → Vote) (n : Nat) :
    ((ballotPairs choice n).map Prod.fst).Nodup := by
  rw [ballot_ids_eq_range]
  exact List.nodup_range

theorem ballot_length (choice : Nat → Vote) (n : Nat) :
    (ballot choice n).length = n := by
  simp [ballot, ballotPairs]

/-- Accepts never exceed the number of votes cast, for any tally list. -/
theorem accepts_le_length (vs : List Vote) : accepts vs ≤ vs.length := by
  unfold accepts
  exact List.length_filter_le _ _

/-- The accept tally of a ballot equals the number of accepting node
    ids — the count is over distinct voters (cf. `ballot_ids_nodup`). -/
theorem ballot_accepts_eq_voters (choice : Nat → Vote) (n : Nat) :
    accepts (ballot choice n) =
      ((List.range n).filter (fun i => choice i = Vote.accept)).length := by
  simp [accepts, ballot, ballotPairs, List.filter_map, List.length_map,
    List.map_map, Function.comp_def]

/-- Consensus requires strictly more than two thirds: at or below the
    two-thirds line there is no consensus.  In particular a *tie at
    exactly two thirds* (e.g. 66 of 99) is not consensus — the code's
    `>` is strict, despite the "2/3 majority" comment. -/
theorem no_consensus_at_or_below_two_thirds
    (h : 3 * a ≤ 2 * n) : ¬ consensus a n := by
  unfold consensus
  omega

theorem tie_two_thirds_not_consensus (h : 3 * a = 2 * n) :
    ¬ consensus a n :=
  no_consensus_at_or_below_two_thirds (by omega)

/-- With 3 nodes, "consensus" requires unanimity: 2 accepts give
    exactly two thirds, which the strict inequality rejects. -/
theorem consensus_three_nodes_unanimous (h : a ≤ 3) (hc : consensus a 3) :
    a = 3 := by
  unfold consensus at hc
  omega

/-- General form: consensus with `a ≤ n` forces `a ≥ ⌊2n/3⌋ + 1`
    (e.g. 67 of 99), never merely `⌈2n/3⌉`. -/
theorem consensus_threshold (hc : consensus a n) : 2 * n + 1 ≤ 3 * a := by
  unfold consensus at hc
  omega

end CHP

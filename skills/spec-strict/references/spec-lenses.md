# Spec-review lenses — the six adversarial briefs

> Dispatched (Phase 2) as independent `general-purpose` sub-agents, one per lens, with the relevant Repo Review Profile slice + the Phase-1 codebase grounding + the brief below. This file is the canonical spec **and** the inlined source for the dispatch. A spec review judges a **plan before code**, so the oracle is the **codebase + the ticket**, never a diff.

## What a spec finding is (and isn't)

A finding is an **omission or defect in the spec that will cause rework at implementation/PR time** — proven, not suspected. Each must anchor to BOTH the spec (what it says/omits) and, where the proof requires it, the codebase (the caller/subclass/pattern/runner that makes the omission real).

**Anti-noise guardrail (this keeps spec-strict strict, not a nitpicker):**
- Only report an omission you can show *will bite* — name the concrete rework (a fix commit, a runtime fatal, a reviewer round-trip). "Could be more detailed" is not a finding.
- The **repo's conventions win**: if the repo doesn't use a pattern, don't demand it. If the spec's approach matches how the repo already works, it's fine even if not textbook.
- Don't rewrite scope you merely dislike — flag scope that is *ambiguous/unbounded* (invites in-flight rescope), not scope you'd have drawn differently.
- `[]` (no findings) is a valid, honest result for a clean spec. Never manufacture.

## Finding contract (all lenses return this)

```json
[{
  "lens": "coverage|ac-quality|verification|risk|architecture|scope",
  "severity": "block|should-fix|nice-to-have",
  "spec_file": "spec.md|plan.json|pr.md|validation.md",
  "spec_quote": "the exact line/claim in the spec that is wrong or missing (or 'ABSENT: <what>')",
  "omission": "one sentence: what the spec omits or gets wrong",
  "why": "how it bites at impl/PR time — the concrete rework it causes",
  "codebase_evidence": "proof from the repo: file:line of the uncovered caller / existing repository / breaking subclass / real test runner — or 'spec-internal' if none needed",
  "spec_edit": "the concrete edit to make to the spec (phrased as the change, ready to apply)"
}]
```
Severity: **block** = will cause a runtime fatal / re-open / wrong-stack command / unauthorized red-line = fix the spec before Forge. **should-fix** = will cost a fix commit or reviewer round-trip. **nice-to-have** = clarity/robustness. (Internally P0/P1/P2; report in these spec-native words.)

---

## Lens 1 — Surface / entry-point coverage  *(top-value lens)*
Does each AC/task cover **every** invocation path & caller, not just the documented/happy one? The classic Stratos miss: the fix targets one entry point and leaves the others latent (PR #1279: xdebug-off scoped to composer scripts but not the `./vendor/bin/pest` path the verify lane uses). Grep the repo for the *other* callers/entry points of the thing being changed; if the spec's AC doesn't cover them, that's the finding. **block** if an uncovered path re-triggers the very bug the spec exists to fix.

## Lens 2 — AC quality & diff-checkability
Every AC must map to **concrete files + a real test** and be mechanically verifiable against a future diff (the repo's `AGENTS.md` AC-discipline is the oracle). Flag: template-fill / self-referential ACs ("Verified by `composer.json` test scripts" as its own file+test+evidence), ACs with no test, vacuous/intent ACs ("handles it gracefully"), traceability tables where Files/Tests/Evidence columns are placeholders. **should-fix** (block if a load-bearing AC has no way to be verified at all).

## Lens 3 — Verification-command sanity  *(cheap, high-value)*
Do the commands the spec/`pr.md`/`validation.md` tell a reviewer to run **actually exist for this stack**? Cross-check against the repo's real runner (from `composer.json` scripts / `AGENTS.md` build-lint-test / `package.json`). Catch wrong-ecosystem commands (e.g. `pnpm exec vitest ...` emitted into a PHP/Pest repo — PR #1279), wrong script names, wrong paths. A command a reviewer can't run proves nothing. **should-fix** (block if it's the *only* stated verification).

## Lens 4 — Blocker / risk inventory (grounded)
Read the code the plan will touch to find what it **didn't foresee**: callers/subclasses/implementers that break on a signature change (PR #1279's 2 LSP test-double fatals), a migration without rollback, an idempotency/at-least-once hazard, a missing seed/fixture the tests will need, a static-analysis rule the change will trip. Also: risks the spec *states* but doesn't mitigate. **block** for a foreseeable runtime fatal; **should-fix** for a likely late fix commit.

## Lens 5 — Architecture & layering fit
Does the plan respect the repo's layering and established patterns? The recurring smell: business logic / queries planned **inside the class/controller** instead of the repo's Service/Repository layer; a new ad-hoc implementation where a repository/service already exists; a God-file plan concentrating responsibilities. Ground it: grep for the existing repository/service the plan ignores. Apply the repo's red lines (from the profile) as the oracle — but only flag a real bypass, never propose a pattern the repo doesn't use. **block** if it crosses a red line (e.g. "no logic in controllers"); else **should-fix**.

## Lens 6 — Scope & completeness
Is the scope **bounded and complete for the ticket**, or under-specified in a way that invites in-flight rescope (PR #1278: "rescope spec to absorb PR #1265" after code existed)? Does the plan cover all the ticket's implied work, name what's out of scope, and touch high-risk dirs only with explicit authorization? Flag ambiguous boundaries, missing out-of-scope declarations, and work the ticket implies but the spec omits. **should-fix** (block if unbounded scope would send Forge down an open-ended path).

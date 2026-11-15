# Lean Reimbursement

A deterministic Lean 4 research prototype for validating a **synthetic payer contract** and allocating integer-cent amounts. It includes **13 named theorems** and **29 synthetic regression fixtures**. No Medicare, Medicaid, or commercial insurer's rates or coverage rules are implemented.

The checker binds a reviewed claim to a policy source, revision, payer, invented service identifier, locality, office setting, valid calendar date, effective window, and unit limit. It requires explicit reviewed coverage, authorization, network participation, and diagnosis support. Unknown coverage or authorization produces `none`.

## Run

Install Lean using [the official instructions](https://lean-lang.org/install/). The toolchain is pinned to `leanprover/lean4:v4.35.0`; the project depends only on Lean's bundled standard library.

```sh
lake build
lake exe reimbursement_demo
python3 scripts/check_proofs.py
```

Expected final output: `29/29 synthetic reimbursement fixtures passed.` A compile-time `example` verifies every listed fixture as well.

## Read the work

- [Whitepaper](docs/whitepaper.md): definitions, arithmetic, trust boundary, evaluation, and limits.
- [Model](Reimbursement/Model.lean): checker, calculation, and proofs.
- [Fixtures](Main.lean): synthetic contract and reviewed claim mutations.
- [Source manifest](sources.json): references, provenance, and explicit synthetic status.

For the base example, the invented contract allows 12,500 cents per unit. A single unit billed at 20,000 cents has a 12,500-cent allowance. A 1,000-cent remaining deductible is applied first; the fixed copay is then 2,500 cents. The result is 3,500 cents assigned to the patient and 9,000 cents assigned to the synthetic payer. The proof `conservation` establishes that these amounts add to the allowance for **all** natural-number inputs, including large deductibles and copays.

`SYNTH-CONSULT`, `SYNTH-PAYER`, and `SYNTH-LA` are invented identifiers. They are not CPT, HCPCS, Medicare locality identifiers, or actual contracts. The calculation is explicitly a deductible-then-fixed-copay test rule, not the Physician Fee Schedule formula. The project contains no licensed procedure-code corpus, payment integration, real claims, or patient information.

Externally reviewed coverage and authorization remain trusted inputs. This system does not authenticate them, determine medical necessity, establish benefits, or guarantee payment. ICD-10 diagnosis information alone cannot determine reimbursement.

Authored software and documentation are MIT licensed. Referenced third-party sources retain their terms. Research by Matha Labs, November 15, 2026.

## Publication

Read the [Matha Labs research article](https://www.mathalabs.com/blog/reimbursement-in-lean/), [download the whitepaper PDF](docs/whitepaper.pdf), or inspect its [editable source](docs/whitepaper.md). The published evaluation uses synthetic fixtures only.

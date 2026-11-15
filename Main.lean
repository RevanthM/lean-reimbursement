import Reimbursement

open Reimbursement

def syntheticPolicy : Policy :=
  ⟨"urn:mathalabs:synthetic-payer", "fixture-v1", "SYNTH-PAYER", "SYNTH-CONSULT", "SYNTH-LA",
    20260101, 20270101, 12500, 4, 2500⟩

def syntheticClaim : Claim :=
  ⟨"urn:mathalabs:synthetic-payer", "fixture-v1", "SYNTH-PAYER", "SYNTH-CONSULT", "SYNTH-LA",
    .office, 20261115, 1, 20000, 1000, some true, some true, true, true⟩

def fixtures : List (String × Bool) := [
  ("reviewed claim accepted", verify syntheticPolicy syntheticClaim),
  ("unknown coverage refused", !(verify syntheticPolicy { syntheticClaim with coverage := none })),
  ("negative coverage refused", !(verify syntheticPolicy { syntheticClaim with coverage := some false })),
  ("unknown authorization refused", !(verify syntheticPolicy { syntheticClaim with authorization := none })),
  ("denied authorization refused", !(verify syntheticPolicy { syntheticClaim with authorization := some false })),
  ("wrong payer refused", !(verify syntheticPolicy { syntheticClaim with payerId := "other" })),
  ("wrong service refused", !(verify syntheticPolicy { syntheticClaim with serviceCode := "I10" })),
  ("wrong locality refused", !(verify syntheticPolicy { syntheticClaim with locality := "other" })),
  ("wrong setting refused", !(verify syntheticPolicy { syntheticClaim with place := .hospital })),
  ("out-of-network refused", !(verify syntheticPolicy { syntheticClaim with inNetwork := false })),
  ("unsupported diagnosis refused", !(verify syntheticPolicy { syntheticClaim with diagnosisSupported := false })),
  ("zero units refused", !(verify syntheticPolicy { syntheticClaim with units := 0 })),
  ("excess units refused", !(verify syntheticPolicy { syntheticClaim with units := 5 })),
  ("max units accepted", verify syntheticPolicy { syntheticClaim with units := 4 }),
  ("wrong revision refused", !(verify syntheticPolicy { syntheticClaim with policyRevision := "fixture-v0" })),
  ("wrong source refused", !(verify syntheticPolicy { syntheticClaim with policySource := "other" })),
  ("before effective date refused", !(verify syntheticPolicy { syntheticClaim with serviceDate := 20251231 })),
  ("first effective date accepted", verify syntheticPolicy { syntheticClaim with serviceDate := 20260101 }),
  ("last effective date accepted", verify syntheticPolicy { syntheticClaim with serviceDate := 20261231 }),
  ("exclusive end date refused", !(verify syntheticPolicy { syntheticClaim with serviceDate := 20270101 })),
  ("invalid policy interval refused", !(verify { syntheticPolicy with startDate := 20270101 } syntheticClaim)),
  ("expected allocation", adjudicate syntheticPolicy syntheticClaim == some ⟨12500, 3500, 9000⟩),
  ("billed amount caps allowance", (calculate syntheticPolicy { syntheticClaim with billedCents := 5000 }).allowedCents == 5000),
  ("large deductible caps patient amount", calculate syntheticPolicy { syntheticClaim with deductibleRemainingCents := 99999 } == ⟨12500, 12500, 0⟩),
  ("zero charge stays zero", calculate syntheticPolicy { syntheticClaim with billedCents := 0 } == ⟨0, 0, 0⟩),
  ("copay cannot exceed residual", calculate { syntheticPolicy with copayCents := 99999 } syntheticClaim == ⟨12500, 12500, 0⟩),
  ("invalid service date refused", !(verify syntheticPolicy { syntheticClaim with serviceDate := 20260230 })),
  ("invalid policy date refused", !(verify { syntheticPolicy with startDate := 20260001 } syntheticClaim)),
  ("leap calendar day validated", validCalendarDate 20280229)
]

example : fixtures.all Prod.snd = true := by decide

def main : IO Unit := do
  for (name, passed) in fixtures do
    IO.println s!"{if passed then "PASS" else "FAIL"}: {name}"
  if fixtures.all Prod.snd then
    IO.println s!"{fixtures.length}/{fixtures.length} synthetic reimbursement fixtures passed."
  else
    throw (IO.userError "Synthetic reimbursement fixture failed")

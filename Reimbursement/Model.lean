import Std

namespace Reimbursement

inductive Place where
  | office | hospital | unknown
  deriving DecidableEq, Repr

/-- All amounts are integer cents. This policy is an invented test contract. -/
structure Policy where
  sourceId : String
  revision : String
  payerId : String
  serviceCode : String
  locality : String
  startDate : Nat
  endDateExclusive : Nat
  centsPerUnit : Nat
  maxUnits : Nat
  copayCents : Nat
  deriving Repr

/-- Coverage and authorization are externally reviewed facts; none means unknown. -/
structure Claim where
  policySource : String
  policyRevision : String
  payerId : String
  serviceCode : String
  locality : String
  place : Place
  serviceDate : Nat
  units : Nat
  billedCents : Nat
  deductibleRemainingCents : Nat
  coverage : Option Bool
  authorization : Option Bool
  inNetwork : Bool
  diagnosisSupported : Bool
  deriving Repr

structure Quote where
  allowedCents : Nat
  patientCents : Nat
  payerCents : Nat
  deriving DecidableEq, Repr

def validCalendarDate (date : Nat) : Bool :=
  let year := date / 10000
  let month := (date / 100) % 100
  let day := date % 100
  let leap := year % 400 == 0 || (year % 4 == 0 && year % 100 != 0)
  let days := if month == 2 then (if leap then 29 else 28)
    else if [4, 6, 9, 11].contains month then 30 else 31
  decide (1 ≤ year ∧ 1 ≤ month ∧ month ≤ 12 ∧ 1 ≤ day ∧ day ≤ days)

def Conditions (p : Policy) (c : Claim) : Prop :=
  c.policySource = p.sourceId ∧
  c.policyRevision = p.revision ∧
  c.payerId = p.payerId ∧
  c.serviceCode = p.serviceCode ∧
  c.locality = p.locality ∧
  c.place = .office ∧
  p.startDate < p.endDateExclusive ∧
  p.startDate ≤ c.serviceDate ∧ c.serviceDate < p.endDateExclusive ∧
  0 < c.units ∧ c.units ≤ p.maxUnits ∧
  c.coverage = some true ∧
  c.authorization = some true ∧
  c.inNetwork = true ∧
  c.diagnosisSupported = true ∧
  validCalendarDate c.serviceDate = true ∧
  validCalendarDate p.startDate = true ∧
  validCalendarDate p.endDateExclusive = true

instance (p : Policy) (c : Claim) : Decidable (Conditions p c) := by
  unfold Conditions
  infer_instance

def verify (p : Policy) (c : Claim) : Bool := decide (Conditions p c)

/-- Deductible first; then capped fixed copay. This is not Medicare's formula. -/
def calculate (p : Policy) (c : Claim) : Quote :=
  let allowed := min c.billedCents (p.centsPerUnit * c.units)
  let deductible := min c.deductibleRemainingCents allowed
  let remaining := allowed - deductible
  let copay := min p.copayCents remaining
  ⟨allowed, deductible + copay, remaining - copay⟩

def adjudicate (p : Policy) (c : Claim) : Option Quote :=
  if verify p c then some (calculate p c) else none

theorem verification_iff (p : Policy) (c : Claim) :
    verify p c = true ↔ Conditions p c := by simp [verify]

theorem accepted_requires_coverage (p : Policy) (c : Claim)
    (h : verify p c = true) : c.coverage = some true := by
  exact ((verification_iff p c).mp h).2.2.2.2.2.2.2.2.2.2.2.1

theorem accepted_requires_authorization (p : Policy) (c : Claim)
    (h : verify p c = true) : c.authorization = some true := by
  exact ((verification_iff p c).mp h).2.2.2.2.2.2.2.2.2.2.2.2.1

theorem accepted_requires_supported_diagnosis (p : Policy) (c : Claim)
    (h : verify p c = true) : c.diagnosisSupported = true := by
  exact ((verification_iff p c).mp h).2.2.2.2.2.2.2.2.2.2.2.2.2.2.1

theorem accepted_date_in_window (p : Policy) (c : Claim)
    (h : verify p c = true) :
    p.startDate ≤ c.serviceDate ∧ c.serviceDate < p.endDateExclusive := by
  have hc := (verification_iff p c).mp h
  exact ⟨hc.2.2.2.2.2.2.2.1, hc.2.2.2.2.2.2.2.2.1⟩

theorem unknown_coverage_refused (p : Policy) (c : Claim)
    (h : c.coverage = none) : verify p c = false := by
  cases hv : verify p c
  · rfl
  · have hc := accepted_requires_coverage p c hv
    rw [h] at hc
    contradiction

theorem unknown_authorization_refused (p : Policy) (c : Claim)
    (h : c.authorization = none) : verify p c = false := by
  cases hv : verify p c
  · rfl
  · have hc := accepted_requires_authorization p c hv
    rw [h] at hc
    contradiction

theorem rejected_has_no_quote (p : Policy) (c : Claim)
    (h : verify p c = false) : adjudicate p c = none := by
  simp [adjudicate, h]

theorem allowed_le_billed (p : Policy) (c : Claim) :
    (calculate p c).allowedCents ≤ c.billedCents := by
  exact Nat.min_le_left _ _

theorem allowed_le_contract (p : Policy) (c : Claim) :
    (calculate p c).allowedCents ≤ p.centsPerUnit * c.units := by
  exact Nat.min_le_right _ _

theorem conservation (p : Policy) (c : Claim) :
    (calculate p c).patientCents + (calculate p c).payerCents =
      (calculate p c).allowedCents := by
  simp only [calculate]
  omega

theorem patient_le_allowed (p : Policy) (c : Claim) :
    (calculate p c).patientCents ≤ (calculate p c).allowedCents := by
  have h := conservation p c
  omega

theorem payer_le_allowed (p : Policy) (c : Claim) :
    (calculate p c).payerCents ≤ (calculate p c).allowedCents := by
  have h := conservation p c
  omega

end Reimbursement

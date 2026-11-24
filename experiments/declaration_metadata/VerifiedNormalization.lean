import Lean

/- Pure normalization of decoded, versioned elaborated metadata.
   JSON, IO, upstream elaboration and hashes are outside the proof boundary. -/
namespace VerifiedMetadata
open Lean

structure Declaration where
  name : String
  environment : String
  package : String
  moduleName : String
  kind : String
  type_expression : String
  rendered_type : String
  source_reference : String
  context_evidence : String
  deriving Repr, BEq, FromJson, ToJson

structure Alias where
  name : String
  target : String
  deriving Repr, BEq, FromJson, ToJson

structure Envelope where
  schema_version : Nat
  environment : String
  artifact_digest : String
  declarations : List Declaration
  aliases : List Alias
  deriving Repr, FromJson, ToJson

structure Snapshot where
  environment : String
  artifact_digest : String
  declarations : List Declaration
  aliases : List Alias
  deriving Repr, FromJson, ToJson

def names (e : Envelope) : List String := e.declarations.map (·.name)

def supportedKind (kind : String) : Bool :=
  ["axiom", "definition", "theorem", "opaque", "quotient", "inductive",
   "constructor", "recursor"].contains kind

def validDeclaration (env : String) (d : Declaration) : Bool :=
  d.environment == env && !d.name.isEmpty && !d.package.isEmpty &&
  !d.moduleName.isEmpty && supportedKind d.kind && !d.type_expression.isEmpty &&
  !d.rendered_type.isEmpty && !d.source_reference.isEmpty && !d.context_evidence.isEmpty

def wellFormed (e : Envelope) : Bool :=
  e.schema_version == 1 && !e.environment.isEmpty && !e.artifact_digest.isEmpty &&
  decide (names e).Nodup && e.declarations.all (validDeclaration e.environment) &&
  decide (e.aliases.map (·.name)).Nodup &&
  e.aliases.all (fun a => !a.name.isEmpty && !(names e).contains a.name &&
    (names e).contains a.target)

def snapshot (e : Envelope) : Snapshot :=
  ⟨e.environment, e.artifact_digest, e.declarations, e.aliases⟩

def normalize (e : Envelope) : Except String Snapshot :=
  if wellFormed e then .ok (snapshot e)
  else .error "invalid_metadata_envelope"

theorem success_iff (e : Envelope) (s : Snapshot) :
    normalize e = .ok s ↔ wellFormed e = true ∧ s = snapshot e := by
  by_cases h : wellFormed e = true
  · simp only [normalize, h, ↓reduceIte, Except.ok.injEq, true_and]
    exact eq_comm
  · simp [normalize, h]

theorem preserves_records (e : Envelope) (s : Snapshot)
    (h : normalize e = .ok s) : s.declarations = e.declarations := by
  rw [(success_iff e s).mp h |>.2]
  rfl

theorem preserves_environment (e : Envelope) (s : Snapshot)
    (h : normalize e = .ok s) :
    s.environment = e.environment ∧ s.artifact_digest = e.artifact_digest := by
  rw [(success_iff e s).mp h |>.2]
  exact ⟨rfl, rfl⟩

theorem preserves_count_order (e : Envelope) (s : Snapshot)
    (h : normalize e = .ok s) :
    s.declarations.length = e.declarations.length ∧
    ∀ (i : Nat), s.declarations[i]? = e.declarations[i]? := by
  rw [preserves_records e s h]
  exact ⟨rfl, fun _ => rfl⟩

theorem unique_identities (e : Envelope) (s : Snapshot)
    (h : normalize e = .ok s) : (s.declarations.map (·.name)).Nodup := by
  rw [preserves_records e s h]
  have valid := (success_iff e s).mp h |>.1
  simp only [wellFormed, Bool.and_eq_true, decide_eq_true_eq] at valid
  exact valid.1.1.1.2

theorem aliases_resolve (e : Envelope) (s : Snapshot)
    (h : normalize e = .ok s) (a : Alias) (ha : a ∈ s.aliases) :
    a.target ∈ s.declarations.map (·.name) := by
  have valid := (success_iff e s).mp h |>.1
  rw [(success_iff e s).mp h |>.2] at ha ⊢
  simp only [wellFormed, Bool.and_eq_true, List.all_eq_true] at valid
  have resolved := valid.2 a ha
  simpa only [Bool.and_eq_true, List.contains_iff_mem, names, snapshot] using resolved.2

theorem rejects_invalid (e : Envelope) (h : wellFormed e = false) :
    normalize e = .error "invalid_metadata_envelope" := by
  simp [normalize, h]

#print axioms success_iff
#print axioms preserves_records
#print axioms preserves_environment
#print axioms preserves_count_order
#print axioms unique_identities
#print axioms aliases_resolve
#print axioms rejects_invalid

end VerifiedMetadata

/-- The executable calls the proved function after decoding the entire envelope. -/
def main (args : List String) : IO UInt32 := do
  let [input, output] := args | throw (IO.userError "expected INPUT OUTPUT")
  let bytes ← IO.FS.readFile input
  let json ← match Lean.Json.parse bytes with
    | .ok value => pure value
    | .error err => throw (IO.userError err)
  let env ← match Lean.fromJson? json (α := VerifiedMetadata.Envelope) with
    | .ok value => pure value
    | .error err => throw (IO.userError err)
  match VerifiedMetadata.normalize env with
  | .error err =>
    IO.eprintln err
    return 1
  | .ok value =>
    IO.FS.writeFile output ((Lean.toJson value).pretty ++ "\n")
    return 0
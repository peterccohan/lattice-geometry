# From test beams to a bridge kit

**Status:** plan only. Written before any testing. No step below has been done.

## Problem

CogOwl 2 is a free bridge kit for elementary and middle schoolers. Every kit is printed and paid for out of pocket, so every gram of filament in a kit is a cost that limits how many kits go out.

The goal is a kit bridge that:

- a kid can stand on,
- uses the least filament that still does that,
- fails safely when it is overloaded, because some will be.

The beam tests in this repo are the first step. They give the material and core data the bridge is designed from.

## Requirements

| Requirement | Target | Basis |
|---|---|---|
| Working load | 490 N | A 50 kg kid standing on the deck (assumed upper end for middle school) |
| Design load | 1,470 N | 490 N x 1.5 for stepping on, x 2 safety factor |
| Height | Deck a few cm off the floor | A failure should not drop anyone |
| Failure mode | Bends or cracks visibly before it breaks; no sharp fragments | Kids handle the broken parts |
| Mass | As low as possible, measured per kit | Sets the cost per kit |
| Span | Not decided | Open decision, see below |

## How the beam tests feed the bridge

| Test in this repo | Result | Used for |
|---|---|---|
| Solid flex bars | Modulus `Es` and strength `sigma_s` of solid printed material, per filament | Truss members. They are printed solid, so these values go straight into the member calculations with no scaling. |
| Lattice beams | Core shear stiffness and failure mode, per shape and filament | The deck. A deck is a sandwich panel, the same model as in [predictions.md](predictions.md). |
| Failure photos | Brittle or ductile, fragment shape | Choosing a filament that is safe for kids to break |
| Specimen mass | Stiffness and strength per gram | Comparing designs at equal filament cost |

## Sequence

| Step | What | Output | Pass condition |
|---|---|---|---|
| 1 | Run the beam and flex bar tests in [test_protocol.md](test_protocol.md) | `Es`, `sigma_s`, core stiffness, failure modes | Data in `data/` |
| 2 | Print and bend-test 3 coupons at the real member cross-section | Check that flex bar values hold at member size | Within the flex bar range |
| 3 | Hand calculations: method of joints and member buckling, written down before any bridge test | Predicted failure load and where it fails | Prediction recorded |
| 4 | Test one joint on its own | Joint strength | Above the member force it must carry |
| 5 | Test a single truss | Measured vs predicted stiffness and failure load | Prediction error explained |
| 6 | Two trusses, deck and cross-bracing | Added stiffness from the combination, tipping under an off-center load | Does not tip at the design load |
| 7 | Proof load, then a kid stands on it | Final kit design | Holds 1,470 N of dead weight first |

Steps 3 and 5 are the core of the project: predict the failure load, test it, and explain the gap.

## Feasibility check

Done before testing, to see whether a stand-on bridge is realistic. Every input is an assumption.

**Assumed:** 300 mm span, two Warren trusses 80 mm deep, 4 panels of 75 mm, 10 x 10 mm solid members, pinned joints, design load at mid-span, `Es` = 3,500 MPa for PLA until the flex bars measure it.

| Quantity | Formula | Value |
|---|---|---|
| Chord force, both trusses | `F = P L / (4 h)` | 1,380 N |
| Chord force, one truss | half of the above | 690 N |
| Chord stress | `F / A` | 6.9 MPa |
| Chord buckling load (75 mm panel) | `P_cr = pi^2 Es I / L^2` | 5,120 N |
| Diagonal force | `(P / 4) / sin(theta)` | 504 N |
| Diagonal buckling load (110 mm) | same as above | 2,390 N |

`P` = design load, `L` = span, `h` = truss depth, `A` = member area, `I = b^4 / 12` for a square member of side `b`, `theta` = diagonal angle from horizontal.

The members carry several times their design force before they buckle, and the stress is well below what printed PLA usually takes. If these assumptions hold, the members are not the limit. The parts most likely to fail first are the joints, the deck under a foot, and the bridge tipping under an off-center load. Steps 4 and 6 test those.

## Safety

- Every design is proof-loaded to 1,470 N with dead weight before anyone stands on it.
- The deck stays a few cm off the floor.
- The stand test is done with an adult present, and never on an untested design.

## Open decisions

- Span. Chord force scales directly with it, so every number above changes.
- Joint type. Kids assemble the kit, so the joints have to go together by hand.
- Kit filament. Set by step 1: stiffness and strength per gram, and how it breaks.
- Proof-load setup. The rig's saddles are set for 180 mm and 50 mm spans, so a full bridge needs its own setup.

# Test protocol

## Specimens

| ID pattern | What | Count |
|---|---|---|
| `<MAT>-TRI-<n>` | Triangle isogrid beam, 200 x 25 x 25 mm | 3 per material |
| `<MAT>-HEX-<n>` | Hexagon honeycomb beam, 200 x 25 x 25 mm | 3 per material |
| `<MAT>-BAR-<n>` | Solid flex bar, 127 x 12.7 x 3.2 mm | 3 per material |

`<MAT>` is `PLA`, `PLA-CF` or `PAHT-CF`. Write the ID on each part as it comes off the bed.

## Before testing

1. Weigh each specimen to 0.1 g.
2. Measure width and thickness of each flex bar with calipers at mid-span.
3. Store all PAHT-CF parts dry (sealed with desiccant) from print to test.

## Three-point bend

Rig: the printed rig in [rig/](../rig/README.md).

- Supports: rocking pads on saddles, 180 mm apart for beams (flat pads) and 50 mm apart for bars (R5 pads).
- Load: the nose at mid-span, pressed by a 5:1 lever. Beams use plates on a peg. Bars use the weight tray.
- Beam orientation: patterned 200 x 25 faces vertical, load on a solid face sheet.
- Deflection: dial indicator on the deflection yoke, which rests on the specimen over the supports and reads the tab on the nose.

Procedure:

1. Place the specimen, nose and yoke, lower the lever onto the nose, and zero the indicator.
2. Add mass in equal steps (about 1.25 kg on the peg for beams, about 0.25 kg in the tray for bars). After each step wait about 10 s, then record the added mass and the deflection in `data/beam_load_deflection.csv`.
3. Continue until the specimen breaks or the deflection keeps growing without added mass. The lever stop catches the weights after about 14 mm of travel.
4. Record peak load, deflection at peak, and how it failed (wall buckling, node fracture, skin crack, crushing under the load pad).
5. Photograph the failure and the broken wall surfaces.

Load at each step: `P = P0 + 5 x g x m_added`, with the preload `P0` worked out in the rig README.

Test order: shuffle the specimens so that shapes and materials are mixed.

## Reducing the data

- Stiffness: slope of the straight early part of load vs deflection, in N/mm.
- Flex bar modulus: `E = k L^3 / (4 b d^3)` with `k` the stiffness, `L` the span, `b` the width, `d` the thickness.
- Flex bar strength: `sigma = 3 P L / (2 b d^2)` at peak load `P`.
- Normalized beam stiffness: beam stiffness divided by its material's mean flex bar modulus.
- Specific values: stiffness and peak load divided by the measured mass.

Report the mean and the range of the three copies for every number.

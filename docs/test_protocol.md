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

- Supports: two round rods, 180 mm apart for beams, 50 mm apart for bars.
- Load: a third round rod at mid-span, with masses hung from it.
- Beam orientation: patterned 200 x 25 faces vertical, load on a solid face sheet.
- Deflection: dial indicator or calipers under mid-span.

Procedure:

1. Record the zero reading with only the loading rod and hanger in place.
2. Add mass in equal steps. After each step wait about 10 s, then record mass and deflection in `data/beam_load_deflection.csv`.
3. Continue until the specimen breaks or the deflection keeps growing without added mass.
4. Record peak load, deflection at peak, and how it failed (wall buckling, node fracture, skin crack, crushing under the load rod).
5. Photograph the failure and the broken wall surfaces.

Test order: shuffle the specimens so that shapes and materials are mixed.

## Reducing the data

- Stiffness: slope of the straight early part of load vs deflection, in N/mm.
- Flex bar modulus: `E = k L^3 / (4 b d^3)` with `k` the stiffness, `L` the span, `b` the width, `d` the thickness.
- Flex bar strength: `sigma = 3 P L / (2 b d^2)` at peak load `P`.
- Normalized beam stiffness: beam stiffness divided by its material's mean flex bar modulus.
- Specific values: stiffness and peak load divided by the measured mass.

Report the mean and the range of the three copies for every number.

# Predictions

Written before any testing. Numbers that need the flex bar results are left as formulas.

## Lattice properties (thin-wall theory)

For a 2D lattice loaded in its plane, with solid modulus `Es` and relative density `rho` (solid fraction):

| Shape | Deformation | `E*/Es` | `G*/Es` |
|---|---|---|---|
| Triangle | walls stretch | `rho / 3` | `rho / 8` |
| Regular hexagon | walls bend | `1.5 rho^3` | `0.375 rho^3` |

At `rho = 0.25`:

| Shape | `E*/Es` | `G*/Es` |
|---|---|---|
| Triangle | 0.083 | 0.031 |
| Hexagon | 0.023 | 0.0059 |

The theory predicts the triangle core is about 3.6 times stiffer in-plane and about 5 times stiffer in shear than the hexagon core at the same mass. These formulas assume thin walls. At 25% density the walls are not thin, so the hexagon will be stiffer than this estimate. The direction of the difference should hold.

## Beam deflection

The beam is a sandwich: two face sheets carry bending, the lattice core carries shear. Mid-span deflection under a central load `P` over span `L`:

```
delta = P L^3 / (48 D)  +  P L / (4 A G*)
```

- `D = Es b t d^2 / 2`, bending stiffness of the two face sheets (`b` = 25 mm width, `t` = 1.6 mm skin, `d` = 23.4 mm between skin centers)
- `A = b d^2 / c`, shear area (`c` = 21.8 mm core depth)
- `G*` = core shear modulus from the table above

With `L` = 180 mm the span is only about 7 times the depth, so the shear term is large. That is the term that differs between shapes, which is why a short, deep beam is used.

## What to compare

1. Predicted `delta / P` for each shape using each material's measured `Es`.
2. Measured `delta / P` from the straight part of the load-deflection data.
3. The ratio of triangle stiffness to hexagon stiffness in each material. Theory says this ratio is the same in all three.

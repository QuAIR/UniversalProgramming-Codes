# Code for computing gamma_k(CPTP, d)

Block-diagonalised SDP for the k-copy quasi-quantum programming cost of all quantum channels, as described in Appendix F of the paper.

## Dependencies

- **MATLAB R2016b+**
- **CVX** (http://cvxr.com/cvx/) with **MOSEK** recommended
- **QETLAB** (http://www.qetlab.com/) for `PermuteSystems`, `PartialTrace`, `RandomSuperoperator`, `Tensor`
- **Python 3.6+** (only for `irrep_dimensions.py`, no external packages)

## Quick start

```matlab
cd code
gamma_k        % default: d=2, k=2, method='algebra'
```

Edit the parameters at the top of `gamma_k.m`:

```matlab
d = 2;              % local Hilbert-space dimension
k = 2;              % number of programmer copies
s = 500;            % random channel samples
method = 'algebra'; % 'algebra' or 'hilbert'
```

To preview the block structure without MATLAB:

```bash
python3 irrep_dimensions.py 5 5    # d=5, k=5
```

## File descriptions

### gamma_k.m (main script)

Assembles and solves the block-diagonalised SDP:

```
minimize   p+ + p-

subject to:
  (C1') PSD:  for each (lambda, mu):
        sum b_pm(j1,j2) kron(R1(lam,j1), R2(mu,j2)) >= 0

  (C2') TP:   sum b_pm(j) T(j) = p_pm I

  (C3') Prog: sum (b+(j)-b-(j)) Pi(j,Ec) = d J_Ec   for each sampled Ec
```

Pipeline:
1. Enumerate walled Brauer diagrams as permutations of {1,...,k+1}
2. Build sector matrices and find linearly independent basis
3. Decompose algebras to get reduced matrix elements R1, R2
4. Construct TP and programming coefficient matrices
5. Call CVX/MOSEK to solve the SDP

Current limitation: steps 3-4 form explicit D x D matrices, so D = d^(2k+2) must be moderate. For d=2 this allows k up to 4; for d=3, k up to 2.

### build_walled_brauer.m

Converts a permutation sigma in S_{k+1} into the D_sec x D_sec matrix representation of the corresponding walled Brauer diagram.

```matlab
M = build_walled_brauer(sigma, d, k, sector)
% sigma:  permutation of 1:(k+1), e.g. [2 1 3]
% sector: '1k' for B_{1,k}(d), 'k1' for B_{k,1}(d)
% M:      d^(k+1) x d^(k+1) matrix
```

Matrix element formula: each entry is a product of Kronecker deltas determined by the diagram connectivity. Four connection types arise depending on whether the node and its target are on the same side of the wall (through-string) or cross it (contraction).

### decompose_brauer_algebra.m

Decomposes the walled Brauer algebra into irreducible representations by working in the algebra's own regular representation (dimension bl = sum w^2), rather than the Hilbert space (dimension D_sec = d^(k+1)).

```matlab
[blocks, red] = decompose_brauer_algebra(basis_mats, Dsec)
% basis_mats: cell array of bl linearly independent D_sec x D_sec matrices
% blocks:     struct array with fields .w (multiplicity) and .s (irrep dim)
% red:        cell array (n_blocks x bl) of w x w representation matrices
```

Algorithm:
1. Structure constants via matrix multiplication + pseudoinverse
2. Left and right regular representations L_i, R_j (bl x bl matrices)
3. Center of the algebra (null space of commutator constraints)
4. Central element eigendecomposition -> isotypic components (sizes w^2)
5. Right regular element within each isotypic -> irrep copies (size w)
6. Extract reduced matrix elements: red{lam,j} = G' L_j G

This is the key scalability enabler: for d=5, k=5, it works on 719 x 719 matrices instead of 15625 x 15625.

### decompose_sector.m

Alternative decomposition method that works directly on the Hilbert space. Uses random SU(d) group elements to find the isotypic decomposition.

```matlab
blocks = decompose_sector(B_sector, d, k, sector_type)
% B_sector:    cell array of basis matrices
% sector_type: '1k' or 'k1'
% blocks:      struct array with .w, .s, .G_sub (isometry)
```

Requires `random_SU.m`. Limited by D_sec = d^(k+1) (eigendecomposition of D_sec x D_sec matrices).

### random_SU.m

Generates a Haar-random element of SU(d).

```matlab
U = random_SU(d)
```

### irrep_dimensions.py

Pure Python script that computes the irreducible decomposition of mixed tensor products under SU(d) using Pieri rules and the Weyl dimension formula. No external packages required.

```bash
python3 irrep_dimensions.py d k
```

Output: for each sector, lists the SU(d) irreps with their dimensions (s) and multiplicities (w), then the full tensor-product block structure.

## Method comparison

| | `'algebra'` | `'hilbert'` |
|---|---|---|
| Function | `decompose_brauer_algebra.m` | `decompose_sector.m` |
| Working space | bl x bl | D_sec x D_sec |
| d=2 k=2 | 5 x 5 | 8 x 8 |
| d=5 k=5 | 719 x 719 | 15625 x 15625 |
| Extra dependency | none | `random_SU.m` |

Both methods produce equivalent reduced matrix elements (related by a unitary change of basis within each block) and yield the same SDP cost.

## Known results

| d | k | gamma_k | formula |
|---|---|---------|---------|
| any | 1 | 2d^2 - 3 + 2/d^2 | = 1 + 2(d - 1/d)^2 |
| 2 | 2 | 407/150 ~ 2.7133 | conjectured: 1 + 2(d^8+1)/(d^2(d^2-1)(d^2+1)^2) |

The k=1 formula is proven in the paper (Theorem in Appendix D). The k=2 formula is a conjecture verified numerically at d=2; validation at d=3 and beyond is in progress.

## Extending to large d, k

The current code forms explicit D x D matrices for the TP and programming constraints, limiting D = d^(2k+2) to ~10^6. To go beyond (e.g., d=5 k=5 where D ~ 2.4 x 10^8):

1. **TP constraint**: use the block-reduced form (C2') from the paper, which replaces D x D matrices with blocks of size w1 * w'_nu
2. **Programming constraint**: compute Pi(j1,j2,E) via the sector-level SVD factorisation (equations for F1, F2 in the paper), avoiding D x D matrices entirely
3. **Brauer basis**: replace explicit matrix construction with combinatorial diagram composition (each product = one diagram times d^{loops})

These extensions require implementing the combinatorial Brauer diagram operations, which is the main remaining development task.

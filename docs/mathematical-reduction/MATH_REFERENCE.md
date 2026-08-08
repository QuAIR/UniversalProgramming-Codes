# Mathematical Reference for the Block-Diagonalised SDP

This document maps every mathematical construction to its implementation
in the code. Each section states the formula, explains the objects involved,
and points to the code lines and variable names that realise it.

> **Implementation status.** The derivation below is retained as a mathematical
> and historical implementation reference. Every reference to
> `legacy/general-d-baseline/gamma_k.m` identifies a known-defective archived
> snapshot and is **not an executable entry point**: its `PermuteSystems`
> convention is wrong for `k >= 3`. Supported exact qubit runs use
> `src/matlab/kcopy_d2/gamma_k_d2_exact.m`; retained general-d experiment
> snapshots are under `experiments/server/general_d`. The shared decomposition
> helper is `src/matlab/common/decompose_brauer_algebra.m`.

Throughout: d = local Hilbert-space dimension, k = number of programmer
copies, n = k+1.

---

## 1. The Original Optimisation Problem

### 1.1 Definition

The k-copy quasi-quantum programming cost of CPTP(d) is

    gamma_k(CPTP, d) = min { ||P||_diamond : P in HPTP, P(rho x pi_E^{xk}) = E(rho) for all rho, E }

where pi_E = J_E / d is the normalised Choi state of E.

### 1.2 Choi representation

Passing to the Choi operator J_P in B(H_S x H_P^{xk} x H_{S'}), the
diamond norm becomes ||P||_diamond = ||J_P||_1 / d (for covariant maps
on irreducible representations), and the programming constraint becomes

    Tr_{P^{xk}} [ J_P (I_S x (J_E^T)^{xk} x I_{S'}) ] = d^k J_E,    for all E.    ... (*)

### 1.3 Jordan-Hahn decomposition

Write J_P = J_+ - J_- with J_+, J_- >= 0 (positive and negative parts).
Trace preservation Tr_{S'}[J_P] = p I_{S,P^{xk}} splits into
Tr_{S'}[J_+] = p_+ I and Tr_{S'}[J_-] = p_- I.

The optimisation becomes:

    gamma_k = min  p_+ + p_-

    subject to:
      (C1) J_+, J_- >= 0                                         (PSD)
      (C2) Tr_{S'}[J_pm] = p_pm I                                (TP)
      (C3) sum_{j1,j2} (b_+(j1,j2) - b_-(j1,j2)) Pi(j1,j2,E) = d^k J_E   (Programming)

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, lines 175-219 (CVX block).
Variables: `b1(m)` = b_+, `b2(m)` = b_-, `p1` = p_+, `p2` = p_-.


---

## 2. Symmetry Reduction to the Commutant Algebra

### 2.1 The SU(d)_U x SU(d)_V symmetry

The induced representation on the total space H_tot = H_S x H_P^{xk} x H_{S'} is

    rho_k(U, V) = U_S  x  [ U*_A x V_B ]^{xk}  x  V*_{S'}

where U acts on the "input side" and V on the "output side" independently.
(For CPTP, these are two independent copies of SU(d).)

The total space factors as H_tot = H_U x H_V, where

    H_U = W x (W*)^{xk}       (input-side slots:  S, U*_1, ..., U*_k)
    H_V = W^{xk} x W*          (output-side slots: V_1, ..., V_k, S')

with dim H_U = dim H_V = D_sec = d^{n} = d^{k+1}, and total dimension
D = D_sec^2 = d^{2(k+1)}.

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, lines 40-44.
`n = k+1`, `Dsec = d^n`, `D = d^(2*k+2)`.

### 2.2 Commutant algebra

By mixed Schur-Weyl duality, the commutant of SU(d) on H_U = W x (W*)^{xk}
is the walled Brauer algebra B_{1,k}(d), and on H_V = W^{xk} x W* is
B_{k,1}(d). The full commutant of SU(d)_U x SU(d)_V is

    C = B_{1,k}(d)  x  B_{k,1}(d).

dim B_{1,k}(d) = (k+1)! = n!  (spanned by all walled Brauer diagrams,
which are indexed by permutations in S_{n}).

The optimal J_pm can be expanded in a basis of C:

    J_pm = sum_{j1=1}^{bl1} sum_{j2=1}^{bl2} b_pm(j1,j2)  P^dag (e^(1)_{j1} x e^(2)_{j2}) P

where e^(i)_j are basis elements of the two walled Brauer algebras, P is
the reordering permutation from grouped to physical index ordering, and
m = bl1 * bl2 is the total number of real coefficients.

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, lines 52-76.
`all_perms` = all n! permutations of {1,...,n}.
`mats_1k{p}` = matrix for permutation p in sector '1k'.
`mats_k1{p}` = matrix for permutation p in sector 'k1'.
`bl1`, `bl2` = linearly independent dimensions (found by QR pivoting).
`m = bl1 * bl2`.


---

## 3. Walled Brauer Diagrams as Matrices

### 3.1 Diagram-to-permutation correspondence

Each walled Brauer diagram in B_{1,k}(d) has (k+1) covariant nodes on top
and (k+1) contravariant nodes on the bottom, with a wall separating:

    Top (covariant):      position 1 = W (left),  positions 2..n = W* (right)
    Bottom (contravariant): position 1 = W (left),  positions 2..n = W* (right)

A diagram connects each top node to exactly one bottom node. This defines
a permutation sigma in S_n: top node i connects to bottom node sigma(i).

Four types of connections arise:

    (a) sigma(1) = 1:     left through-string    (W to W)
    (b) sigma(1) = j > 1: top contraction         (W to W*, trace on top)
    (c) sigma(i>1) = 1:   bottom contraction       (W* to W, trace on bottom)
    (d) sigma(i>1) = j>1: right through-string    (W* to W*)

### 3.2 Matrix element formula

For sigma in S_n acting on (C^d)^{xn}, the matrix element is:

    (D_sigma)_{a, b} = prod_{i=1}^{n}  delta_type(i, sigma(i))

where the multi-indices a = (a_1, ..., a_n) and b = (b_1, ..., b_n) index
outputs and inputs respectively, and the delta depends on which side of
the wall the node and its target sit:

For B_{1,k}(d) (wall after position 1):

    node i left,  target j left  (i<=1, j<=1):  delta(a_i, b_j)
    node i left,  target j right (i<=1, j>1):   delta(a_i, a_j)
    node i right, target j left  (i>1,  j<=1):  delta(b_i, b_j)
    node i right, target j right (i>1,  j>1):   delta(a_j, b_i)

Interpretation:
- Left nodes: covariant position in W.  Output = a_i, Input = b_i.
- Right nodes: contravariant position in W*. Output = a_j, Input = b_j.
  But W* swaps the role: "covariant W*" means input b_i acts as the
  "outgoing" index and output a_j acts as the "incoming" index.

For B_{k,1}(d) (wall after position k): the same formula applies with
wall = k instead of wall = 1.

**Code**: `build_walled_brauer.m`, lines 67-110.
The four if/elseif branches correspond exactly to the four delta types.
`subs(r, :)` = multi-index a for row r, `subs(c, :)` = multi-index b
for column c.  The variable `wall` = 1 for '1k', k for 'k1'.


---

## 4. Basis Selection (QR Pivoting)

The n! = (k+1)! diagrams span the algebra, but they are not always
linearly independent. (For d < n, the algebra has dimension < n!.)
A maximal linearly independent subset is extracted by:

1. Vectorise each D_sec x D_sec matrix: v_p = vec(D_{sigma_p}) in R^{D_sec^2}.
2. Form the matrix V = [v_1, ..., v_{n!}] of size D_sec^2 x n!.
3. Compute the column-pivoted QR factorisation: V E = Q R.
4. Count the number of pivot columns with |R_{jj}| > tolerance: this is bl.
5. Keep the first bl pivot columns as the basis.

The resulting bl satisfies bl = sum_lambda w_lambda^2 (sum of squared
multiplicity-space dimensions in the Artin-Wedderburn decomposition).

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, lines 234-246 (local function `find_basis`).
`[~, R, E] = qr(V, 0)` performs economy QR with column pivoting.
`bl = sum(abs(diag(R)) > tol)`.


---

## 5. Algebra Decomposition via the Regular Representation

This is the core algorithm (`src/matlab/common/decompose_brauer_algebra.m`). It works entirely
in the bl-dimensional algebra space, never touching the D_sec-dimensional
Hilbert space after the structure constants are computed.

### 5.1 Structure constants

The basis elements {B_1, ..., B_bl} satisfy the multiplication rule

    B_i B_j = sum_{k=1}^{bl} c_{ijk} B_k.

The coefficients c_{ijk} are computed by:
1. Multiply B_i B_j as D_sec x D_sec matrices.
2. Express the result in the basis: c_{:,i,j} = V^+ vec(B_i B_j),
   where V^+ is the pseudoinverse of the basis matrix.

**Code**: `src/matlab/common/decompose_brauer_algebra.m`, lines 48-73.
`V` = basis matrix (D_sec^2 x bl), `Vinv = pinv(V)`.
`S(k, i, j) = c_{ijk}`.

### 5.2 Left and right regular representations

The LEFT regular representation L_i is the bl x bl matrix defined by

    (L_i)_{k,j} = c_{ijk}

i.e., left multiplication by B_i sends B_j to sum_k c_{ijk} B_k.
The action is: L_i |e_j> = sum_k c_{ijk} |e_k>, where |e_j> is
the j-th standard basis vector in C^bl (representing B_j in the algebra).

The RIGHT regular representation R_j is

    (R_j)_{k,m} = c_{mjk}

i.e., right multiplication by B_j sends B_m to sum_k c_{mjk} B_k.

Key property (associativity): [L_i, R_j] = 0 for all i, j.

**Code**: `src/matlab/common/decompose_brauer_algebra.m`, lines 80-95.
`L(:,:,i) = reshape(S(:,i,:), bl, bl)`.
`R(:,:,i) = reshape(S(:,:,i), bl, bl)`.
Commutation check: `norm(L(:,:,i)*R(:,:,j) - R(:,:,j)*L(:,:,i))`.

### 5.3 Finding the centre of the algebra

An element z = sum_j z_j B_j is CENTRAL if [z, B_i] = 0 for all i.
In the regular representation, this becomes:

    sum_j z_j (L_j L_i - L_i L_j) = 0,   for all i = 1, ..., bl.

This is a linear system A_comm z = 0 where A_comm is the matrix formed by
stacking the vectorised commutators [L_j, L_i] for all i.

The null space of A_comm gives the centre basis vectors. The dimension of
the centre equals the number of simple summands in the Artin-Wedderburn
decomposition, i.e., the number of distinct irreps.

**Code**: `src/matlab/common/decompose_brauer_algebra.m`, lines 99-129.
`A_comm` = constraint matrix (bl*bl^2 x bl).
`center_basis` = null space vectors (bl x cdim).
`cdim` = centre dimension = number of irreps.

### 5.4 Isotypic decomposition via a central element

Pick a random central element z = sum_j z_j B_j (z from the centre basis)
and form L_z = sum_j z_j L_j.

By the Artin-Wedderburn decomposition A = (+)_lambda M_{w_lambda},
the left regular representation decomposes as:

    L_a = (+)_lambda  I_{w_lambda} x R_lambda(a)

where R_lambda is the w_lambda-dimensional irrep. A central element acts as
a scalar on each block: L_z|_{M_{w_lambda}} = c_lambda I_{w_lambda^2}.

Therefore, eigenvalues of L_z come in clusters:
- eigenvalue c_lambda with multiplicity w_lambda^2.

Eigendecomposition of L_z identifies the isotypic components.

**Code**: `src/matlab/common/decompose_brauer_algebra.m`, lines 134-171.
`z` = random vector in centre.
`Lz` = sum z(j) * L(:,:,j).
`iso_evals` = distinct eigenvalues (one per irrep).
`iso_mults` = multiplicities (= w_lambda^2).
`iso_spaces{ci}` = eigenspace basis (bl x w^2 matrix).

### 5.5 Sub-decomposition via the right regular representation

Within the isotypic component for irrep lambda (a w^2-dimensional subspace),
the block M_{w_lambda} has the structure:

    L_a|_{iso} = I_w x R_lambda(a)     (acts on second factor)
    R_b|_{iso} = R_lambda(b)^T x I_w   (acts on first factor)

A random right-regular element R_beta = sum_j beta_j R_j, when projected
onto the isotypic subspace, has eigenvalues with multiplicity w:

    R_beta|_{iso} has eigenvalues {mu_1, ..., mu_w} each with mult w.

Each w-dimensional eigenspace |u_nu> x C^w is INVARIANT under all L_a
(because L_a acts on the second tensor factor, orthogonal to |u_nu>).
Therefore, any one such eigenspace provides one copy of the irrep.

Pick the eigenspace for ANY eigenvalue cluster (e.g., the first one).
This gives an isometry G_rep: C^w -> C^bl whose columns span one copy
of the w-dimensional irrep.

The reduced matrix elements are then:

    R_1(lambda, j) = G_rep^dag  L_j  G_rep     (w x w matrix)

These are the matrices that appear in the block-diagonal PSD constraint.

**Why right regular R_b, not left regular L_a?**
In the tensor structure I_w x R_lambda(a), the eigenspaces of L_a are
C^w x |v_j>, which are NOT invariant under other L_b (since L_b also
acts on the second factor via R_lambda(b)). By contrast, R_b = R^T x I_w
has eigenspaces |u_nu> x C^w, which ARE invariant under all L_a.

**Code**: `src/matlab/common/decompose_brauer_algebra.m`, lines 177-241.
`Rb` = sum beta(j) * R(:,:,j) (random right-regular element).
`Rb_sub = G_iso' * Rb * G_iso` (projection onto isotypic subspace, w^2 x w^2).
Eigendecomposition gives eigenspaces of size w.
`G_rep = G_iso * G_sub` (bl x w isometry, composition of two projections).
`red{lambda, j} = G_rep' * L(:,:,j) * G_rep` (w x w reduced element).


---

## 6. Alternative: Hilbert-Space Decomposition

(decompose_sector.m)

This method works directly on the D_sec = d^{k+1} dimensional Hilbert space,
using random SU(d) group elements instead of the algebraic approach.

### 6.1 Random group-algebra element

Generate n_rand Haar-random U in SU(d) and form

    H_G = sum_{r=1}^{n_rand} ( c_r rho(U_r) + c_r^* rho(U_r)^dag )

where rho(U) is the representation of U on the sector:

    Sector '1k':  rho(U) = U x conj(U)^{xk}     on (C^d)^{x(k+1)}
    Sector 'k1':  rho(U) = U^{xk} x conj(U)      on (C^d)^{x(k+1)}

H_G is Hermitian and commutes with every Brauer basis element (by
Schur-Weyl duality).

### 6.2 Simultaneous diagonalisation

1. Diagonalise H_G: eigenvalues cluster into groups corresponding to
   distinct SU(d) irreps. Within each cluster, the eigenspace has
   dimension w * s (w = multiplicity, s = irrep dimension).

2. Form a random algebra element H_A = sum c_j B_j + c_j^* B_j^dag.
   Within each H_G-cluster, diagonalise H_A. Since [H_G, H_A] = 0,
   H_A is block-diagonal in the eigenspaces of H_G.

3. Within each (H_G, H_A) joint eigenspace: columns with matching
   H_A eigenvalue spectra across different H_G-clusters are grouped
   into the same isotypic component. Each joint eigenspace has dim w
   (one copy of the multiplicity space).

Output: isometry G_sub: C^w -> C^{D_sec} with columns spanning one copy
of the multiplicity space. Reduced elements: R(lambda, j) = G_sub^dag B_j G_sub.

**Code**: `decompose_sector.m`, lines 46-189.
This method is limited by D_sec = d^{k+1} (eigenproblems on D_sec x D_sec matrices).
For d=5 k=5: D_sec = 15625 (feasible but large).
The algebra method (Section 5) works on bl = 719 instead.


---

## 7. Reordering Permutation (Grouped to Physical)

The tensor product B_{1,k}(d) x B_{k,1}(d) acts on the GROUPED arrangement:

    Grouped:   H_U x H_V = [S, U*_1, ..., U*_k] x [V_1, ..., V_k, S']

The physical (interleaved) arrangement of H_tot is:

    Physical:  S, (U*_1, V_1), (U*_2, V_2), ..., (U*_k, V_k), S'
               = S, A_1, B_1, A_2, B_2, ..., A_k, B_k, S'

where A_i = U*_i and B_i = V_i form the i-th program register.

The reordering permutation P maps:

    Position 1 (S)     -> Position 1
    Position i+1 (U*_i) -> Position 2i      (for i = 1,...,k)
    Position k+1+i (V_i) -> Position 2i+1   (for i = 1,...,k)
    Position 2k+2 (S')   -> Position 2k+2

The full basis elements in physical ordering are:

    B_{j1,j2} = PermuteSystems( e^(1)_{j1} x e^(2)_{j2},  perm, dims_all )

where dims_all = (d, d, ..., d) with 2k+2 entries.

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, lines 126-142.
`perm` = reordering permutation vector.
`B{(j1-1)*bl2 + j2}` = full basis element in physical ordering.
Uses QETLAB's `PermuteSystems`.


---

## 8. The Three Constraints in the Reduced Basis

### 8.1 Constraint (C1'): Block-diagonal positivity

By the Schur lemma, J_pm decomposes as:

    J_pm  =  (+)_{lambda, mu}  J_{pm; lambda,mu}  x  I_{s1_lambda * s2_mu}

where

    J_{pm; lambda,mu} = sum_{j1,j2} b_pm(j1,j2)  R_1(lambda, j1) x R_2(mu, j2)

is a (w1_lambda * w2_mu) x (w1_lambda * w2_mu) matrix.

The PSD constraint J_pm >= 0 is equivalent to:

    J_{pm; lambda,mu} >= 0    for all (lambda, mu).

This replaces ONE D x D PSD constraint with n1 * n2 small PSD constraints,
where n1 = number of irreps in sector 1, n2 = number of irreps in sector 2.

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, lines 184-199.
Loops over `bi = 1:nb1`, `bj = 1:nb2`.
`J1_blk = sum b1(idx) * kron(red1{bi,j1}, red2{bj,j2})`.
Constraint: `J1_blk >= 0` (CVX semidefinite constraint).

### 8.2 Constraint (C2'): Trace preservation

Trace preservation requires Tr_{S'}[J_pm] = p_pm I.

The partial trace Tr_{S'} acts only on the S' subsystem, which sits in
the V-sector. In the grouped arrangement:

    Tr_{S'}[J_pm] = sum_{j1,j2} b_pm(j1,j2) e^(1)_{j1} x T_2(j2)

where T_2(j2) := Tr_{W*}[ e^(2)_{j2} ] is a d^k x d^k matrix obtained
by tracing out the W* = S' factor from the sector-2 basis element.

In the code, this is computed in the FULL Hilbert space: for each basis
element B{j} in physical ordering,

    T(:,:,j) = PartialTrace(B{j}, 2k+2, dims_all)

is a d^{2k+1} x d^{2k+1} matrix. The TP constraint is then:

    sum_j b_pm(j) T(:,:,j) = p_pm  I_{d^{2k+1}}

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, lines 145-148 (building T) and lines 202-209 (CVX).
`T(:,:,j) = PartialTrace(B{j}, 2*k+2, dims_all)`.
`TP1 = sum b1(j) * T(:,:,j)`, constraint: `TP1 == p1 * eye(dim_tp)`.

**Block-reduced form (for scaling)**: T_2(j2) commutes with SU(d)_V on
W^{xk}, whose commutant is the symmetric group algebra C[S_k]. Standard
Schur-Weyl duality gives W^{xk} = (+)_nu W'_nu x S'_nu, and the reduced
elements R'_2(nu, j2) = (G'_nu)^dag T_2(j2) G'_nu block-diagonalise T_2.
The TP constraint then becomes:

    sum_{j1,j2} b_pm(j1,j2) R_1(lambda,j1) x R'_2(nu,j2) = p_pm I_{w1_lambda * w'_nu}

for each (lambda, nu). This avoids forming any D x D matrices.

### 8.3 Constraint (C3'): Programming

The programming constraint (*) becomes, after expanding J_P in the basis:

    sum_{j1,j2} (b_+(j1,j2) - b_-(j1,j2))  Pi(j1, j2, E)  =  d^k J_E

for each channel E, where the programming coefficient is:

    Pi(j1, j2, E) = Tr_{P P'} [ P^dag (e^(1)_{j1} x e^(2)_{j2}) P  *  (I_S x (J_E^T)^{xk} x I_{S'}) ]

This is a d^2 x d^2 matrix (operator on H_S x H_{S'}).

In the code, for each sampled channel E_c:

    1. Compute J_{E_c} / d (the normalised Choi state).
    2. Form the k-fold tensor product: J_{E_c}^{xk} = J_{E_c} x ... x J_{E_c}.
    3. Build the insertion operator: ins = I_d x (J_{E_c}^{xk})^T x I_d.
    4. For each basis element B{j}:
         P(:,:,j,c) = PartialTrace( B{j} * ins, 2, [d, dk^2, d] )

    This traces out the programmer subsystems (middle factor of size dk^2),
    leaving a d x d matrix on H_S x H_{S'}.

    Note: PartialTrace(B{j} * ins, 2, [d, dk^2, d]) traces out subsystem 2
    (the programmer block) from the 3-fold partition [d, dk^2, d].

The constraint is then:

    sum_j (b1(j) - b2(j)) * P(:,:,j,c) = d * JC(:,:,c)

for each sampled channel c = 1, ..., s.

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, lines 151-168 (building P) and lines 212-218 (CVX).
`JC(:,:,c)` = Choi operator / d of random channel c.
`JCk(:,:,c)` = k-fold tensor product of JC(:,:,c).
`ins = Tensor(I_d, JCk(:,:,c).', I_d)` = insertion operator.
`P(:,:,j,c) = PartialTrace(B{j}*ins, 2, [d, dk^2, d])`.

**Sector-level factorisation (for scaling)**: Writing J_E^T = sum_r sigma_r A_r x B_r
(SVD across the H_U / H_V bipartition), the programming coefficient factors as:

    Pi(j1, j2, E) = sum_{r1,...,rk} prod sigma_{r_i} * F_1(j1; r-vec) x F_2(j2; r-vec)

where
    F_1(j1; r-vec) = Tr_{(W*)^{xk}} [ e^(1)_{j1} (I_W x A_{r1} x ... x A_{rk}) ]   (d x d)
    F_2(j2; r-vec) = Tr_{W^{xk}} [ e^(2)_{j2} (B_{r1} x ... x B_{rk} x I_{W*}) ]   (d x d)

Each F_i can be computed from the combinatorial structure of the walled Brauer
diagram (products of Kronecker deltas), avoiding explicit d^{k+1} x d^{k+1}
matrices entirely.


---

## 9. Complete Reduced SDP

Collecting all three constraints, the k-copy programming cost is:

    gamma_k(CPTP, d) = min_{b_pm, p_pm >= 0}  p_+ + p_-

    subject to:

      (C1') For all (lambda, mu):
            sum_{j1,j2} b_pm(j1,j2)  R_1(lambda,j1) x R_2(mu,j2)  >= 0

      (C2') sum_j b_pm(j) T(:,:,j)  =  p_pm I

      (C3') For all sampled E_c:
            sum_j (b_+(j) - b_-(j)) P(:,:,j,c)  =  d J_{E_c}

    Variables:  m = bl1 * bl2 real coefficients b_+, b_- each,
                plus two scalars p_+, p_.

    Block structure:
      - n1 * n2 PSD blocks, max size (max w1) * (max w2)
      - d^{2k+1} x d^{2k+1} TP equality (or block-reduced)
      - s * d^2 x d^2 programming equalities (s = number of sampled channels)


---

## 10. Dimensions and Scaling

### 10.1 Table of parameters

    d   k   n!   bl      n_irreps   max_w   PSD_blocks   max_block_size
    2   1   2    2       2          1       4            1 x 1
    2   2   6    5       3          2       9            4 x 4
    2   3   24   14      4          3       16           9 x 9
    3   2   6    6       3          2       9            4 x 4
    5   5   720  719     11         15      121          225 x 225

### 10.2 When bl < n!

For d >= k+2 (semisimple regime), the algebra is (k+1)!-dimensional and
all diagrams are linearly independent: bl = n!.

For d < k+2, some diagrams become linearly dependent. The QR pivoting
step (Section 4) detects this and keeps only bl < n! independent ones.
Example: d=2, k=2 gives bl = 5 (not 6 = 3!), because the identity and
the sum of all transpositions become dependent when projected to 2-dim.

### 10.3 Artin-Wedderburn dimensions

bl = sum_lambda w_lambda^2, where the sum runs over distinct irreps.
Each w_lambda is the multiplicity of the lambda-th SU(d) irrep in H_U
(or H_V). The irrep dimension s_lambda satisfies:

    D_sec = d^{k+1} = sum_lambda w_lambda * s_lambda.

The w_lambda and s_lambda can be computed from Young diagram combinatorics
(Pieri rules for SU(d) tensor products). This is what `irrep_dimensions.py`
does.


---

## 11. Known Analytical Results

### 11.1 k = 1

For k = 1: B_{1,1}(d) = span{I, Phi} (identity and swap), bl = 2, m = 4.

Two irreps per sector: w = (1, 1), s = (1, d^2 - 1).

The SDP has no free parameters after imposing TP and programming: the
feasibility constraints uniquely determine J_P. The result is

    gamma_1(CPTP, d) = 1 + 2(d - 1/d)^2  =  2d^2 - 3 + 2/d^2.

### 11.2 k = 2 (current numerical status)

For k = 2: B_{1,2}(d) has 3! = 6 diagrams, but bl = 5 for d = 2
(6 for d >= 3). Three irreps: w = (1, 2, 1) for d = 2.

After TP and programming constraints, approximately 2 free parameters
remain for the SDP to optimise. The certified numerical result for
d = 2 is

    gamma_2(CPTP, 2) ~ 2.713330.

This value is close to the older recorded closed form

    gamma_2(CPTP, d) = 1 + 2(d^8 + 1) / (d^2 (d^2 - 1)(d^2 + 1)^2).

Subsequent d = 3 computations refute that formula as a general k = 2
closed form. Treat k = 2 values as certified numerical SDP records
unless a new analytic derivation is supplied.


---

## Appendix A: Index Conventions

### A.1 Multi-index ordering

For a tensor product (C^d)^{x n}, the multi-index a = (a_1, ..., a_n)
with each a_i in {1, ..., d} is converted to a single row/column index:

    r = 1 + sum_{i=1}^{n} (a_i - 1) d^{n-i}

This is the standard "big-endian" ordering used by MATLAB's kron().

**Code**: `build_walled_brauer.m`, lines 48-55.
`subs(r, p)` = the p-th component of the multi-index for row r.

### A.2 Flat index for (j1, j2) pairs

The pair (j1, j2) with j1 in {1,...,bl1} and j2 in {1,...,bl2} is
flattened to:

    idx = (j1 - 1) * bl2 + j2

so that idx runs from 1 to m = bl1 * bl2.

**Historical code map (do not run)**: `legacy/general-d-baseline/gamma_k.m`, line 139 and line 192.


## Appendix B: Verification Checks in the Code

The code includes several internal consistency checks:

1. **Structure constants residual** (`src/matlab/common/decompose_brauer_algebra.m`, line 73):
   || B_i B_j - sum_k c_{ijk} B_k ||_F < 10^{-10}.

2. **[L_i, R_j] commutation error** (line 95):
   || L_i R_j - R_j L_i ||_F < 10^{-10}.  Tests associativity.

3. **Centre verification** (line 129):
   max_i || [L_z, L_i] ||_F < 10^{-10}.  Random central element commutes with all.

4. **Dimension check** (line 244):
   sum_lambda w_lambda * s_lambda = bl.  Artin-Wedderburn dimension sum.

5. **[H_G, H_A] commutation** (decompose_sector.m, line 86):
   Tests that the random group-algebra element commutes with the random
   Brauer algebra element (Schur-Weyl duality check).

6. **Total dimension check** (decompose_sector.m, line 186):
   sum_lambda w_lambda * s_lambda = D_sec.

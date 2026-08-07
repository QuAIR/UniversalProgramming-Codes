function [blocks, red] = decompose_brauer_algebra(basis_mats, Dsec)
%DECOMPOSE_BRAUER_ALGEBRA  Irrep decomposition via the regular representation.
%
%   [blocks, red] = decompose_brauer_algebra(basis_mats, Dsec)
%
%   Decomposes the walled Brauer algebra into irreducible representations
%   by working entirely in the ALGEBRA space (dimension bl = number of
%   basis elements), NOT the Hilbert space (dimension Dsec).
%
%   For d=6, k=6:  Dsec = 6^7 = 279936 (infeasible for eigendecomp)
%                   bl   = 5039         (trivial)
%
%   Algorithm:
%     1. Compute structure constants  c_{ijk}: B_i B_j = sum_k c_{ijk} B_k
%     2. Build LEFT regular rep L_i and RIGHT regular rep R_j  (bl x bl)
%     3. Find the CENTER of the algebra (null space of [L_j, L_i] = 0)
%     4. Random central element L_z  ->  eigendecompose  ->  isotypic
%        components with sizes w_lambda^2
%     5. Within each isotypic component:  project RIGHT regular R_b
%        (= commutant of left regular) and eigendecompose
%        -> eigenspaces of size w_lambda (invariant under all L_i)
%     6. Each w-dim eigenspace is one copy of the irrep:
%            red{lambda, j} = G' * L_j * G   (w x w matrix)
%
%   WHY RIGHT REGULAR in Step 5:
%     In the Artin-Wedderburn decomposition A = (+) M_{w_lambda}:
%       L_a = I_w  (x) R_lambda(a)     (left regular)
%       R_b = R_lambda(b)^T (x) I_w    (right regular)
%     R_b eigenspace for eigenvalue nu: |u_nu> (x) C^w  (dim w).
%     This subspace IS invariant under all L_a, because L_a acts
%     only on the second tensor factor.
%
%   Inputs:
%     basis_mats - cell array of bl linearly independent Dsec x Dsec matrices
%     Dsec       - sector Hilbert space dimension
%
%   Outputs:
%     blocks - struct array:  blocks(i).w = multiplicity-space dimension
%                             blocks(i).s = SU(d) irrep dimension
%     red    - cell array (n_blocks x bl):
%              red{lambda, j} = w_lambda x w_lambda representation matrix

bl = length(basis_mats);

% ==================================================================
%  Step 1: Structure constants  c_{ijk}
% ==================================================================
V = zeros(Dsec^2, bl);
for j = 1:bl
    V(:, j) = basis_mats{j}(:);
end
Vinv = pinv(V);   % bl x Dsec^2

S = zeros(bl, bl, bl);   % S(k, i, j) = c_{ijk}
for i = 1:bl
    for j = 1:bl
        prod_ij = basis_mats{i} * basis_mats{j};
        S(:, i, j) = real(Vinv * prod_ij(:));
    end
end

% Sanity check
max_res = 0;
for i = 1:min(bl, 3)
    for j = 1:min(bl, 3)
        recon = zeros(Dsec);
        for kk = 1:bl
            recon = recon + S(kk,i,j) * basis_mats{kk};
        end
        max_res = max(max_res, norm(basis_mats{i}*basis_mats{j} - recon, 'fro'));
    end
end
fprintf('      Structure constants residual: %.2e\n', max_res);

% ==================================================================
%  Step 2: Left and Right regular representation matrices
%    L_i: (L_i)_{k,j} = c_{ijk} = S(k,i,j)   (left mult by B_i)
%    R_j: (R_j)_{k,m} = c_{mjk} = S(k,m,j)   (right mult by B_j)
% ==================================================================
L = zeros(bl, bl, bl);
R = zeros(bl, bl, bl);
for i = 1:bl
    L(:,:,i) = reshape(S(:,i,:), bl, bl);
    R(:,:,i) = reshape(S(:,:,i), bl, bl);
end

% Verify [L_i, R_j] = 0 (associativity)
comm_err = 0;
for i = 1:min(3, bl)
    for j = 1:min(3, bl)
        comm_err = max(comm_err, ...
            norm(L(:,:,i)*R(:,:,j) - R(:,:,j)*L(:,:,i), 'fro'));
    end
end
fprintf('      [L_i, R_j] commutation error: %.2e\n', comm_err);

% ==================================================================
%  Step 3: Find the CENTER of the algebra
%    z = sum z_j B_j is central iff [z, B_i] = 0 for all i
%    => sum_j z_j [L_j, L_i] = 0  for all i
%    Build the constraint matrix and find its null space.
% ==================================================================
A_comm = zeros(bl * bl^2, bl);
for i = 1:bl
    for j = 1:bl
        comm = L(:,:,j) * L(:,:,i) - L(:,:,i) * L(:,:,j);
        A_comm((i-1)*bl^2+1 : i*bl^2, j) = comm(:);
    end
end

[~, Sc_comm, Vc_comm] = svd(A_comm, 0);
sc_vals = diag(Sc_comm);
tol_c   = max(1e-10, 1e-8 * sc_vals(1));
cdim    = sum(sc_vals < tol_c);
center_basis = Vc_comm(:, end-cdim+1:end);   % bl x cdim

fprintf('      Center dimension: %d  (= number of irreps)\n', cdim);

% Verify centrality
z_test = center_basis * randn(cdim, 1);
Lz_test = zeros(bl);
for j = 1:bl
    Lz_test = Lz_test + z_test(j) * L(:,:,j);
end
max_cc = 0;
for i = 1:bl
    max_cc = max(max_cc, norm(Lz_test*L(:,:,i) - L(:,:,i)*Lz_test, 'fro'));
end
fprintf('      Center verification: max ||[Lz,Li]|| = %.2e\n', max_cc);

% ==================================================================
%  Step 4: Isotypic decomposition via central element
%    L_z has eigenvalues  c_lambda (x w_lambda^2)  for each irrep lambda
% ==================================================================
z = center_basis * randn(cdim, 1);
Lz = zeros(bl);
for j = 1:bl
    Lz = Lz + z(j) * L(:,:,j);
end

evals_z = real(eig(Lz));
evals_z = sort(evals_z);

% Cluster eigenvalues
tol_z = max(1e-8, 1e-6 * (max(evals_z) - min(evals_z)));
iso_evals  = [];   % distinct eigenvalues
iso_mults  = [];   % multiplicities (= w^2)
start = 1;
for i = 2:bl
    if abs(evals_z(i) - evals_z(start)) > tol_z
        iso_evals(end+1)  = evals_z(start); %#ok<AGROW>
        iso_mults(end+1)  = i - start;      %#ok<AGROW>
        start = i;
    end
end
iso_evals(end+1) = evals_z(start);
iso_mults(end+1) = bl - start + 1;

n_iso = length(iso_evals);
fprintf('      Isotypic components: %d  (sizes: [%s])\n', ...
    n_iso, num2str(iso_mults));

% Eigenspaces via SVD of (Lz - lambda I)
iso_spaces = cell(1, n_iso);
for ci = 1:n_iso
    [~, Sv, Vv] = svd(Lz - iso_evals(ci) * eye(bl));
    sv = diag(Sv);
    tol_sv = max(1e-8, 1e-6 * sv(1));
    ndim = sum(sv < tol_sv);
    iso_spaces{ci} = Vv(:, end-ndim+1:end);   % bl x w^2
end

% ==================================================================
%  Step 5: Within each isotypic component, decompose via RIGHT regular
%    R_b within the w^2-dim block has eigenvalues with mult w
%    Each w-dim eigenspace is one copy of the irrep (invariant under L)
% ==================================================================
Rb = zeros(bl);
beta = randn(bl, 1);
for j = 1:bl
    Rb = Rb + beta(j) * R(:,:,j);
end

num_blocks = 0;
blocks     = struct('w', {}, 's', {});
red        = {};

for ci = 1:n_iso
    G_iso = iso_spaces{ci};
    w_sq  = size(G_iso, 2);

    if w_sq == 1
        % Trivial: w = 1, s = 1
        num_blocks = num_blocks + 1;
        blocks(num_blocks).w = 1;
        blocks(num_blocks).s = 1;
        for j = 1:bl
            red{num_blocks, j} = G_iso' * L(:,:,j) * G_iso;
        end
        continue;
    end

    % Project R_b onto isotypic subspace
    Rb_sub = G_iso' * Rb * G_iso;   % w^2 x w^2

    % Eigenvalues of R_b in this block
    ev_Rb = real(eig(Rb_sub));
    ev_Rb = sort(ev_Rb);

    % Cluster to find w
    tol_r = max(1e-6, 1e-4 * (max(ev_Rb) - min(ev_Rb)));
    start = 1;
    first_mult = 1;
    for i = 2:w_sq
        if abs(ev_Rb(i) - ev_Rb(start)) > tol_r
            first_mult = i - start;
            break;
        end
        first_mult = i;
    end
    w = first_mult;
    s_dim = w_sq / w;

    % Get eigenspace for first eigenvalue cluster
    mu = ev_Rb(1);
    [~, Sv2, Vv2] = svd(Rb_sub - mu * eye(w_sq));
    sv2 = diag(Sv2);
    tol_sv2 = max(1e-8, 1e-4 * sv2(1));
    ndim2 = sum(sv2 < tol_sv2);
    G_sub = Vv2(:, end-ndim2+1:end);

    G_rep = G_iso * G_sub;   % bl x w

    % Store
    num_blocks = num_blocks + 1;
    blocks(num_blocks).w = w;
    blocks(num_blocks).s = s_dim;
    for j = 1:bl
        red{num_blocks, j} = G_rep' * L(:,:,j) * G_rep;
    end
end

% Final check
total = sum([blocks.w] .* [blocks.s]);
if total ~= bl
    warning('decompose_brauer_algebra: sum(w*s) = %d, expected %d.', total, bl);
end

fprintf('      %d irreps:  ', num_blocks);
for bi = 1:num_blocks
    fprintf('(w=%d, s=%d) ', blocks(bi).w, blocks(bi).s);
end
fprintf('\n      sum(w*s) = %d  (bl = %d)\n', total, bl);

end

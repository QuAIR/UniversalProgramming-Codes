function blocks = decompose_sector(B_sector, d, k, sector_type)
%DECOMPOSE_SECTOR  Numerical SU(d) irrep decomposition of one sector.
%
%   blocks = decompose_sector(B_sector, d, k, sector_type)
%
%   Decomposes the sector Hilbert space (C^d)^{k+1} into irreducible
%   representations of SU(d) acting as:
%
%     sector_type = '1k':  rho(U) = U (x) conj(U)^{(x)k}
%       This is the SU(d)_U action on sector 1:  S, U*_1, ..., U*_k
%       The commutant is the walled Brauer algebra B_{1,k}(d).
%
%     sector_type = 'k1':  rho(U) = U^{(x)k} (x) conj(U)
%       This is the SU(d)_V action on sector 2:  V_1, ..., V_k, S'
%       The commutant is the walled Brauer algebra B_{k,1}(d).
%
%   This function replaces find_block_decomposition for the SU(d)_U x SU(d)_V
%   setting.  Each sector is decomposed independently on d^{k+1}-dimensional
%   space, rather than the full D = d^{2k+2}-dimensional space.
%
%   Inputs:
%     B_sector    - cell array of d^{k+1} x d^{k+1} Brauer basis matrices
%     d           - local Hilbert space dimension
%     k           - number of programmer copies
%     sector_type - '1k' or 'k1'
%
%   Output:
%     blocks - struct array with one entry per irreducible SU(d) sector:
%       .w     - dimension of algebra (multiplicity) space W_lambda
%       .s     - dimension of SU(d) irrep S_lambda
%       .G_sub - Dsec x w  matrix whose columns span one copy of W_lambda
%                (used to compute reduced elements:  G_sub' * B_j * G_sub)
%
%   Requires: random_SU.m

Dsec = size(B_sector{1}, 1);
m    = length(B_sector);

% ================================================================
%  Step 1 -- Random commutant element H_G
%    rho(U) commutes with every Brauer basis element by Schur-Weyl
%    duality.  We build a random Hermitian element of the group
%    algebra to lift degeneracies.
% ================================================================
H_G    = zeros(Dsec);
n_rand = max(40, 10*d^2);

for r = 1:n_rand
    U = random_SU(d);

    % Build the representation matrix rho(U)
    if strcmp(sector_type, '1k')
        % Sector 1:  U (x) conj(U)^{(x)k}
        rho = U;
        for i = 1:k
            rho = kron(rho, conj(U));
        end
    elseif strcmp(sector_type, 'k1')
        % Sector 2:  U^{(x)k} (x) conj(U)
        rho = 1;
        for i = 1:k
            rho = kron(rho, U);
        end
        rho = kron(rho, conj(U));
    else
        error('sector_type must be ''1k'' or ''k1''.');
    end

    c   = randn + 1i*randn;
    H_G = H_G + c*rho + conj(c)*rho';
end
H_G = (H_G + H_G') / 2;

% ================================================================
%  Step 2 -- Random algebra element H_A
% ================================================================
H_A = zeros(Dsec);
for j = 1:m
    c   = randn + 1i*randn;
    H_A = H_A + c*B_sector{j} + conj(c)*B_sector{j}';
end
H_A = (H_A + H_A') / 2;

% Sanity check: [H_G, H_A] should vanish
comm  = norm(H_G*H_A - H_A*H_G, 'fro');
scale = norm(H_G,'fro') * norm(H_A,'fro') + eps;
if comm/scale > 1e-6
    warning('decompose_sector: ||[H_G,H_A]||/scale = %.2e (expect ~0).', ...
            comm/scale);
end

% ================================================================
%  Step 3 -- Diagonalize H_G, cluster degenerate eigenvalues
% ================================================================
[V_G, D_G] = eig(H_G);
evals_G     = real(diag(D_G));
[evals_G, idx] = sort(evals_G);
V_G = V_G(:, idx);

tol_G    = max(1e-8, 1e-10 * (max(evals_G) - min(evals_G)));
clusters = {};
start    = 1;
for i = 2:Dsec
    if abs(evals_G(i) - evals_G(start)) > tol_G
        clusters{end+1} = start:(i-1); %#ok<AGROW>
        start = i;
    end
end
clusters{end+1} = start:Dsec;

% ================================================================
%  Step 4 -- Within each H_G-cluster, diagonalize H_A
% ================================================================
refined_V    = zeros(Dsec, Dsec);
cluster_info = struct('size',{},'A_evals',{},'cols',{});
col_offset   = 0;

for ci = 1:length(clusters)
    idx_ci = clusters{ci};
    V_ci   = V_G(:, idx_ci);
    nc     = length(idx_ci);

    H_A_sub = V_ci' * H_A * V_ci;
    H_A_sub = (H_A_sub + H_A_sub') / 2;

    [V_A, D_A] = eig(H_A_sub);
    evals_A    = sort(real(diag(D_A)));

    cols_range = col_offset + (1:nc);
    refined_V(:, cols_range) = V_ci * V_A;

    cluster_info(ci).size    = nc;
    cluster_info(ci).A_evals = evals_A;
    cluster_info(ci).cols    = cols_range;
    col_offset = col_offset + nc;
end

% ================================================================
%  Step 5 -- Group clusters into isotypic components
% ================================================================
all_A = vertcat(cluster_info.A_evals);
tol_A = max(1e-7, 1e-9 * max(abs(all_A(:))));

assigned = false(1, length(clusters));
isotypic = {};

for ci = 1:length(clusters)
    if assigned(ci), continue; end
    group       = ci;
    assigned(ci) = true;

    for cj = (ci+1):length(clusters)
        if assigned(cj), continue; end
        if cluster_info(cj).size ~= cluster_info(ci).size
            continue;
        end
        if max(abs(cluster_info(ci).A_evals - cluster_info(cj).A_evals)) < tol_A
            group       = [group, cj]; %#ok<AGROW>
            assigned(cj) = true;
        end
    end
    isotypic{end+1} = group; %#ok<AGROW>
end

% ================================================================
%  Step 6 -- Build output struct
% ================================================================
num_blocks = length(isotypic);
blocks     = struct('w',{},'s',{},'G_sub',{});

for bi = 1:num_blocks
    group = isotypic{bi};
    w     = cluster_info(group(1)).size;
    s_dim = length(group);

    first_cols = cluster_info(group(1)).cols;
    G_sub      = refined_V(:, first_cols);

    blocks(bi).w     = w;
    blocks(bi).s     = s_dim;
    blocks(bi).G_sub = G_sub;
end

% Final check: dimensions must sum to Dsec
total = sum([blocks.w] .* [blocks.s]);
assert(total == Dsec, ...
    'decompose_sector: block dims sum to %d, expected %d.', total, Dsec);

end

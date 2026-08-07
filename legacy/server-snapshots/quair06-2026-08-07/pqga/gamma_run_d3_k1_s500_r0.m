%% gamma_k.m
%  ---------------------------------------------------------------
%  Compute the k-copy programming cost gamma_k(CPTP, d)
%  via the block-diagonalised SDP of Appendix F.
%
%  The optimisation variable J_pm lives in the commutant algebra
%  B_{1,k}(d) (x) B_{k,1}(d) and is parametrised by
%  m = bl1 * bl2 real Brauer coefficients b_pm(j1,j2).
%
%  Three constraints act on the SAME coefficients:
%    (C1) PSD:  block-diagonal, sizes w1_lam * w2_mu
%    (C2) TP:   linear equalities on b (full Hilbert space)
%    (C3) Prog: linear equalities on b (d^2 x d^2 per channel)
%
%  Pipeline:
%    1. build_walled_brauer.m   -- diagram -> Dsec x Dsec matrix
%    2. decompose_brauer_algebra.m OR decompose_sector.m
%       -- extract reduced matrix elements red{lambda, j}
%    3. This script: assemble constraints and call CVX/MOSEK
%
%  Usage:
%    >> gamma_k          % runs with default d=2, k=2
%    Edit d, k, s below for other parameters.
%
%  Required: CVX (+ MOSEK), QETLAB
%  Required files: build_walled_brauer.m, decompose_brauer_algebra.m,
%                  decompose_sector.m, random_SU.m
%  ---------------------------------------------------------------
clear; clc;

%% ===== PARAMETERS ====================================================
d = 3;
k = 1;
s = 500;
method = 'hilbert';  % 'algebra' or 'hilbert'
                     %   algebra: decompose via bl-dim regular representation
                     %   hilbert: decompose via Dsec-dim random group element
% ======================================================================

n     = k + 1;
Dsec  = d^n;           % sector dimension: d^(k+1)
D     = d^(2*k+2);     % total Hilbert-space dimension
dk    = d^k;            % programmer dimension per side
I_d   = eye(d);
addpath(genpath("<QETLAB_ROOT>")); rng(0);
dim_tp = d^(2*k+1);    % TP constraint acts on this space

fprintf('============================================================\n');
fprintf('  gamma_%d(CPTP, d=%d)\n', k, d);
fprintf('  D = %d,  Dsec = %d,  method = %s\n', D, Dsec, method);
fprintf('============================================================\n');

%% ===== STEP 1: BUILD WALLED BRAUER BASIS =============================
fprintf('\n[1/5] Enumerating walled Brauer diagrams ...\n');

all_perms = perms(1:n);          % (k+1)! x (k+1) matrix
n_diag    = size(all_perms, 1);

% Sector 1: B_{1,k}(d) on V (x) (V*)^k
mats_1k = cell(1, n_diag);
for p = 1:n_diag
    mats_1k{p} = build_walled_brauer(all_perms(p,:), d, k, '1k');
end

% Sector 2: B_{k,1}(d) on V^k (x) V*
mats_k1 = cell(1, n_diag);
for p = 1:n_diag
    mats_k1{p} = build_walled_brauer(all_perms(p,:), d, k, 'k1');
end

% Find linearly independent bases
[basis_1k, bl1] = find_basis(mats_1k, Dsec);
[basis_k1, bl2] = find_basis(mats_k1, Dsec);
m = bl1 * bl2;
V1=zeros(Dsec^2,bl1); for jj=1:bl1, tmp=basis_1k{jj}; V1(:,jj)=tmp(:); end; V1i=pinv(V1); A1=zeros(bl1); for jj=1:bl1, tt=transpose(basis_1k{jj}); A1(:,jj)=real(V1i*tt(:)); end; V2=zeros(Dsec^2,bl2); for jj=1:bl2, tmp=basis_k1{jj}; V2(:,jj)=tmp(:); end; V2i=pinv(V2); A2=zeros(bl2); for jj=1:bl2, tt=transpose(basis_k1{jj}); A2(:,jj)=real(V2i*tt(:)); end; Aherm=kron(A1,A2); AhermC=Aherm-eye(bl1*bl2); AhermC(abs(AhermC)<1e-9)=0;

fprintf('      bl1 = %d,  bl2 = %d,  m = %d  (from %d diagrams)\n', ...
    bl1, bl2, m, n_diag);

%% ===== STEP 2: IRREP DECOMPOSITION ==================================
fprintf('[2/5] Decomposing walled Brauer algebras ...\n');

if strcmp(method, 'algebra')
    % Method A: decompose in the bl-dim algebra space
    % (scales to d=5,k=5: only 719x719 eigenproblems)
    [blocks1, red1] = decompose_brauer_algebra(basis_1k, Dsec);
    [blocks2, red2] = decompose_brauer_algebra(basis_k1, Dsec);
else
    % Method B: decompose in the Dsec-dim Hilbert space
    % (uses random SU(d) group elements; limited by Dsec)
    blocks1 = decompose_sector(basis_1k, d, k, '1k');
    blocks2 = decompose_sector(basis_k1, d, k, 'k1');
    % Extract reduced elements
    red1 = cell(length(blocks1), bl1);
    for bi = 1:length(blocks1)
        G = blocks1(bi).G_sub;
        for j = 1:bl1, red1{bi,j} = G' * basis_1k{j} * G; end
    end
    red2 = cell(length(blocks2), bl2);
    for bi = 1:length(blocks2)
        G = blocks2(bi).G_sub;
        for j = 1:bl2, red2{bi,j} = G' * basis_k1{j} * G; end
    end
end

nb1 = length(blocks1);
nb2 = length(blocks2);

fprintf('      Sector 1: %d blocks,  w = [', nb1);
fprintf('%d ', [blocks1.w]); fprintf(']\n');
fprintf('      Sector 2: %d blocks,  w = [', nb2);
fprintf('%d ', [blocks2.w]); fprintf(']\n');

max_block = max([blocks1.w]) * max([blocks2.w]);
fprintf('      PSD blocks: %d pairs,  largest: %d x %d\n', ...
    nb1*nb2, max_block, max_block);

%% ===== STEP 3: FULL BASIS & CONSTRAINT COEFFICIENTS ==================
fprintf('[3/5] Building full basis and constraint coefficients ...\n');

if D > 1e6
    error(['D = %d is too large for explicit constraint matrices.\n' ...
           'For d=%d k=%d, use the block-reduced TP/programming ' ...
           'formulation (see Appendix F of the paper).'], D, d, k);
end

% Permutation: grouped (sector) -> physical (interleaved) ordering
perm = zeros(1, 2*k+2);
perm(1) = 1;
for i = 1:k
    perm(i+1)   = 2*i;       % U*_i
    perm(k+1+i) = 2*i+1;     % V_i
end
perm(2*k+2) = 2*k+2;
ipm = zeros(1,2*k+2); ipm(perm) = 1:(2*k+2); perm = ipm;
dims_all = d * ones(1, 2*k+2);

% Full basis in physical ordering
B = cell(1, m);
for j1 = 1:bl1
    for j2 = 1:bl2
        B{(j1-1)*bl2 + j2} = ...
            PermuteSystems(kron(basis_1k{j1}, basis_k1{j2}), perm, dims_all);
    end
end

% TP coefficients: T(:,:,j) = Tr_{S'}[B{j}]
T = zeros(dim_tp, dim_tp, m);
for j = 1:m
    T(:,:,j) = PartialTrace(B{j}, 2*k+2, dims_all);
end

% Programming coefficients: P(:,:,j,c) = Tr_prog[B{j} * ins(C_c)]
fprintf('      Generating %d random channels ...\n', s);
JC  = zeros(d^2, d^2, s);
JCk = zeros(dk^2, dk^2, s);
for c = 1:s
    JC(:,:,c) = RandomSuperoperator(d) / d;
    temp = JC(:,:,c);
    for kk = 1:k-1
        temp = kron(temp, JC(:,:,c));
    end
    JCk(:,:,c) = temp;
end

P = zeros(d^2, d^2, m, s);
for c = 1:s
    ins = Tensor(I_d, JCk(:,:,c).', I_d);
    for j = 1:m
        P(:,:,j,c) = PartialTrace(B{j} * ins, 2, [d, dk^2, d]);
    end
end

%% ===== STEP 4: SOLVE BLOCK-DIAGONAL SDP =============================
fprintf('[4/5] Solving SDP (%d PSD blocks, max size %d) ...\n', ...
    nb1*nb2, max_block);

TPR = orth([reshape(T,[],m), -reshape(eye(dim_tp),[],1)]')'; APR=zeros(2*d^4*s,m); BPR=zeros(2*d^4*s,1); for c=1:s, Mc=reshape(P(:,:,:,c),d^4,m); rh=d*reshape(JC(:,:,c),d^4,1); APR((c-1)*2*d^4+(1:d^4),:)=real(Mc); BPR((c-1)*2*d^4+(1:d^4))=real(rh); APR((c-1)*2*d^4+d^4+(1:d^4),:)=imag(Mc); BPR((c-1)*2*d^4+d^4+(1:d^4))=imag(rh); end; RowB=orth([APR BPR]')'; ARED=RowB(:,1:end-1); BRED=RowB(:,end); AHR=orth(AhermC')'; clear APR BPR RowB;
cvx_solver mosek;
cvx_begin sdp quiet
    variable b1(m)
    variable b2(m)
    variable p1
    variable p2

    minimize(p1 + p2)
if ~isempty(AHR); AHR*b1 == 0; AHR*b2 == 0; end; ARED*(b1-b2) == BRED; TPR*[b1;p1] == 0; TPR*[b2;p2] == 0;

    % ---- (C1') Block-diagonal PSD ----
    for bi = 1:nb1
        for bj = 1:nb2
            J1_blk = 0;
            J2_blk = 0;
            for j1 = 1:bl1
                for j2 = 1:bl2
                    idx = (j1-1)*bl2 + j2;
                    R   = kron(red1{bi,j1}, red2{bj,j2});
                    J1_blk = J1_blk + b1(idx) * R;
                    J2_blk = J2_blk + b2(idx) * R;
                end
            end
            (J1_blk + ctranspose(J1_blk))/2 >= 0;  %#ok<VUNUS>
            (J2_blk + ctranspose(J2_blk))/2 >= 0;  %#ok<VUNUS>
        end
    end

    % ---- (C2') Trace preservation ----
    TP1 = zeros(dim_tp);
    TP2 = zeros(dim_tp);
    for j = 1:m
        
        
    end
      %#ok<EQEFF>
      %#ok<EQEFF>

    % ---- (C3') Programming ----
    for c = 1:s
        prog = zeros(d^2);
        for j = 1:m
            
        end
          %#ok<EQEFF>
    end
cvx_end

cost = p1 + p2;
if ~exist("results","dir"); mkdir("results"); end; save(sprintf("results/gamma_d%d_k%d_s%d_r%d.mat",d,k,s,0),"cost","d","k","s","method","cvx_status");

%% ===== STEP 5: REPORT ===============================================
fprintf('\n============================================================\n');
fprintf('  gamma_%d(CPTP, %d) = %.6f\n', k, d, cost);
fprintf('  CVX status: %s\n', cvx_status);
fprintf('============================================================\n');


%% =====================================================================
%                          LOCAL FUNCTIONS
%% =====================================================================

function [basis, bl] = find_basis(mats, Dsec)
%FIND_BASIS  Extract maximal linearly independent subset.
    n_mats = length(mats);
    V = zeros(Dsec^2, n_mats);
    for j = 1:n_mats
        V(:, j) = mats{j}(:);
    end
    [~, R, E] = qr(V, 0);
    tol = max(size(V)) * eps(norm(diag(R), 'inf'));
    bl  = sum(abs(diag(R)) > tol);
    keep = sort(E(1:bl));
    basis = mats(keep);
end

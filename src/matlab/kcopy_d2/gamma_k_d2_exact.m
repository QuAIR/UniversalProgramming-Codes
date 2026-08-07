function [cost, info] = gamma_k_d2_exact(k, opts)
%GAMMA_K_D2_EXACT  Exact row-space-reduced SDP for gamma_k(CPTP,d=2).
%
% This solver is the corrected exact d=2 reduction.  It keeps the full
% k-copy programming constraint row space, then removes redundant rows
% numerically.  It must not be confused with the old m=0,1 "linear" model,
% which is only a relaxation.
%
% The reduction has three layers:
%   1. Restrict J_+ and J_- to the SU(2) x SU(2) commutant.
%   2. Use block decomposition of the two walled-Brauer sectors for PSD.
%   3. Generate the full programming affine row space from CPTP samples and
%      keep an orthonormal independent row basis.
%
% Dependencies:
%   CVX, QETLAB, build_walled_brauer.m, decompose_sector.m, random_SU.m.

if nargin < 2 || isempty(opts)
    opts = struct();
end

d = 2;
if ~(isscalar(k) && k == round(k) && k >= 1)
    error('gamma_k_d2_exact:badK', 'k must be a positive integer.');
end

thisDir = fileparts(mfilename('fullpath'));
opts = local_defaults(opts, thisDir);
local_setup_paths(opts);

rng(opts.seed, 'twister');

n = k + 1;
Dsec = d^n;
D = d^(2*k + 2);
dk = d^k;

if opts.verbose
    fprintf('=== exact d=2 k-copy SDP: k=%d, D=%d ===\n', k, D);
end

% Build independent bases for B_{1,k}(2) and B_{k,1}(2).
allPerms = perms(1:n);
nDiag = size(allPerms, 1);
mats1 = cell(1, nDiag);
mats2 = cell(1, nDiag);
for p = 1:nDiag
    mats1{p} = build_walled_brauer(allPerms(p, :), d, k, '1k');
    mats2{p} = build_walled_brauer(allPerms(p, :), d, k, 'k1');
end
basis1 = local_independent_basis(mats1);
basis2 = local_independent_basis(mats2);
clear mats1 mats2

bl1 = numel(basis1);
bl2 = numel(basis2);
m = bl1 * bl2;
if opts.verbose
    fprintf('Brauer bases: bl1=%d bl2=%d product=%d\n', bl1, bl2, m);
end

% Decompose each sector, then precompute reduced block images.
blocks1 = decompose_sector(basis1, d, k, '1k');
blocks2 = decompose_sector(basis2, d, k, 'k1');
nb1 = numel(blocks1);
nb2 = numel(blocks2);
red1 = cell(nb1, bl1);
red2 = cell(nb2, bl2);
for bi = 1:nb1
    G = blocks1(bi).G_sub;
    for j = 1:bl1
        red1{bi, j} = G' * basis1{j} * G;
    end
end
for bi = 1:nb2
    G = blocks2(bi).G_sub;
    for j = 1:bl2
        red2{bi, j} = G' * basis2{j} * G;
    end
end
if opts.verbose
    fprintf('sector blocks: %d x %d, w1=[%s], w2=[%s]\n', ...
        nb1, nb2, num2str([blocks1.w]), num2str([blocks2.w]));
end

% Hermiticity: represent transpose on each sector basis and keep the
% fixed-point null space for the product coefficient vector.
V1 = zeros(Dsec^2, bl1);
for j = 1:bl1
    V1(:, j) = basis1{j}(:);
end
V1i = pinv(V1);
A1 = zeros(bl1);
for j = 1:bl1
    tmp = transpose(basis1{j});
    A1(:, j) = real(V1i * tmp(:));
end

V2 = zeros(Dsec^2, bl2);
for j = 1:bl2
    V2(:, j) = basis2{j}(:);
end
V2i = pinv(V2);
A2 = zeros(bl2);
for j = 1:bl2
    tmp = transpose(basis2{j});
    A2(:, j) = real(V2i * tmp(:));
end

Aherm = kron(A1, A2) - eye(m);
Aherm(abs(Aherm) < 1e-9) = 0;
[~, Sv, Vv] = svd(Aherm);
NS = Vv(:, diag(Sv) < opts.hermTol);
nn = size(NS, 2);
clear Aherm A1 A2
if opts.verbose
    fprintf('Hermitian coefficient dimension: %d of %d\n', nn, m);
end

% Exact TP family via Gram row reduction.
T2v = zeros(d^(2*k), bl2);
for j = 1:bl2
    t2 = PartialTrace(basis2{j}, k + 1, d * ones(1, k + 1));
    T2v(:, j) = t2(:);
end
Q1 = orth(V1);
G1 = Q1' * V1;
g1 = Q1' * reshape(eye(Dsec), [], 1);
Q2 = orth(T2v);
G2 = Q2' * T2v;
g2 = Q2' * reshape(eye(dk), [], 1);
TPb = kron(G1, G2) * NS;
tpv = kron(g1, g2);
clear V1 V2 T2v Q1 Q2 G1 G2 g1 g2
if opts.verbose
    fprintf('TP rows: %d\n', size(TPb, 1));
end

% Full programming row space.  The samples are only used to span and reduce
% the polynomial identity rows; a fresh residual is computed after solving.
[M1, M2] = local_program_maps(basis1, basis2, d, k, dk);
[ARED, BRED, progRows] = local_program_rows(M1, M2, NS, d, k, dk, opts.s);
if opts.checkExpectedRows
    local_check_expected_rows(k, progRows);
end
if opts.verbose
    fprintf('programming rows: %d (sample count %d)\n', progRows, opts.s);
end

% Vectorized PSD block maps.
nbp = nb1 * nb2;
Rmat = cell(nbp, 1);
wsz = zeros(nbp, 1);
for bi = 1:nb1
    for bj = 1:nb2
        ip = (bi - 1) * nb2 + bj;
        w = blocks1(bi).w * blocks2(bj).w;
        wsz(ip) = w;
        RM = zeros(w * w, m);
        for j1 = 1:bl1
            for j2 = 1:bl2
                idx = (j1 - 1) * bl2 + j2;
                kr = kron(red1{bi, j1}, red2{bj, j2});
                RM(:, idx) = kr(:);
            end
        end
        Rmat{ip} = RM * NS;
    end
end

ticSolve = tic;
cvx_begin sdp quiet
    cvx_solver(opts.solver)
    cvx_precision high
    variable y1v(nn)
    variable y2v(nn)
    variable p1
    variable p2
    minimize(p1 + p2)
    ARED * (y1v - y2v) == BRED;
    TPb * y1v == p1 * tpv;
    TPb * y2v == p2 * tpv;
    for ip = 1:nbp
        w = wsz(ip);
        Jb1 = reshape(Rmat{ip} * y1v, w, w);
        Jb2 = reshape(Rmat{ip} * y2v, w, w);
        (Jb1 + Jb1') / 2 >= 0;
        (Jb2 + Jb2') / 2 >= 0;
    end
cvx_end
solveTime = toc(ticSolve);

b1 = NS * y1v;
b2 = NS * y2v;
cost = p1 + p2;
y1 = NS' * b1;
y2 = NS' * b2;

[mineig, maxNonHerm] = local_block_certificate(Rmat, wsz, y1, y2);
tpResidual = max(norm(TPb * y1 - p1 * tpv), norm(TPb * y2 - p2 * tpv));
freshResidual = local_fresh_program_residual(M1, M2, b1, b2, d, k, dk, ...
    opts.certFresh, opts.freshSeed);
[blocksPlus, blocksMinus, blocksPlusRaw, blocksMinusRaw, blockMeta] = ...
    local_saved_blocks(Rmat, wsz, y1, y2, blocks1, blocks2);

info = struct();
info.d = d;
info.k = k;
info.cost = cost;
info.pplus = p1;
info.pminus = p2;
info.status = cvx_status;
info.solveTime = solveTime;
info.sampleCount = opts.s;
info.progRows = progRows;
info.tpRows = size(TPb, 1);
info.hermDim = nn;
info.basisDims = [bl1, bl2];
info.blockWidths1 = [blocks1.w];
info.blockWidths2 = [blocks2.w];
info.blockGrid = [nb1, nb2];
info.minEig = mineig;
info.maxNonHerm = maxNonHerm;
info.tpResidual = tpResidual;
info.freshProgResidual = freshResidual;

if opts.verbose
    fprintf('SOLVE: gamma_%d(CPTP,2)=%.12f [%s]\n', k, cost, cvx_status);
    fprintf('CERT: min eig %.3e ; nonherm %.2e ; TP %.2e ; fresh prog %.3e (%d ch)\n', ...
        mineig, maxNonHerm, tpResidual, freshResidual, opts.certFresh);
end

if opts.saveResult
    if ~exist(opts.resultsDir, 'dir')
        mkdir(opts.resultsDir);
    end
    coeffPlus = b1;
    coeffMinus = b2;
    yPlus = y1v;
    yMinus = y2v;
    save(fullfile(opts.resultsDir, sprintf('exact_d2_k%d.mat', k)), ...
        'cost', 'info', 'b1', 'b2', 'coeffPlus', 'coeffMinus', ...
        'yPlus', 'yMinus', 'p1', 'p2', ...
        'blocksPlus', 'blocksMinus', 'blocksPlusRaw', 'blocksMinusRaw', ...
        'blockMeta', '-v7.3');
end

end

function opts = local_defaults(opts, thisDir)
defaults = struct();
defaults.seed = 0;
defaults.freshSeed = 777;
defaults.s = 500;
defaults.certFresh = 50;
defaults.verbose = true;
defaults.solver = 'sdpt3';
defaults.hermTol = 1e-7;
defaults.setupCvx = false;
defaults.cvxRoot = '';
defaults.qetlabPath = '';
defaults.helperPath = fullfile(thisDir, '..', 'common');
defaults.saveResult = true;
defaults.resultsDir = fullfile(thisDir, 'results');
defaults.checkExpectedRows = true;

fields = fieldnames(defaults);
for i = 1:numel(fields)
    f = fields{i};
    if ~isfield(opts, f) || isempty(opts.(f))
        opts.(f) = defaults.(f);
    end
end
end

function local_setup_paths(opts)
if ~isempty(opts.helperPath) && exist(opts.helperPath, 'dir')
    addpath(opts.helperPath);
end
if ~isempty(opts.qetlabPath) && exist(opts.qetlabPath, 'dir')
    addpath(genpath(opts.qetlabPath));
end
if opts.setupCvx
    if ~isempty(opts.cvxRoot) && exist(opts.cvxRoot, 'dir')
        addpath(genpath(opts.cvxRoot));
    end
    cvx_setup;
end
end

function basis = local_independent_basis(mats)
nMats = numel(mats);
V = zeros(numel(mats{1}), nMats);
for j = 1:nMats
    V(:, j) = mats{j}(:);
end
[~, Rq, Eq] = qr(V, 0);
tol = max(size(V)) * eps(norm(diag(Rq), 'inf'));
rankV = sum(abs(diag(Rq)) > tol);
keep = sort(Eq(1:rankV));
basis = mats(keep);
end

function [M1, M2] = local_program_maps(basis1, basis2, d, k, dk)
bl1 = numel(basis1);
bl2 = numel(basis2);
M1 = cell(1, bl1);
M2 = cell(1, bl2);
for j = 1:bl1
    R4 = reshape(full(basis1{j}), [dk, d, dk, d]);
    M1{j} = reshape(permute(R4, [2, 4, 1, 3]), d*d, dk*dk);
end
for j = 1:bl2
    R4 = reshape(full(basis2{j}), [d, dk, d, dk]);
    M2{j} = reshape(permute(R4, [1, 3, 2, 4]), d*d, dk*dk);
end
end

function [ARED, BRED, progRows] = local_program_rows(M1, M2, NS, d, k, dk, s)
bl1 = numel(M1);
bl2 = numel(M2);
m = bl1 * bl2;
APR = zeros(2 * d^4 * s, m);
BPR = zeros(2 * d^4 * s, 1);
Pc = zeros(d^2, d^2, m);
gperm = [1:2:(2*k - 1), 2:2:(2*k)];

for c = 1:s
    JC = RandomSuperoperator(d) / d;
    Y = local_program_Y(JC, d, k, dk, gperm);
    for j1 = 1:bl1
        Z = M1{j1} * Y;
        for j2 = 1:bl2
            idx = (j1 - 1) * bl2 + j2;
            G = Z * M2{j2}.';
            R4g = reshape(G, [d, d, d, d]);
            Pc(:, :, idx) = reshape(permute(R4g, [3, 1, 4, 2]), d^2, d^2);
        end
    end
    Mc = reshape(Pc, d^4, m);
    rhs = d * reshape(JC, d^4, 1);
    rows = (c - 1) * 2 * d^4;
    APR(rows + (1:d^4), :) = real(Mc);
    BPR(rows + (1:d^4)) = real(rhs);
    APR(rows + d^4 + (1:d^4), :) = imag(Mc);
    BPR(rows + d^4 + (1:d^4)) = imag(rhs);
end

APR = APR * NS;
RowB = orth([APR, BPR]')';
ARED = RowB(:, 1:end-1);
BRED = RowB(:, end);
progRows = size(ARED, 1);
end

function Y = local_program_Y(JC, d, k, dk, gperm)
temp = JC;
for kk = 1:(k - 1)
    temp = kron(temp, JC);
end
Xt = temp.';
Xg = PermuteSystems(Xt, gperm, d * ones(1, 2*k));
R4x = reshape(Xg, [dk, dk, dk, dk]);
Y = reshape(permute(R4x, [4, 2, 3, 1]), dk^2, dk^2);
end

function local_check_expected_rows(k, progRows)
% These are the programming rows after restricting to the Hermitian
% coefficient null space.  The unreduced programming family has ranks
% 3, 8, 18, 36, ... for k=1,2,3,4 before this projection.
expected = [3, 7, 16, 29];
if k <= numel(expected) && progRows ~= expected(k)
    error('gamma_k_d2_exact:rowRank', ...
        'Programming row rank for k=%d is %d, expected %d.', ...
        k, progRows, expected(k));
end
end

function [mineig, maxNonHerm] = local_block_certificate(Rmat, wsz, y1, y2)
mineig = inf;
maxNonHerm = 0;
for ip = 1:numel(Rmat)
    w = wsz(ip);
    Jb1 = reshape(Rmat{ip} * y1, w, w);
    Jb2 = reshape(Rmat{ip} * y2, w, w);
    H1 = (Jb1 + Jb1') / 2;
    H2 = (Jb2 + Jb2') / 2;
    mineig = min([mineig, min(real(eig(H1))), min(real(eig(H2)))]);
    maxNonHerm = max([maxNonHerm, norm(Jb1 - Jb1', 'fro'), ...
        norm(Jb2 - Jb2', 'fro')]);
end
end

function [blocksPlus, blocksMinus, blocksPlusRaw, blocksMinusRaw, blockMeta] = ...
    local_saved_blocks(Rmat, wsz, y1, y2, blocks1, blocks2)
nb1 = numel(blocks1);
nb2 = numel(blocks2);
blocksPlus = cell(nb1, nb2);
blocksMinus = cell(nb1, nb2);
blocksPlusRaw = cell(nb1, nb2);
blocksMinusRaw = cell(nb1, nb2);
blockMeta = struct('pairIndex', {}, 'sector1', {}, 'sector2', {}, ...
    'width', {}, 'w1', {}, 'w2', {}, 's1', {}, 's2', {});

for bi = 1:nb1
    for bj = 1:nb2
        ip = (bi - 1) * nb2 + bj;
        w = wsz(ip);
        Jp = reshape(Rmat{ip} * y1, w, w);
        Jm = reshape(Rmat{ip} * y2, w, w);
        blocksPlusRaw{bi, bj} = full(Jp);
        blocksMinusRaw{bi, bj} = full(Jm);
        blocksPlus{bi, bj} = full((Jp + Jp') / 2);
        blocksMinus{bi, bj} = full((Jm + Jm') / 2);
        blockMeta(ip).pairIndex = ip;
        blockMeta(ip).sector1 = bi;
        blockMeta(ip).sector2 = bj;
        blockMeta(ip).width = w;
        blockMeta(ip).w1 = blocks1(bi).w;
        blockMeta(ip).w2 = blocks2(bj).w;
        blockMeta(ip).s1 = blocks1(bi).s;
        blockMeta(ip).s2 = blocks2(bj).s;
    end
end
end

function fres = local_fresh_program_residual(M1, M2, b1, b2, d, k, dk, nf, seed)
bl1 = numel(M1);
bl2 = numel(M2);
gperm = [1:2:(2*k - 1), 2:2:(2*k)];
fres = 0;
rng(seed, 'twister');
for c = 1:nf
    JC = RandomSuperoperator(d) / d;
    Y = local_program_Y(JC, d, k, dk, gperm);
    prog = zeros(d^2);
    for j1 = 1:bl1
        Z = M1{j1} * Y;
        for j2 = 1:bl2
            idx = (j1 - 1) * bl2 + j2;
            G = Z * M2{j2}.';
            R4g = reshape(G, [d, d, d, d]);
            Pj = reshape(permute(R4g, [3, 1, 4, 2]), d^2, d^2);
            prog = prog + (b1(idx) - b2(idx)) * Pj;
        end
    end
    fres = max(fres, norm(prog - d * JC, 'fro'));
end
end

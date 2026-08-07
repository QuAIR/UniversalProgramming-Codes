function test_quair06_evidence
% Load-only checks for quair06 evidence. This file must never invoke a solve.

repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
resultRoot = fullfile(repoRoot, 'results', 'diagnostic');

k5 = load(fullfile(resultRoot, 'quair06_exact_d2_k5_saved_blocks.mat'));
required = {'b1', 'b2', 'blockMeta', 'blocksMinus', 'blocksMinusRaw', ...
    'blocksPlus', 'blocksPlusRaw', 'coeffMinus', 'coeffPlus', 'cost', ...
    'info', 'p1', 'p2', 'yMinus', 'yPlus'};
assert(all(isfield(k5, required)));
assert(abs(k5.cost - 1.35153816332987) < 1e-12);
assert(abs(k5.p1 - 1.17576941409901) < 1e-12);
assert(abs(k5.p2 - 0.175768749230858) < 1e-12);
assert(k5.info.sampleCount == 500);
assert(k5.info.minEig > 0);
assert(k5.info.tpResidual < 3e-6);
assert(k5.info.freshProgResidual < 1.1e-6);

k56 = load(fullfile(resultRoot, 'quair06_exact_k56_checkpoint.mat'));
assert(isequal(k56.Tpartial.ks(:).', [5 6]));
assert(abs(k56.Tpartial.gamma(1) - k5.cost) < 1e-12);
assert(isnan(k56.Tpartial.gamma(2)));
assert(isnan(k56.Tpartial.runtime_s(2)));
assert(k56.opts.s == 500);

comparison = load(fullfile(resultRoot, 'quair06_full_vs_linear_k1_k3.mat'));
assert(isequal(comparison.ks(:).', [1 2 3 4]));
assert(all(isfinite(comparison.gam_full(1:3))));
assert(all(isfinite(comparison.gam_linear(1:3))));
assert(isnan(comparison.gam_full(4)));
assert(isnan(comparison.gam_linear(4)));

fprintf('quair06 evidence load-only checks passed.\n');
end

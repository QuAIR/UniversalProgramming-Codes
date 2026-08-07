%% run_kcopy_d2.m -- local driver for the corrected d=2 exact SDP
%
% The main path is gamma_k_d2_exact.m.  The legacy gamma_k_d2.m entry point is
% used only for the optional m=0,1 relaxation comparison.

clear; clc;
warning('legacy:qubitReducedPrototype', ...
    'Archived provenance runner: not a supported experiment entry point.');
scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(scriptDir));
addpath(fullfile(repoRoot, 'src', 'matlab'));
addpath(scriptDir);
cfg = up_config();
up_setup(cfg, false);
outputDir = fullfile(cfg.resultsRoot, 'legacy', 'qubit-reduced-prototype');
if exist(outputDir, 'dir') ~= 7
    mkdir(outputDir);
end

opts = struct();
opts.solver = 'sdpt3';
opts.s = 500;
opts.certFresh = 20;
opts.verbose = true;
opts.saveResult = true;

kmax = 3;
ks = 1:kmax;

%% ---- 0. exact self-test ----
[g1, info1] = gamma_k_d2_exact(1, opts);
assert(abs(g1 - 5.5) < 1e-5, ...
    'SELF-TEST FAILED: gamma_1 = %.6f, expected 5.5.', g1);
assert(info1.progRows == 3, ...
    'SELF-TEST FAILED: expected 3 exact programming rows at k=1.');
fprintf('[self-test passed] gamma_1 = %.8f, progRows=%d\n\n', ...
    g1, info1.progRows);

%% ---- 1. exact sequence ----
gam_exact = nan(1, kmax);
pp = nan(1, kmax);
pm = nan(1, kmax);
progRows = nan(1, kmax);
freshResidual = nan(1, kmax);

for ii = 1:kmax
    k = ks(ii);
    t = tic;
    [gam_exact(ii), info] = gamma_k_d2_exact(k, opts);
    pp(ii) = info.pplus;
    pm(ii) = info.pminus;
    progRows(ii) = info.progRows;
    freshResidual(ii) = info.freshProgResidual;
    fprintf('k=%d exact gamma=%.12f status=%s rows=%d fresh=%.2e runtime=%.1fs\n', ...
        k, gam_exact(ii), info.status, progRows(ii), freshResidual(ii), toc(t));
    assert(abs((pp(ii) - pm(ii)) - 1) < 1e-4, ...
        'p+ - p- != 1 at k=%d.', k);
end

%% ---- 2. optional relaxation diagnostic ----
fprintf('\n--- legacy m=0,1 relaxation gap diagnostic ---\n');
gam_linear = nan(1, kmax);
for ii = 1:kmax
    k = ks(ii);
    gam_linear(ii) = gamma_k_d2(k, 'linear', false);
    fprintf('k=%d exact=%.8f linear=%.8f gap=%.3e\n', ...
        k, gam_exact(ii), gam_linear(ii), gam_exact(ii) - gam_linear(ii));
end

save(fullfile(outputDir, 'kcopy_d2_results.mat'), 'gam_exact', 'gam_linear', 'pp', 'pm', ...
    'progRows', 'freshResidual', 'kmax');
fprintf('\nSaved kcopy_d2_results.mat\n');

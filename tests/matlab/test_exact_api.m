clear; clc;

repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();
up_setup(cfg, false);

opts = struct();
opts.setupCvx = false;
opts.solver = cfg.solver;
opts.s = 500;
opts.certFresh = 50;
opts.verbose = true;
opts.saveResult = false;

[cost, info] = gamma_k_d2_exact(1, opts);

assert(abs(cost - 5.5) < 1e-5, ...
    'Expected gamma_1(CPTP,2)=5.5, got %.12f', cost);
assert(info.progRows == 3, ...
    'Expected 3 exact programming rows for d=2,k=1, got %d', ...
    info.progRows);
assert(info.freshProgResidual < 1e-6, ...
    'Fresh programming residual too large: %.3e', ...
    info.freshProgResidual);

fprintf('TEST_EXACT_API_OK gamma=%.12f progRows=%d fresh=%.3e\n', ...
    cost, info.progRows, info.freshProgResidual);

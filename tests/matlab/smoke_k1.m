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

[cost, ~] = gamma_k_d2_exact(1, opts);
assert(abs(cost - 5.5) < 1e-5, ...
    'Expected gamma_1(CPTP,2)=5.5, got %.12f', cost);
fprintf('SMOKE_K1_OK gamma=%.12f\n', cost);

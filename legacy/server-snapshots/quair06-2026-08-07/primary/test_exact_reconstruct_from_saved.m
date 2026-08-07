clear; clc;

addpath(pwd);

common = struct();
common.setupCvx = true;
common.cvxRoot = '<CVX_ROOT>';
common.qetlabPath = '<QETLAB_ROOT>';
common.solver = 'sdpt3';
common.s = 80;
common.certFresh = 3;
common.verbose = false;
common.saveResult = true;

srcOpts = common;
srcOpts.resultsDir = tempname(pwd);
[cost1, ~] = gamma_k_d2_exact(1, srcOpts);
srcFile = fullfile(srcOpts.resultsDir, 'exact_d2_k1.mat');

reconOpts = common;
reconOpts.setupCvx = false;
reconOpts.resultsDir = tempname(pwd);
reconOpts.initialSolutionFile = srcFile;
reconOpts.loadedProgRows = 3;
[cost2, info2] = gamma_k_d2_exact(1, reconOpts);

assert(strcmp(info2.status, 'LoadedSolution'), ...
    'Expected reconstruction status LoadedSolution, got %s.', info2.status);
assert(abs(cost1 - cost2) < 1e-8, ...
    'Reconstructed cost %.12f differs from source %.12f.', cost2, cost1);

S = load(fullfile(reconOpts.resultsDir, 'exact_d2_k1.mat'));
assert(isfield(S, 'blocksPlus') && isfield(S, 'blocksMinus'), ...
    'Reconstructed save is missing block matrices.');

fprintf('TEST_EXACT_RECONSTRUCT_FROM_SAVED_OK gamma=%.12f blocks=%d\n', ...
    cost2, numel(S.blocksPlus));

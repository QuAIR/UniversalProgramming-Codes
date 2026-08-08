clear; clc;

caseRoot = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(caseRoot));
addpath(caseRoot);
addpath(fullfile(repoRoot, 'src', 'matlab'));

cfg = up_config();
opts = struct('solve', false, 'verbose', true, ...
    'solver', cfg.solver, 'cvxRoot', cfg.cvxRoot, ...
    'qetlabRoot', cfg.qetlabRoot, 'saveResult', false, ...
    'resultPath', fullfile(cfg.resultsRoot, ...
        'strict_submultiplicativity.mat'));

report = verify_strict_submultiplicativity(opts); %#ok<NASGU>

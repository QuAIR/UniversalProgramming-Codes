clear; clc;

repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(repoRoot, 'experiments', 'strict_submultiplicativity'));

report = verify_strict_submultiplicativity(struct( ...
    'solve', false, 'verbose', false));

assert(report.certificateNnz == 360);
assert(report.hermiticityResidual < 1e-12);
assert(report.outputTraceResidual < 1e-12);
assert(max(report.annihilationResiduals, [], 'all') < 1e-12);

fprintf('TEST_STRICT_SUBMULT_OK residual=%.3e\n', ...
    max(report.annihilationResiduals, [], 'all'));

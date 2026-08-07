clear; clc;

repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();
up_setup(cfg, false);

if exist(cfg.resultsRoot, 'dir') ~= 7
    mkdir(cfg.resultsRoot);
end
resultsDir = tempname(cfg.resultsRoot);
cleanupObj = onCleanup(@() local_remove_directory(resultsDir)); %#ok<NASGU>

opts = struct();
opts.setupCvx = false;
opts.solver = cfg.solver;
opts.s = 500;
opts.certFresh = 50;
opts.verbose = false;
opts.saveResult = true;
opts.resultsDir = resultsDir;

[cost, info] = gamma_k_d2_exact(1, opts); %#ok<ASGLU>
outFile = fullfile(opts.resultsDir, 'exact_d2_k1.mat');
assert(exist(outFile, 'file') == 2, 'Expected saved result file: %s', outFile);

S = load(outFile);

required = {'blocksPlus', 'blocksMinus', 'blocksPlusRaw', 'blocksMinusRaw', ...
    'blockMeta', 'coeffPlus', 'coeffMinus', 'yPlus', 'yMinus', 'p1', ...
    'p2', 'info'};
for i = 1:numel(required)
    assert(isfield(S, required{i}), ...
        'Saved result is missing field "%s".', required{i});
end

assert(iscell(S.blocksPlus) && iscell(S.blocksMinus), ...
    'blocksPlus and blocksMinus must be cell arrays.');
assert(isequal(size(S.blocksPlus), size(S.blocksMinus)), ...
    'blocksPlus and blocksMinus must have matching block grids.');
assert(numel(S.blocksPlus) == numel(S.blockMeta), ...
    'blockMeta must describe every saved block.');
assert(isnumeric(S.blocksPlus{1}) && isnumeric(S.blocksMinus{1}), ...
    'Saved block entries must be numeric matrices.');
assert(S.info.sampleCount == 500, ...
    'Saved result did not retain the required 500-sample setting.');
assert(S.info.certFresh == 50, ...
    'Saved result did not retain the required 50 fresh-channel checks.');
assert(abs(cost - S.info.cost) < 1e-7, ...
    'Saved optimized cost does not match the returned cost.');
assert(abs(S.p1 + S.p2 - S.info.cost) < 1e-7, ...
    'Saved p1+p2 does not match optimized cost.');

fprintf('TEST_EXACT_SAVED_BLOCKS_OK gamma=%.12f blocks=%d\n', ...
    S.info.cost, numel(S.blocksPlus));

function local_remove_directory(directory)
if exist(directory, 'dir') == 7
    rmdir(directory, 's');
end
end

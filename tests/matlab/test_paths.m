clear; clc;

% This test intentionally does not call up_setup: path resolution must remain
% testable on machines where the optional CVX and QETLAB dependencies are absent.
repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();

assert(strcmp(cfg.repoRoot, repoRoot), ...
    'up_config resolved an unexpected repository root.');
addpath(fullfile(cfg.repoRoot, 'src', 'matlab', 'common'));
addpath(fullfile(cfg.repoRoot, 'src', 'matlab', 'kcopy_d2'));

local_assert_in_repo('build_walled_brauer', cfg.repoRoot);
local_assert_in_repo('decompose_sector', cfg.repoRoot);
local_assert_in_repo('gamma_k_d2_exact', cfg.repoRoot);

fprintf('TEST_PATHS_OK repo=%s\n', cfg.repoRoot);

function local_assert_in_repo(functionName, repoRoot)
resolved = which(functionName);
assert(~isempty(resolved), 'Could not resolve %s.', functionName);

prefix = [repoRoot filesep];
assert(strncmpi(resolved, prefix, numel(prefix)), ...
    '%s resolved outside the repository: %s', functionName, resolved);
end

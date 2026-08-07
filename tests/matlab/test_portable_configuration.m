function tests = test_portable_configuration
% Behavioral tests for the portable MATLAB configuration entry points.

tests = functiontests(localfunctions);
end

function setupOnce(testCase)
testCase.TestData.repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
testCase.TestData.matlabRoot = fullfile(testCase.TestData.repoRoot, 'src', ...
    'matlab');
testCase.TestData.originalPath = path;
testCase.TestData.tempRoot = tempname;
testCase.TestData.environment = local_environment_values();
mkdir(testCase.TestData.tempRoot);

testCase.addTeardown(@() local_restore_environment(testCase.TestData.environment));
testCase.addTeardown(@() local_restore_path(testCase.TestData.originalPath));
testCase.addTeardown(@() local_remove_directory(testCase.TestData.tempRoot));
testCase.addTeardown(@local_restore_default_path);
end

function setup(testCase)
restoredefaultpath;
addpath(testCase.TestData.matlabRoot);
clear cvx_begin cvx_setup RandomSuperoperator sdpvar
local_clear_environment();
end

function testConfigDefaultsAndResolvedPaths(testCase)
cfg = up_config();

verifyEqual(testCase, cfg.repoRoot, testCase.TestData.repoRoot);
verifyEqual(testCase, cfg.resultsRoot, fullfile(testCase.TestData.repoRoot, ...
    'results', 'generated'));
verifyEqual(testCase, cfg.cvxRoot, '');
verifyEqual(testCase, cfg.qetlabRoot, '');
verifyEqual(testCase, cfg.yalmipRoot, '');
verifyEqual(testCase, cfg.matlabBin, 'matlab');
verifyEqual(testCase, cfg.solver, 'sdpt3');
end

function testConfigReadsEnvironmentValues(testCase)
values = local_test_values('environment');
local_set_environment(values);

cfg = up_config();

local_verify_config(testCase, cfg, values);
end

function testConfigOverridesTakePrecedenceOverEnvironment(testCase)
local_set_environment(local_test_values('environment'));
overrides = local_test_values('override');

cfg = up_config(overrides);

local_verify_config(testCase, cfg, overrides);
end

function testSetupReportsMissingCVX(testCase)
cfg = up_config();

verifyError(testCase, @() up_setup(cfg, false), 'up_setup:missingCVX');
end

function testSetupReportsMissingQETLABAfterConfiguredCVX(testCase)
cvxRoot = local_fake_cvx(testCase, false);
cfg = up_config(struct('cvxRoot', cvxRoot));

verifyError(testCase, @() up_setup(cfg, false), 'up_setup:missingQETLAB');
end

function testSetupOnlyRequiresYalmipWhenRequested(testCase)
cvxRoot = local_fake_cvx(testCase, false);
qetlabRoot = local_fake_function(testCase, 'qetlab', ...
    'RandomSuperoperator', 'function RandomSuperoperator; end');
cfg = up_config(struct('cvxRoot', cvxRoot, 'qetlabRoot', qetlabRoot));

up_setup(cfg, false);
verifyError(testCase, @() up_setup(cfg, true), 'up_setup:missingYALMIP');
end

function testSetupRunsCvxSetupWhenConfiguredCvxIsFirstAdded(testCase)
cvxRoot = local_fake_cvx(testCase, false);
qetlabRoot = local_fake_function(testCase, 'qetlab', ...
    'RandomSuperoperator', 'function RandomSuperoperator; end');
cfg = up_config(struct('cvxRoot', cvxRoot, 'qetlabRoot', qetlabRoot));

up_setup(cfg, false);

verifyEqual(testCase, getenv('UP_TEST_CVX_SETUP_CALLED'), 'true');
end

function testSetupSkipsCvxSetupWhenCvxIsAlreadyAvailable(testCase)
cvxRoot = local_fake_cvx(testCase, true);
qetlabRoot = local_fake_function(testCase, 'qetlab', ...
    'RandomSuperoperator', 'function RandomSuperoperator; end');
addpath(cvxRoot);
cfg = up_config(struct('qetlabRoot', qetlabRoot));

up_setup(cfg, false);
end

function values = local_test_values(prefix)
values = struct();
values.cvxRoot = [prefix '-cvx'];
values.qetlabRoot = [prefix '-qetlab'];
values.yalmipRoot = [prefix '-yalmip'];
values.matlabBin = [prefix '-matlab'];
values.solver = [prefix '-solver'];
values.resultsRoot = [prefix '-results'];
end

function local_verify_config(testCase, cfg, values)
verifyEqual(testCase, cfg.cvxRoot, values.cvxRoot);
verifyEqual(testCase, cfg.qetlabRoot, values.qetlabRoot);
verifyEqual(testCase, cfg.yalmipRoot, values.yalmipRoot);
verifyEqual(testCase, cfg.matlabBin, values.matlabBin);
verifyEqual(testCase, cfg.solver, values.solver);
verifyEqual(testCase, cfg.resultsRoot, values.resultsRoot);
end

function root = local_fake_cvx(testCase, failIfSetupRuns)
if failIfSetupRuns
    setupSource = [ ...
        'function cvx_setup', newline, ...
        'error(''test_portable_configuration:cvxSetupCalled'', ...', newline, ...
        '    ''cvx_setup should not run when cvx_begin is available.'');', newline, ...
        'end'];
else
    setupSource = [ ...
        'function cvx_setup', newline, ...
        'setenv(''UP_TEST_CVX_SETUP_CALLED'', ''true'');', newline, ...
        'end'];
end

root = local_fake_function(testCase, 'cvx', 'cvx_begin', ...
    'function cvx_begin; end');
local_write_function(fullfile(root, 'cvx_setup.m'), setupSource);
end

function root = local_fake_function(testCase, directoryName, functionName, source)
root = tempname(fullfile(testCase.TestData.tempRoot, directoryName));
mkdir(root);
local_write_function(fullfile(root, [functionName '.m']), source);
end

function local_write_function(filename, source)
file = fopen(filename, 'w');
assert(file ~= -1, 'test_portable_configuration:writeFailed', ...
    'Could not create fake dependency function.');
cleanup = onCleanup(@() fclose(file));
fprintf(file, '%s\n', source);
end

function values = local_environment_values()
names = local_environment_names();
values = struct();
for index = 1:numel(names)
    values.(names{index}) = getenv(names{index});
end
end

function local_clear_environment()
names = local_environment_names();
for index = 1:numel(names)
    setenv(names{index}, '');
end
end

function local_set_environment(values)
setenv('UP_CVX_ROOT', values.cvxRoot);
setenv('UP_QETLAB_ROOT', values.qetlabRoot);
setenv('UP_YALMIP_ROOT', values.yalmipRoot);
setenv('UP_MATLAB_BIN', values.matlabBin);
setenv('UP_SDP_SOLVER', values.solver);
setenv('UP_RESULTS_ROOT', values.resultsRoot);
end

function local_restore_environment(values)
names = local_environment_names();
for index = 1:numel(names)
    setenv(names{index}, values.(names{index}));
end
end

function local_restore_path(originalPath)
path(originalPath);
end

function local_restore_default_path()
restoredefaultpath;
end

function names = local_environment_names()
names = {'UP_CVX_ROOT', 'UP_QETLAB_ROOT', 'UP_YALMIP_ROOT', ...
    'UP_MATLAB_BIN', 'UP_SDP_SOLVER', 'UP_RESULTS_ROOT', ...
    'UP_TEST_CVX_SETUP_CALLED'};
end

function local_remove_directory(directory)
if exist(directory, 'dir') == 7
    rmdir(directory, 's');
end
end

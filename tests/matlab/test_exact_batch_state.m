function tests = test_exact_batch_state
% Dependency-free state tests shared by the exact batch runners.

tests = functiontests(localfunctions);
end

function setupOnce(testCase)
repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
testCase.TestData.commonRoot = fullfile(repoRoot, 'src', 'matlab', 'common');
addpath(testCase.TestData.commonRoot);
testCase.addTeardown(@() rmpath(testCase.TestData.commonRoot));
end

function testCompletedRequiresExplicitSuccessStatus(testCase)
artifact = [tempname '.mat'];
cleanup = onCleanup(@() local_delete_file(artifact)); %#ok<NASGU>
T = local_summary_table();
T.gamma(1) = 5.5;
T.pplus(1) = 4;
T.pminus(1) = 1.5;
local_save_valid_artifact(artifact, 1, 5.5, 'Solved', 500, 50);

T.status{1} = 'Solved';
verifyTrue(testCase, exact_batch_is_completed(T, 1, artifact));

T.status{1} = 'Inaccurate/Solved';
local_save_valid_artifact(artifact, 1, 5.5, 'Inaccurate/Solved', 500, 50);
verifyTrue(testCase, exact_batch_is_completed(T, 1, artifact));

T.status{1} = 'Failed';
verifyFalse(testCase, exact_batch_is_completed(T, 1, artifact));
end

function testCompletedRejectsUnrelatedOrMismatchedArtifact(testCase)
artifact = [tempname '.mat'];
cleanup = onCleanup(@() local_delete_file(artifact)); %#ok<NASGU>
T = local_summary_table();
T.gamma(1) = 5.5;
T.pplus(1) = 4;
T.pminus(1) = 1.5;
T.status{1} = 'Solved';

savedValue = 1;
save(artifact, 'savedValue');
verifyFalse(testCase, exact_batch_is_completed(T, 1, artifact));

local_save_valid_artifact(artifact, 2, 5.5, 'Solved', 500, 50);
verifyFalse(testCase, exact_batch_is_completed(T, 1, artifact));

local_save_valid_artifact(artifact, 1, 5.6, 'Solved', 500, 50);
verifyFalse(testCase, exact_batch_is_completed(T, 1, artifact));

local_save_valid_artifact(artifact, 1, 5.5, 'Solved', 499, 50);
verifyFalse(testCase, exact_batch_is_completed(T, 1, artifact));

local_save_valid_artifact(artifact, 1, 5.5, 'Solved', 500, 49);
verifyFalse(testCase, exact_batch_is_completed(T, 1, artifact));

local_save_valid_artifact(artifact, 1, 5.5, 'Solved', 500, 50, 4e-6);
verifyFalse(testCase, exact_batch_is_completed(T, 1, artifact));
end

function testInvalidSavedResultIsDetected(testCase)
T = local_summary_table();
T.gamma(1) = 5.5;
T.status{1} = 'Failed';
verifyTrue(testCase, exact_batch_has_invalid_saved_result(T, 1));

T.status{1} = 'ERROR';
verifyFalse(testCase, exact_batch_has_invalid_saved_result(T, 1));

T = local_summary_table();
verifyFalse(testCase, exact_batch_has_invalid_saved_result(T, 1));
end

function testSuccessRejectsInvalidSolverStatus(testCase)
T = local_summary_table();
info = local_info('Failed');
verifyError(testCase, @() exact_batch_record_success(T, 1, 5.5, info, 1), ...
    'exact_batch_record_success:invalidStatus');
end

function testErrorRecordClearsStaleSolverData(testCase)
T = local_summary_table();
T.gamma(1) = 5.5;
T.pplus(1) = 4;
T.pminus(1) = 1.5;
T.progRows(1) = 10;
T.tpRows(1) = 11;
T.hermDim(1) = 12;
T.minEig(1) = -1e-8;
T.tpResidual(1) = 1e-9;
T.freshProgResidual(1) = 1e-9;
T.status{1} = 'Failed';
T.basisDim(1) = 42;

T = exact_batch_record_error(T, 1, 3.25, 'solver failed');

verifyTrue(testCase, all(isnan(T{1, {'gamma', 'pplus', 'pminus', ...
    'progRows', 'tpRows', 'hermDim', 'minEig', 'tpResidual', ...
    'freshProgResidual'}})));
verifyEqual(testCase, T.runtime_s(1), 3.25);
verifyEqual(testCase, T.status{1}, 'ERROR');
verifyEqual(testCase, T.errorMsg{1}, 'solver failed');
verifyEqual(testCase, T.basisDim(1), 42);
end

function T = local_summary_table()
T = table(1, nan, nan, nan, {''}, nan, nan, nan, nan, nan, nan, nan, ...
    nan, {''}, 'VariableNames', {'ks', 'gamma', 'pplus', 'pminus', ...
    'status', 'progRows', 'tpRows', 'hermDim', 'runtime_s', 'minEig', ...
    'tpResidual', 'freshProgResidual', 'basisDim', 'errorMsg'});
end

function info = local_info(status)
info = struct('pplus', 4, 'pminus', 1.5, 'status', status, ...
    'progRows', 10, 'tpRows', 11, 'hermDim', 12, 'minEig', -1e-8, ...
    'tpResidual', 1e-9, 'freshProgResidual', 1e-9);
end

function local_save_valid_artifact(filename, k, cost, status, sampleCount, certFresh, freshResidual)
if nargin < 7
    freshResidual = 1e-8;
end
p1 = 4;
p2 = cost - p1;
info = struct('d', 2, 'k', k, 'cost', cost, 'pplus', p1, ...
    'pminus', p2, 'status', status, 'sampleCount', sampleCount, ...
    'certFresh', certFresh, 'minEig', -1e-8, 'maxNonHerm', 1e-8, ...
    'tpResidual', 1e-8, 'freshProgResidual', freshResidual);
b1 = 1; b2 = 1; coeffPlus = 1; coeffMinus = 1;
yPlus = 1; yMinus = 1;
blocksPlus = {1}; blocksMinus = {1};
blocksPlusRaw = {1}; blocksMinusRaw = {1};
blockMeta = struct('index', 1);
save(filename, 'cost', 'info', 'b1', 'b2', 'coeffPlus', 'coeffMinus', ...
    'yPlus', 'yMinus', 'p1', 'p2', 'blocksPlus', 'blocksMinus', ...
    'blocksPlusRaw', 'blocksMinusRaw', 'blockMeta');
end

function local_delete_file(filename)
if exist(filename, 'file') == 2
    delete(filename);
end
end

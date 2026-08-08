function report = verify_strict_submultiplicativity(opts)
%VERIFY_STRICT_SUBMULTIPLICATIVITY Reproduce the finite qubit example.
%
% Set opts.solve=false to check only the historical correction matrix.
% Set opts.solve=true to recompute the one-copy and correlated costs with CVX.

if nargin < 1 || isempty(opts)
    opts = struct();
end
if ~isstruct(opts) || ~isscalar(opts)
    error('verify_strict_submultiplicativity:badOptions', ...
        'opts must be a scalar struct.');
end

caseRoot = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(caseRoot));
opts = local_defaults(opts, repoRoot);
local_add_root(opts.qetlabRoot);
if exist('PartialTrace', 'file') ~= 2 || exist('PermuteSystems', 'file') ~= 2
    error('verify_strict_submultiplicativity:missingQETLAB', ...
        'QETLAB is required. Set UP_QETLAB_ROOT or opts.qetlabRoot.');
end

[JCorrection, entryCount] = local_load_correction(opts.certificatePath);
[channelChoi, programs, channelTpResiduals] = local_channels();

dimsJoint = 2 * ones(1, 8);
hermiticityResidual = norm(JCorrection - JCorrection', 'fro');
outputTraceResidual = norm(PartialTrace( ...
    JCorrection, [7, 8], dimsJoint, 0), 'fro');

annihilationResiduals = zeros(2);
for i = 1:2
    for j = 1:2
        program = PermuteSystems(kron(programs{i}, programs{j}), ...
            [1, 3, 2, 4], 2 * ones(1, 4));
        weight = kron(eye(4), kron(program.', eye(4)));
        induced = PartialTrace(JCorrection * weight, ...
            [3, 4, 5, 6], dimsJoint, 0);
        annihilationResiduals(i, j) = norm(induced, 'fro');
    end
end

maxStructuralResidual = max([channelTpResiduals(:); ...
    hermiticityResidual; outputTraceResidual; annihilationResiduals(:)]);
if maxStructuralResidual > opts.residualTolerance
    error('verify_strict_submultiplicativity:structuralResidual', ...
        'The historical correction failed a structural check (%.3e).', ...
        maxStructuralResidual);
end

report = struct();
report.mode = 'structural';
report.registerOrder = ...
    {'S1', 'S2', 'A1', 'A2', 'B1', 'B2', 'S1_out', 'S2_out'};
report.certificateNnz = entryCount;
report.channelTpResiduals = channelTpResiduals;
report.hermiticityResidual = hermiticityResidual;
report.outputTraceResidual = outputTraceResidual;
report.annihilationResiduals = annihilationResiduals;
report.oneCopyCost = NaN;
report.productCost = NaN;
report.correlatedCost = NaN;
report.strictGap = NaN;
report.oneCopyStatus = 'not_run';
report.correlatedStatus = 'not_run';
report.isStrictNumerical = false;

if opts.verbose
    fprintf('Historical correction: %d nonzero entries\n', entryCount);
    fprintf('Structural residuals: Herm %.3e, output trace %.3e, annihilation %.3e\n', ...
        hermiticityResidual, outputTraceResidual, ...
        max(annihilationResiduals, [], 'all'));
end

if ~opts.solve
    return;
end

local_setup_cvx(opts.cvxRoot);

% Optimal one-copy processor in order S,A,B,S_out.
dimsOne = 2 * ones(1, 4);
weightsOne = cell(1, 2);
for i = 1:2
    weightsOne{i} = kron(eye(2), kron(programs{i}.', eye(2)));
end

cvx_begin sdp quiet
    cvx_solver(opts.solver)
    cvx_precision high
    variable JPlus(16, 16) hermitian
    variable JMinus(16, 16) hermitian
    variable pPlus
    variable pMinus
    minimize(pPlus + pMinus)
    subject to
        JPlus >= 0;
        JMinus >= 0;
        PartialTrace(JPlus, 4, dimsOne, 0) == pPlus * eye(8);
        PartialTrace(JMinus, 4, dimsOne, 0) == pMinus * eye(8);
        for i = 1:2
            PartialTrace((JPlus - JMinus) * weightsOne{i}, ...
                [2, 3], dimsOne, 0) == channelChoi{i};
        end
cvx_end

oneCopyStatus = cvx_status;
if ~contains(lower(oneCopyStatus), 'solved')
    error('verify_strict_submultiplicativity:oneCopySolve', ...
        'The one-copy SDP did not solve: %s.', oneCopyStatus);
end

JOne = JPlus - JMinus;
oneCopyCost = pPlus + pMinus;
oneCopyTpResidual = norm(PartialTrace(JOne, 4, dimsOne, 0) - eye(8), 'fro');

% Tensor the optimal processor and group equal register types to match J_C.
JProduct = PermuteSystems(kron(JOne, JOne), ...
    [1, 5, 2, 6, 3, 7, 4, 8], dimsJoint);
JCorrelated = JProduct + JCorrection;
correlatedTpResidual = norm(PartialTrace( ...
    JCorrelated, [7, 8], dimsJoint, 0) - eye(64), 'fro');

correlatedProgrammingResiduals = zeros(2);
for i = 1:2
    for j = 1:2
        program = PermuteSystems(kron(programs{i}, programs{j}), ...
            [1, 3, 2, 4], 2 * ones(1, 4));
        target = PermuteSystems(kron(channelChoi{i}, channelChoi{j}), ...
            [1, 3, 2, 4], 2 * ones(1, 4));
        weight = kron(eye(4), kron(program.', eye(4)));
        induced = PartialTrace(JCorrelated * weight, ...
            [3, 4, 5, 6], dimsJoint, 0);
        correlatedProgrammingResiduals(i, j) = norm(induced - target, 'fro');
    end
end

% QETLAB uses the low-rank Kraus form of the fixed map, which is much smaller
% than introducing a dense 256-by-256 decomposition inside this script.
correlatedCost = DiamondNorm(JCorrelated, [64, 4]);
correlatedStatus = 'Solved (QETLAB DiamondNorm)';
productCost = oneCopyCost^2;
strictGap = productCost - correlatedCost;
maxNumericalResidual = max([oneCopyTpResidual; correlatedTpResidual; ...
    correlatedProgrammingResiduals(:)]);
if maxNumericalResidual > opts.numericalTolerance
    error('verify_strict_submultiplicativity:numericalResidual', ...
        'The numerical processor residual is too large (%.3e).', ...
        maxNumericalResidual);
end
if strictGap <= opts.gapTolerance
    error('verify_strict_submultiplicativity:noStrictGap', ...
        'No strict numerical gap was reproduced (gap %.3e).', strictGap);
end

report.mode = 'full';
report.oneCopyCost = oneCopyCost;
report.productCost = productCost;
report.correlatedCost = correlatedCost;
report.strictGap = strictGap;
report.gapTolerance = opts.gapTolerance;
report.oneCopyStatus = oneCopyStatus;
report.correlatedStatus = correlatedStatus;
report.oneCopyTpResidual = oneCopyTpResidual;
report.correlatedTpResidual = correlatedTpResidual;
report.correlatedProgrammingResiduals = correlatedProgrammingResiduals;
report.isStrictNumerical = true;

if opts.verbose
    fprintf('one-copy cost             : %.12f\n', oneCopyCost);
    fprintf('product cost              : %.12f\n', productCost);
    fprintf('correlated processor cost : %.12f\n', correlatedCost);
    fprintf('strict numerical gap      : %.6e\n', strictGap);
end

if opts.saveResult
    resultDir = fileparts(opts.resultPath);
    if ~exist(resultDir, 'dir')
        mkdir(resultDir);
    end
    save(opts.resultPath, 'report');
end
end

function opts = local_defaults(opts, repoRoot)
defaults = struct();
defaults.solve = false;
defaults.verbose = true;
defaults.solver = local_environment('UP_SDP_SOLVER', 'sdpt3');
defaults.cvxRoot = getenv('UP_CVX_ROOT');
defaults.qetlabRoot = getenv('UP_QETLAB_ROOT');
defaults.certificatePath = fullfile(repoRoot, 'results', 'certified', ...
    'strict_submult_C_sparse.tsv');
defaults.residualTolerance = 1e-10;
defaults.numericalTolerance = 1e-6;
defaults.gapTolerance = 1e-6;
defaults.saveResult = false;
defaults.resultPath = fullfile(repoRoot, 'results', 'generated', ...
    'strict_submultiplicativity.mat');

fields = fieldnames(defaults);
for i = 1:numel(fields)
    field = fields{i};
    if ~isfield(opts, field) || isempty(opts.(field))
        opts.(field) = defaults.(field);
    end
end
end

function [JCorrection, entryCount] = local_load_correction(path)
if exist(path, 'file') ~= 2
    error('verify_strict_submultiplicativity:missingCertificate', ...
        'Certificate file not found: %s', path);
end

tableData = readtable(path, 'FileType', 'text', 'Delimiter', '\t');
required = {'row', 'col', 'numerator', 'denominator'};
if ~isequal(tableData.Properties.VariableNames, required)
    error('verify_strict_submultiplicativity:certificateSchema', ...
        'Unexpected certificate columns.');
end
entryCount = height(tableData);
if entryCount ~= 360
    error('verify_strict_submultiplicativity:certificateCount', ...
        'Expected 360 nonzero entries, found %d.', entryCount);
end

rows = double(tableData.row);
cols = double(tableData.col);
values = double(tableData.numerator) ./ double(tableData.denominator);
JCorrection = full(sparse(rows, cols, values, 256, 256));
end

function [channelChoi, programs, tpResiduals] = local_channels()
parameters = [4/9, 4/9, 1/9; 4/9, 1/9, 4/9];
channelChoi = cell(1, 2);
programs = cell(1, 2);
tpResiduals = zeros(1, 2);

for i = 1:2
    g = parameters(i, 1);
    alpha = parameters(i, 2);
    lambda = parameters(i, 3);
    kraus = {
        [0, sqrt(g); 0, 0], ...
        [1, 0; 0, sqrt(alpha)], ...
        [0, 0; 0, sqrt(lambda)]};

    J = zeros(4);
    normalization = zeros(2);
    for r = 1:numel(kraus)
        vector = kraus{r}(:);
        J = J + vector * vector';
        normalization = normalization + kraus{r}' * kraus{r};
    end
    channelChoi{i} = J;
    programs{i} = J / 2;
    tpResiduals(i) = norm(normalization - eye(2), 'fro');
end
end

function local_setup_cvx(cvxRoot)
if exist('cvx_begin', 'file') ~= 2
    local_add_root(cvxRoot);
    if exist('cvx_setup', 'file') == 2
        cvx_setup;
    end
end
if exist('cvx_begin', 'file') ~= 2
    error('verify_strict_submultiplicativity:missingCVX', ...
        'CVX is required in full mode. Set UP_CVX_ROOT or opts.cvxRoot.');
end
end

function local_add_root(root)
if ~isempty(root) && exist(root, 'dir') == 7
    addpath(genpath(root));
end
end

function value = local_environment(name, fallback)
value = getenv(name);
if isempty(value)
    value = fallback;
end
end

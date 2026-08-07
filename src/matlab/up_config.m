function cfg = up_config(overrides)
%UP_CONFIG Build portable configuration for local experiment code.

if nargin < 1 || isempty(overrides)
    overrides = struct();
end
if ~isstruct(overrides) || ~isscalar(overrides)
    error('up_config:badOverrides', 'overrides must be a scalar struct.');
end

matlabRoot = fileparts(mfilename('fullpath'));
srcRoot = fileparts(matlabRoot);
repoRoot = fileparts(srcRoot);

cfg = struct();
cfg.repoRoot = repoRoot;
cfg.cvxRoot = local_value(overrides, 'cvxRoot', 'UP_CVX_ROOT', '');
cfg.qetlabRoot = local_value(overrides, 'qetlabRoot', 'UP_QETLAB_ROOT', '');
cfg.yalmipRoot = local_value(overrides, 'yalmipRoot', 'UP_YALMIP_ROOT', '');
cfg.matlabBin = local_value(overrides, 'matlabBin', 'UP_MATLAB_BIN', 'matlab');
cfg.solver = local_value(overrides, 'solver', 'UP_SDP_SOLVER', 'sdpt3');
cfg.resultsRoot = local_value(overrides, 'resultsRoot', 'UP_RESULTS_ROOT', ...
    fullfile(repoRoot, 'results', 'generated'));
end

function value = local_value(overrides, field, environmentName, defaultValue)
if isfield(overrides, field)
    value = overrides.(field);
    return;
end

value = getenv(environmentName);
if isempty(value)
    value = defaultValue;
end
end

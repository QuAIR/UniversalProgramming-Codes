function up_setup(cfg, requireYalmip)
%UP_SETUP Configure the supported MATLAB solver dependencies.

if nargin < 1 || isempty(cfg)
    cfg = up_config();
end
if nargin < 2 || isempty(requireYalmip)
    requireYalmip = false;
end

addpath(fullfile(cfg.repoRoot, 'src', 'matlab', 'common'));
addpath(fullfile(cfg.repoRoot, 'src', 'matlab', 'kcopy_d2'));

if exist('cvx_begin', 'file') ~= 2
    local_add_root(cfg.cvxRoot);
    if exist('cvx_setup', 'file') == 2
        cvx_setup;
    end
end
if exist('cvx_begin', 'file') ~= 2
    error('up_setup:missingCVX', ...
        'CVX is required. Set UP_CVX_ROOT or cfg.cvxRoot.');
end

local_add_root(cfg.qetlabRoot);
if exist('RandomSuperoperator', 'file') ~= 2
    error('up_setup:missingQETLAB', ...
        'QETLAB is required. Set UP_QETLAB_ROOT or cfg.qetlabRoot.');
end

if requireYalmip
    local_add_root(cfg.yalmipRoot);
    if exist('sdpvar', 'file') ~= 2
        error('up_setup:missingYALMIP', ...
            'YALMIP is required. Set UP_YALMIP_ROOT or cfg.yalmipRoot.');
    end
end
end

function local_add_root(root)
if ~isempty(root) && exist(root, 'dir') == 7
    addpath(genpath(root));
end
end

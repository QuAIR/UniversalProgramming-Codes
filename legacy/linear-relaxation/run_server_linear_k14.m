%% run_server_linear_k14.m -- server simplified SDP run, k=1..4
%
% This runs only gamma_k_d2(k, 'linear'), i.e. the m=0,1 simplified
% lower-bound SDP.  It deliberately does not call the exact 'full' mode.

clear; clc;
warning('legacy:linearRelaxation', ...
    'Lower-bound relaxation only; not equivalent to exact gamma_k.');
scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(scriptDir));
prototypeDir = fullfile(repoRoot, 'legacy', 'qubit-reduced-prototype');
addpath(fullfile(repoRoot, 'src', 'matlab'));
addpath(prototypeDir);
cfg = up_config();
up_setup(cfg, false);
outputDir = fullfile(cfg.resultsRoot, 'legacy', 'linear-relaxation');
if exist(outputDir, 'dir') ~= 7
    mkdir(outputDir);
end

cvx_quiet(false);
cvx_precision high;

cvx_solver sdpt3;

ks = 1:4;
gam_linear = nan(size(ks));
pplus_linear = nan(size(ks));
pminus_linear = nan(size(ks));
status_linear = strings(size(ks));
runtime_linear = nan(size(ks));
info_linear = cell(size(ks));

for idx = 1:numel(ks)
    k = ks(idx);
    fprintf('\n=== k=%d simplified m=0,1 SDP only ===\n', k);

    t = tic;
    try
        [gam_linear(idx), pplus_linear(idx), pminus_linear(idx), info] = gamma_k_d2(k, 'linear', true);
        runtime_linear(idx) = toc(t);
        status_linear(idx) = string(info.status);
        info_linear{idx} = info;
    catch ME
        runtime_linear(idx) = toc(t);
        status_linear(idx) = "ERROR: " + string(ME.identifier);
        fprintf(2, 'LINEAR_FAILED k=%d: %s\n', k, getReport(ME, 'extended', 'hyperlinks', 'off'));
    end

    fprintf('SUMMARY_SIMPLIFIED k=%d linear=%.10f pplus=%.10f pminus=%.10f runtime_s=%.2f status=%s\n', ...
        k, gam_linear(idx), pplus_linear(idx), pminus_linear(idx), runtime_linear(idx), char(status_linear(idx)));

    save(fullfile(outputDir, 'kcopy_d2_server_linear_k14_partial.mat'), ...
        'ks', 'gam_linear', 'pplus_linear', 'pminus_linear', ...
        'status_linear', 'runtime_linear', 'info_linear');
end

T = table(ks(:), gam_linear(:), pplus_linear(:), pminus_linear(:), ...
    status_linear(:), runtime_linear(:), ...
    'VariableNames', {'k', 'gamma_linear', 'pplus_linear', 'pminus_linear', ...
    'status_linear', 'runtime_linear_s'});

disp(T);
writetable(T, fullfile(outputDir, 'kcopy_d2_server_linear_k14.csv'));
save(fullfile(outputDir, 'kcopy_d2_server_linear_k14.mat'), 'T', ...
    'ks', 'gam_linear', 'pplus_linear', 'pminus_linear', ...
    'status_linear', 'runtime_linear', 'info_linear');

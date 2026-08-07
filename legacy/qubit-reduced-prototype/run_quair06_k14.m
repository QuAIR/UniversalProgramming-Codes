%% run_quair06_k14.m -- quair06 batch run for gamma_k(CPTP, d=2), k=1..4
%
% This follows ../kcopy_d2_reduction/kcopy_d2_reduction.tex after the proof split:
%   full   = exact all-row SDP;
%   linear = m=0,1 lower-bound relaxation.

clear; clc;
warning('legacy:qubitReducedPrototype', ...
    'Archived provenance runner: not a supported experiment entry point.');
scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(scriptDir));
addpath(fullfile(repoRoot, 'src', 'matlab'));
addpath(scriptDir);
cfg = up_config();
up_setup(cfg, false);
outputDir = fullfile(cfg.resultsRoot, 'legacy', 'qubit-reduced-prototype');
if exist(outputDir, 'dir') ~= 7
    mkdir(outputDir);
end

cvx_quiet(false);
cvx_precision high;

cvx_solver sdpt3;

ks = 1:4;
gam_full = nan(size(ks));
gam_linear = nan(size(ks));
pplus_full = nan(size(ks));
pminus_full = nan(size(ks));
pplus_linear = nan(size(ks));
pminus_linear = nan(size(ks));
status_full = strings(size(ks));
status_linear = strings(size(ks));
runtime_full = nan(size(ks));
runtime_linear = nan(size(ks));
gap_full_minus_linear = nan(size(ks));
linear_lower_bound_ok = false(size(ks));
binding_flag = strings(size(ks));

for idx = 1:numel(ks)
    k = ks(idx);

    fprintf('\n=== k=%d exact full-row SDP ===\n', k);
    t = tic;
    try
        [gam_full(idx), pplus_full(idx), pminus_full(idx), info] = gamma_k_d2(k, 'full', true);
        runtime_full(idx) = toc(t);
        status_full(idx) = string(info.status);
    catch ME
        runtime_full(idx) = toc(t);
        status_full(idx) = "ERROR: " + string(ME.identifier);
        fprintf(2, 'FULL_FAILED k=%d: %s\n', k, getReport(ME, 'extended', 'hyperlinks', 'off'));
    end

    save(fullfile(outputDir, 'kcopy_d2_quair06_updated_k14_partial.mat'), ...
        'ks', 'gam_full', 'gam_linear', 'gap_full_minus_linear', ...
        'linear_lower_bound_ok', 'binding_flag', ...
        'pplus_full', 'pminus_full', 'pplus_linear', 'pminus_linear', ...
        'status_full', 'status_linear', 'runtime_full', 'runtime_linear');

    fprintf('\n=== k=%d m=0,1 relaxation ===\n', k);
    t = tic;
    try
        [gam_linear(idx), pplus_linear(idx), pminus_linear(idx), info] = gamma_k_d2(k, 'linear', true);
        runtime_linear(idx) = toc(t);
        status_linear(idx) = string(info.status);
    catch ME
        runtime_linear(idx) = toc(t);
        status_linear(idx) = "ERROR: " + string(ME.identifier);
        fprintf(2, 'LINEAR_FAILED k=%d: %s\n', k, getReport(ME, 'extended', 'hyperlinks', 'off'));
    end

    gap_full_minus_linear(idx) = gam_full(idx) - gam_linear(idx);
    linear_lower_bound_ok(idx) = isnan(gap_full_minus_linear(idx)) || gap_full_minus_linear(idx) >= -1e-5;
    if isnan(gap_full_minus_linear(idx))
        binding_flag(idx) = "unknown";
    elseif abs(gap_full_minus_linear(idx)) < 1e-5
        binding_flag(idx) = "no_detected_gap";
    else
        binding_flag(idx) = "omitted_rows_bind";
    end

    fprintf('SUMMARY k=%d full=%.10f linear=%.10f gap=%.3e flag=%s\n', ...
        k, gam_full(idx), gam_linear(idx), gap_full_minus_linear(idx), char(binding_flag(idx)));

    save(fullfile(outputDir, 'kcopy_d2_quair06_updated_k14_partial.mat'), ...
        'ks', 'gam_full', 'gam_linear', 'gap_full_minus_linear', ...
        'linear_lower_bound_ok', 'binding_flag', ...
        'pplus_full', 'pminus_full', 'pplus_linear', 'pminus_linear', ...
        'status_full', 'status_linear', 'runtime_full', 'runtime_linear');
end

T = table(ks(:), gam_full(:), gam_linear(:), gap_full_minus_linear(:), ...
    linear_lower_bound_ok(:), binding_flag(:), ...
    pplus_full(:), pminus_full(:), pplus_linear(:), pminus_linear(:), ...
    status_full(:), status_linear(:), runtime_full(:), runtime_linear(:), ...
    'VariableNames', {'k', 'gamma_full', 'gamma_linear', 'gap_full_minus_linear', ...
    'linear_lower_bound_ok', 'binding_flag', ...
    'pplus_full', 'pminus_full', 'pplus_linear', 'pminus_linear', ...
    'status_full', 'status_linear', 'runtime_full_s', 'runtime_linear_s'});

disp(T);
writetable(T, fullfile(outputDir, 'kcopy_d2_quair06_updated_k14.csv'));
save(fullfile(outputDir, 'kcopy_d2_quair06_updated_k14.mat'), 'T', ...
    'ks', 'gam_full', 'gam_linear', 'gap_full_minus_linear', ...
    'linear_lower_bound_ok', 'binding_flag', ...
    'pplus_full', 'pminus_full', 'pplus_linear', 'pminus_linear', ...
    'status_full', 'status_linear', 'runtime_full', 'runtime_linear');

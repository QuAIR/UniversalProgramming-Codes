clear; clc;

scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(fileparts(scriptDir)));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();
up_setup(cfg, false);

outputDir = fullfile(cfg.resultsRoot, 'server', 'kcopy_d2', 'exact_k14');
perKDir = fullfile(outputDir, 'per_k');
if exist(outputDir, 'dir') ~= 7
    mkdir(outputDir);
end
if exist(perKDir, 'dir') ~= 7
    mkdir(perKDir);
end

diary(fullfile(outputDir, 'run_exact_k14.log'));
cleanupObj = onCleanup(@() diary('off')); %#ok<NASGU>

fprintf('=== exact d=2 k-copy run: k=1..4 ===\n');
fprintf('Started at %s\n', datestr(now));

opts = struct();
opts.setupCvx = false;
opts.solver = cfg.solver;
opts.s = 500;
opts.certFresh = 50;
opts.seed = 0;
opts.freshSeed = 777;
opts.verbose = true;
opts.saveResult = true;
opts.resultsDir = perKDir;
opts.checkExpectedRows = true;

ks = (1:4).';
partialMat = fullfile(outputDir, 'exact_k14_partial.mat');
partialCsv = fullfile(outputDir, 'exact_k14_partial.csv');
Tpartial = local_load_or_create_summary(partialMat, ks);

for ii = 1:numel(ks)
    k = ks(ii);
    perKFile = fullfile(perKDir, sprintf('exact_d2_k%d.mat', k));
    t0 = tic;
    try
        if exact_batch_is_completed(Tpartial, ii, perKFile)
            if k == 1
                local_assert_k1_cost(Tpartial.gamma(ii));
            end
            fprintf('Skipping completed exact k=%d.\n', k);
            continue;
        end

        if exact_batch_has_invalid_saved_result(Tpartial, ii)
            error('run_exact_k14:invalidResume', ...
                'Resumed exact k=%d has unvalidated solver data.', k);
        end

        fprintf('\n--- exact k=%d ---\n', k);
        [cost, info] = gamma_k_d2_exact(k, opts);
        Tpartial = exact_batch_record_success(Tpartial, ii, cost, info, toc(t0));
        if k == 1
            local_assert_k1_cost(cost);
        end
        local_save_summary(partialMat, partialCsv, Tpartial, opts);
        fprintf('RESULT k=%d gamma=%.12f status=%s runtime=%.2fs\n', ...
            k, Tpartial.gamma(ii), Tpartial.status{ii}, Tpartial.runtime_s(ii));
    catch ME
        Tpartial = exact_batch_record_error(Tpartial, ii, toc(t0), ME.message);
        local_save_summary(partialMat, partialCsv, Tpartial, opts);
        fprintf(2, 'ERROR k=%d after %.2fs: %s\n', ...
            k, Tpartial.runtime_s(ii), ME.message);
    end
end

T = Tpartial;
save(fullfile(outputDir, 'exact_k14.mat'), 'T', 'opts');
writetable(T, fullfile(outputDir, 'exact_k14.csv'));

fprintf('\n=== finished at %s ===\n', datestr(now));
disp(T);

failedKs = T.ks(strcmp(T.status, 'ERROR'));
if ~isempty(failedKs)
    error('run_exact_k14:batchFailed', ...
        'Exact batch completed with errors for k=%s.', mat2str(failedKs.'));
end

function T = local_load_or_create_summary(partialMat, ks)
if exist(partialMat, 'file') == 2
    saved = load(partialMat, 'Tpartial');
    assert(isfield(saved, 'Tpartial') && istable(saved.Tpartial), ...
        'run_exact_k14:invalidPartial', ...
        'Partial summary is missing a compatible Tpartial table.');
    T = saved.Tpartial;
    assert(isequal(T.ks, ks), 'run_exact_k14:invalidPartial', ...
        'Partial summary does not match k=1,...,4.');
    return;
end

n = numel(ks);
T = table(ks, nan(n, 1), nan(n, 1), nan(n, 1), repmat({''}, n, 1), ...
    nan(n, 1), nan(n, 1), nan(n, 1), nan(n, 1), nan(n, 1), nan(n, 1), ...
    nan(n, 1), repmat({''}, n, 1), 'VariableNames', ...
    {'ks', 'gamma', 'pplus', 'pminus', 'status', 'progRows', 'tpRows', ...
    'hermDim', 'runtime_s', 'minEig', 'tpResidual', 'freshProgResidual', ...
    'errorMsg'});
end

function local_save_summary(partialMat, partialCsv, Tpartial, opts)
save(partialMat, 'Tpartial', 'opts');
writetable(Tpartial, partialCsv);
end

function local_assert_k1_cost(cost)
assert(abs(cost - 5.5) < 1e-5, 'run_exact_k14:k1Cost', ...
    'Expected gamma_1(CPTP,2)=5.5, got %.12f.', cost);
end

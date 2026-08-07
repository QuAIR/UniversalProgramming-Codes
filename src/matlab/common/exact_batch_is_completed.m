function completed = exact_batch_is_completed(T, index, perKFile)
%EXACT_BATCH_IS_COMPLETED Validate the summary row and its per-k artifact.

completed = false;
if ~(isfinite(T.gamma(index)) && ...
        exact_batch_is_success_status(T.status{index}) && ...
        exist(perKFile, 'file') == 2)
    return;
end

requiredVariables = {'cost', 'info', 'b1', 'b2', 'coeffPlus', ...
    'coeffMinus', 'yPlus', 'yMinus', 'p1', 'p2', 'blocksPlus', ...
    'blocksMinus', 'blocksPlusRaw', 'blocksMinusRaw', 'blockMeta'};
try
    variables = who('-file', perKFile);
    if ~all(ismember(requiredVariables, variables))
        return;
    end
    saved = load(perKFile, 'cost', 'info', 'p1', 'p2');
catch
    return;
end

requiredInfo = {'d', 'k', 'cost', 'pplus', 'pminus', 'status', ...
    'sampleCount', 'certFresh', 'minEig', 'maxNonHerm', ...
    'tpResidual', 'freshProgResidual'};
if ~isstruct(saved.info) || ~all(isfield(saved.info, requiredInfo))
    return;
end

info = saved.info;
expectedK = T.ks(index);
summaryStatus = local_status_text(T.status{index});
artifactStatus = local_status_text(info.status);
residualTolerance = 3e-6;
completed = local_equal_scalar(info.d, 2) && ...
    local_equal_scalar(info.k, expectedK) && ...
    local_equal_scalar(info.sampleCount, 500) && ...
    local_equal_scalar(info.certFresh, 50) && ...
    exact_batch_is_success_status(artifactStatus) && ...
    strcmp(artifactStatus, summaryStatus) && ...
    local_close(saved.cost, T.gamma(index)) && ...
    local_close(info.cost, saved.cost) && ...
    local_close(saved.p1, T.pplus(index)) && ...
    local_close(saved.p2, T.pminus(index)) && ...
    local_close(info.pplus, saved.p1) && ...
    local_close(info.pminus, saved.p2) && ...
    local_close(saved.p1 + saved.p2, saved.cost) && ...
    local_finite_scalar(info.minEig) && info.minEig >= -residualTolerance && ...
    local_residual_ok(info.maxNonHerm, residualTolerance) && ...
    local_residual_ok(info.tpResidual, residualTolerance) && ...
    local_residual_ok(info.freshProgResidual, residualTolerance);
end

function valid = local_equal_scalar(actual, expected)
valid = local_finite_scalar(actual) && local_finite_scalar(expected) && ...
    actual == expected;
end

function valid = local_close(actual, expected)
valid = local_finite_scalar(actual) && local_finite_scalar(expected) && ...
    abs(double(actual) - double(expected)) <= 1e-8 * max(1, abs(double(expected)));
end

function valid = local_finite_scalar(value)
valid = isnumeric(value) && isscalar(value) && isfinite(value) && isreal(value);
end

function valid = local_residual_ok(value, tolerance)
valid = local_finite_scalar(value) && abs(double(value)) <= tolerance;
end

function status = local_status_text(status)
if isstring(status)
    status = char(status);
end
if ~ischar(status)
    status = '';
end
end

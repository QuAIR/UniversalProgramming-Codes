function T = exact_batch_record_success(T, index, cost, info, runtime)
%EXACT_BATCH_RECORD_SUCCESS Record only finite results with CVX success statuses.

if ~(isscalar(cost) && isfinite(cost))
    error('exact_batch_record_success:invalidCost', ...
        'Exact solver returned a non-finite cost.');
end
if ~exact_batch_is_success_status(info.status)
    error('exact_batch_record_success:invalidStatus', ...
        'Exact solver returned non-success status: %s.', info.status);
end

T.gamma(index) = cost;
T.pplus(index) = info.pplus;
T.pminus(index) = info.pminus;
T.status{index} = info.status;
T.progRows(index) = info.progRows;
T.tpRows(index) = info.tpRows;
T.hermDim(index) = info.hermDim;
T.runtime_s(index) = runtime;
T.minEig(index) = info.minEig;
T.tpResidual(index) = info.tpResidual;
T.freshProgResidual(index) = info.freshProgResidual;
T.errorMsg{index} = '';
end

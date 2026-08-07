function T = exact_batch_record_error(T, index, runtime, message)
%EXACT_BATCH_RECORD_ERROR Clear solver output before persisting a failed row.

solverFields = {'gamma', 'pplus', 'pminus', 'progRows', 'tpRows', 'hermDim', ...
    'minEig', 'tpResidual', 'freshProgResidual'};
for fieldIndex = 1:numel(solverFields)
    field = solverFields{fieldIndex};
    if ismember(field, T.Properties.VariableNames)
        T.(field)(index) = nan;
    end
end

T.runtime_s(index) = runtime;
T.status{index} = 'ERROR';
T.errorMsg{index} = message;
end

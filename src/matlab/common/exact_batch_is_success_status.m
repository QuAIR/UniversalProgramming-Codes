function isSuccess = exact_batch_is_success_status(status)
%EXACT_BATCH_IS_SUCCESS_STATUS Return whether CVX reported a usable solution.

if isstring(status)
    status = char(status);
end

isSuccess = ischar(status) && any(strcmp(status, ...
    {'Solved', 'Inaccurate/Solved'}));
end

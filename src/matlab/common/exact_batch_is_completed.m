function completed = exact_batch_is_completed(T, index, perKFile)
%EXACT_BATCH_IS_COMPLETED Require a finite result, CVX success, and artifact.

completed = isfinite(T.gamma(index)) && ...
    exact_batch_is_success_status(T.status{index}) && ...
    exist(perKFile, 'file') == 2;
end

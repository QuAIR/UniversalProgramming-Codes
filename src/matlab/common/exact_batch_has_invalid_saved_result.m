function invalid = exact_batch_has_invalid_saved_result(T, index)
%EXACT_BATCH_HAS_INVALID_SAVED_RESULT Detect stale non-error solver output.

status = T.status{index};
if isstring(status)
    status = char(status);
end

invalid = (isfinite(T.gamma(index)) || ~isempty(status)) && ...
    ~strcmp(status, 'ERROR');
end

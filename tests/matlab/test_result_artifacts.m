root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
manifest = jsondecode(fileread(fullfile(root, 'results', 'mat-artifacts.json')));
artifacts = manifest.artifacts;
assert(manifest.artifact_count == numel(artifacts));

for i = 1:numel(artifacts)
    if iscell(artifacts)
        artifact = artifacts{i};
    else
        artifact = artifacts(i);
    end
    path = fullfile(root, strrep(artifact.path, '/', filesep));
    vars = whos('-file', path);
    actualNames = sort(string({vars.name}));
    expectedNames = sort(string(artifact.variables));
    assert(isequal(actualNames(:), expectedNames(:)), ...
        'Schema mismatch for %s', artifact.path);

    data = load(path);
    assert(~contains_sensitive_path(data), ...
        'Personal path remains in %s', artifact.path);

    if strcmp(artifact.classification, 'certified')
        assert(isfield(artifact, 'checks') && ~isempty(artifact.checks), ...
            'Certified artifact lacks checks: %s', artifact.path);
    end

    if isfield(artifact, 'checks') && ~isempty(artifact.checks)
        for j = 1:numel(artifact.checks)
            if iscell(artifact.checks)
                check = artifact.checks{j};
            else
                check = artifact.checks(j);
            end
            actual = get_nested_field(data, check.matlab_path);
            if isnumeric(check.expected)
                tolerance = check.tolerance;
                assert(isnumeric(actual) && isscalar(actual));
                assert(abs(double(actual) - double(check.expected)) <= tolerance, ...
                    'Value mismatch for %s:%s', artifact.path, check.matlab_path);
            else
                assert(strcmp(string(actual), string(check.expected)), ...
                    'String mismatch for %s:%s', artifact.path, check.matlab_path);
            end
        end
    end

    if isfield(artifact, 'evidence') && ~isempty(fieldnames(artifact.evidence))
        validate_recorded_numeric_evidence(data, artifact.evidence, artifact.path);
    end
end

fprintf('Verified %d MAT artifacts from manifest.\n', numel(artifacts));

function value = get_nested_field(value, dottedPath)
parts = strsplit(dottedPath, '.');
for i = 1:numel(parts)
    assert(isstruct(value) && isfield(value, parts{i}), ...
        'Missing field %s in path %s', parts{i}, dottedPath);
    value = value.(parts{i});
end
end


function validate_recorded_numeric_evidence(data, evidence, artifactPath)
directFields = {'d', 'k', 'cost', 'p1', 'p2'};
for i = 1:numel(directFields)
    field = directFields{i};
    if ~isfield(evidence, field)
        continue;
    end
    if isfield(data, field)
        actual = data.(field);
    elseif isfield(data, 'info') && isfield(data.info, field)
        actual = data.info.(field);
    else
        continue;
    end
    assert_numeric_equal(actual, evidence.(field), artifactPath, field);
end

if isfield(evidence, 'sample_count')
    if isfield(data, 's')
        actual = data.s;
    elseif isfield(data, 'info') && isfield(data.info, 'sampleCount')
        actual = data.info.sampleCount;
    elseif isfield(data, 'opts') && isfield(data.opts, 's')
        actual = data.opts.s;
    else
        actual = [];
    end
    if ~isempty(actual)
        assert_numeric_equal(actual, evidence.sample_count, artifactPath, 'sample_count');
    end
end

if isfield(evidence, 'k5_cost')
    assert(isfield(data, 'Tpartial') && numel(data.Tpartial.gamma) >= 1);
    assert_numeric_equal(data.Tpartial.gamma(1), evidence.k5_cost, artifactPath, 'k5_cost');
end
if isfield(evidence, 'k6_cost')
    assert(isfield(data, 'Tpartial') && numel(data.Tpartial.gamma) >= 2);
    assert_numeric_equal(data.Tpartial.gamma(2), evidence.k6_cost, artifactPath, 'k6_cost');
end
if isfield(evidence, 'full_costs')
    assert_numeric_equal(data.gam_full, evidence.full_costs, artifactPath, 'full_costs');
end
if isfield(evidence, 'linear_costs')
    assert_numeric_equal(data.gam_linear, evidence.linear_costs, artifactPath, 'linear_costs');
end
end


function assert_numeric_equal(actual, expected, artifactPath, field)
actual = double(actual);
if (ischar(expected) || isstring(expected)) && strcmp(string(expected), "NaN")
    assert(all(isnan(actual), 'all'), ...
        'Value mismatch for %s:%s', artifactPath, field);
    return;
end
if iscell(expected)
    normalized = nan(size(expected));
    for i = 1:numel(expected)
        item = expected{i};
        if isnumeric(item)
            normalized(i) = double(item);
        else
            assert(strcmp(string(item), "NaN"), ...
                'Non-numeric manifest value for %s:%s', artifactPath, field);
        end
    end
    expected = normalized;
end
expected = double(expected);
assert(numel(actual) == numel(expected), ...
    'Length mismatch for %s:%s', artifactPath, field);
actual = actual(:);
expected = expected(:);
sameNaN = isnan(actual) & isnan(expected);
finite = isfinite(actual) & isfinite(expected);
scale = max(1, abs(expected));
close = abs(actual - expected) <= 1e-10 .* scale;
assert(all(sameNaN | (finite & close), 'all'), ...
    'Value mismatch for %s:%s', artifactPath, field);
end

function found = contains_sensitive_path(value)
found = false;
if ischar(value) || isstring(value)
    text = string(value);
    unixPersonal = "/home/";
    windowsPersonal = "C:" + "\\" + "Users" + "\\";
    found = any(contains(text, unixPersonal)) || ...
        any(contains(text, windowsPersonal));
elseif isstruct(value)
    fields = fieldnames(value);
    for i = 1:numel(value)
        for j = 1:numel(fields)
            if contains_sensitive_path(value(i).(fields{j}))
                found = true;
                return;
            end
        end
    end
elseif iscell(value)
    for i = 1:numel(value)
        if contains_sensitive_path(value{i})
            found = true;
            return;
        end
    end
elseif istable(value)
    found = contains_sensitive_path(table2cell(value));
end
end

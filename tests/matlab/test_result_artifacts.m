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

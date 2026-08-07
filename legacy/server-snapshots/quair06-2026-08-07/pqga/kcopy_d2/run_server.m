% run_server.m -- server driver for gamma_k(CPTP, d=2), k=1..4
% Detached run: matlab -batch "cd('~/projects/pqga/kcopy_d2'); run_server"

addpath(genpath('<QINFO_ROOT>'));
cvx_solver mosek
cvx_quiet(true);

kmax = 4;
d = 2;

fprintf('=== gamma_k(CPTP, d=2) server run, k=1..%d ===\n\n', kmax);

% 0. self-test
t0 = tic;
g1 = gamma_k_d2(1, 'full', false);
assert(abs(g1 - 5.5) < 1e-5, 'SELF-TEST FAILED: gamma_1 = %.6f', g1);
fprintf('[self-test passed] gamma_1 = %.8f  (%.1fs)\n\n', g1, toc(t0));

% 1. full sequence
gam_full = nan(1,kmax); pp = nan(1,kmax); pm = nan(1,kmax); rt = nan(1,kmax);
for k = 1:kmax
    t = tic;
    [gam_full(k), pp(k), pm(k)] = gamma_k_d2(k, 'full', true);
    rt(k) = toc(t);
    fprintf('      (runtime %.1fs, p+ - p- = %.6f)\n', rt(k), pp(k)-pm(k));
end

% 2. linear relaxation comparison
fprintf('\n--- m>=2 binding test (full vs linear) ---\n');
gam_lin = nan(1,kmax);
for k = 1:kmax
    gam_lin(k) = gamma_k_d2(k, 'linear', false);
    tag = '';
    if abs(gam_lin(k) - gam_full(k)) < 1e-5, tag = '   <-- m>=2 NOT binding'; end
    fprintf(' k=%d : full=%.8f  linear=%.8f  diff=%.2e%s\n', ...
            k, gam_full(k), gam_lin(k), gam_full(k)-gam_lin(k), tag);
end

% 3. sequence analysis
fprintf('\n--- sequence analysis ---\n');
fprintf(' k :  gamma_k       gamma_k-1      ratio\n');
for k = 1:kmax
    if k==1
        fprintf(' %d :  %12.8f   %12.8f\n', k, gam_full(k), gam_full(k)-1);
    else
        fprintf(' %d :  %12.8f   %12.8f    %10.6f\n', k, gam_full(k), gam_full(k)-1, ...
                (gam_full(k)-1)/(gam_full(k-1)-1));
    end
end

% 4. rational guesses
fprintf('\n exact-rational guesses:\n');
for k = 1:kmax
    [n, den] = rat(gam_full(k), 1e-6);
    fprintf(' k=%d : %d/%d  (= %.8f)\n', k, n, den, gam_full(k));
end

% 5. comparison with known certified values
known = [5.5, 2.71333026, 1.888291441, 1.529423184];
fprintf('\n--- comparison with certified values ---\n');
for k = 1:min(kmax, numel(known))
    fprintf(' k=%d : this=%.8f  certified=%.8f  diff=%.2e\n', ...
            k, gam_full(k), known(k), abs(gam_full(k)-known(k)));
end

save('kcopy_d2_results.mat','gam_full','gam_lin','pp','pm','rt','kmax');
fprintf('\n=== done, saved kcopy_d2_results.mat ===\n');

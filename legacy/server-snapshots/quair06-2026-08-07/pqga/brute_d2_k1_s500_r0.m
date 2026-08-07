% brute.m -- un-reduced k-copy programming SDP (independent check, no Brauer reduction)
d = 2; k = 1; s = 500;
addpath(genpath("<QETLAB_ROOT>"));
rng(0);
D = d^(2*k+2); dk = d^k; dim_tp = d^(2*k+1); I_d = eye(d);
fprintf("brute gamma_%d(CPTP, d=%d), D=%d\n", k, d, D);
JC = zeros(d^2, d^2, s); ins = zeros(D, D, s);
for c = 1:s
    JC(:,:,c) = RandomSuperoperator(d) / d;
    temp = JC(:,:,c);
    for kk = 1:k-1
        temp = kron(temp, JC(:,:,c));
    end
    ins(:,:,c) = Tensor(I_d, transpose(temp), I_d);
end
dims_all = d * ones(1, 2*k+2);
cvx_begin sdp quiet
    cvx_solver mosek
    variable J1(D,D) hermitian semidefinite
    variable J2(D,D) hermitian semidefinite
    variable p1
    variable p2
    minimize(p1 + p2)
    PartialTrace(J1, 2*k+2, dims_all) == p1 * eye(dim_tp);
    PartialTrace(J2, 2*k+2, dims_all) == p2 * eye(dim_tp);
    for c = 1:s
        prog = PartialTrace((J1 - J2) * ins(:,:,c), 2, [d, dk^2, d]);
        prog == d * JC(:,:,c);
    end
cvx_end
cost = p1 + p2;
if ~exist("results","dir"); mkdir("results"); end; save(sprintf("results/brute_d%d_k%d_s%d_r%d.mat",d,k,s,0),"cost","d","k","s","cvx_status");
fprintf("RESULT brute gamma_%d(CPTP, %d) = %.6f  [%s]\n", k, d, cost, cvx_status);

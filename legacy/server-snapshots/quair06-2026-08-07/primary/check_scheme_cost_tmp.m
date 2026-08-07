function check_scheme_cost_tmp()
addpath('<CVX_ROOT>');
cvx_setup quiet;
for k = 1:3
    J = scheme_choi(k);
    D = size(J, 1);
    nIn = D / 2;
    cvx_begin sdp quiet
        cvx_solver sdpt3
        variable Jp(D,D) hermitian
        variable Jm(D,D) hermitian
        variable pp nonnegative
        variable pm nonnegative
        minimize(pp + pm)
        Jp - Jm == J;
        Jp >= 0;
        Jm >= 0;
        Jp(1:nIn,1:nIn) + Jp(nIn+1:D,nIn+1:D) == pp * eye(nIn);
        Jm(1:nIn,1:nIn) + Jm(nIn+1:D,nIn+1:D) == pm * eye(nIn);
    cvx_end
    fprintf('SCHEME_COST k=%d cost=%.12f status=%s pp=%.12f pm=%.12f\n', ...
        k, cvx_optval, cvx_status, pp, pm);
end
end

function J = scheme_choi(k)
% Qubit order: O, S, A1, B1, ..., Ak, Bk. O is first so Tr_O is block-contiguous.
nq = 2*k + 2;
D = 2^nq;
J = 0.5 * eye(D);
for i = 1:k
    A = 2 + 2*i - 1;
    B = 2 + 2*i;
    J = J + local_term(nq, 2, A, B, 1) / k;
end
J = (J + J') / 2;
end

function T = local_term(nq, S, A, B, O)
D = 2^nq;
T = zeros(D,D);
for col = 0:D-1
    inBits = bits_of(col, nq);
    for row = 0:D-1
        outBits = bits_of(row, nq);
        restOk = true;
        for q = 1:nq
            if q ~= S && q ~= A && q ~= B && q ~= O
                if outBits(q) ~= inBits(q)
                    restOk = false;
                    break;
                end
            end
        end
        if ~restOk
            continue;
        end
        omegaSA = (outBits(S) == outBits(A)) && (inBits(S) == inBits(A));
        if ~omegaSA
            continue;
        end
        omegaBO = (outBits(B) == outBits(O)) && (inBits(B) == inBits(O));
        identBO = (outBits(B) == inBits(B)) && (outBits(O) == inBits(O));
        val = 2 * double(omegaBO) - double(identBO);
        if val ~= 0
            T(row+1, col+1) = val;
        end
    end
end
end

function b = bits_of(x, nq)
b = zeros(1, nq);
for q = 1:nq
    b(q) = bitget(x, nq - q + 1);
end
end

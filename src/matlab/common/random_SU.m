function U = random_SU(d)
%RANDOM_SU  Generate a Haar-random element of SU(d).
%
%   U = random_SU(d) returns a d x d unitary matrix with determinant 1,
%   sampled uniformly from the Haar measure on SU(d).

    Z = randn(d) + 1i*randn(d);
    [Q, R] = qr(Z);
    Q = Q * diag(diag(R) ./ abs(diag(R)));
    U = Q / det(Q)^(1/d);
end

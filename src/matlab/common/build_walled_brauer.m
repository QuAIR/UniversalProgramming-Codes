function M = build_walled_brauer(sigma, d, k, sector)
%BUILD_WALLED_BRAUER  Matrix representation of a walled Brauer diagram.
%
%   M = build_walled_brauer(sigma, d, k, sector)
%
%   Each diagram in the walled Brauer algebra B_{1,k}(d) or B_{k,1}(d)
%   corresponds to a permutation sigma of {1, ..., k+1}, mapping the
%   (k+1) covariant nodes to the (k+1) contravariant nodes.
%
%   The matrix element formula (from Schur-Weyl duality):
%
%     (D_sigma)_{a, b} = prod_{i=1}^{k+1} delta(cov_i, contrav_{sigma(i)})
%
%   For B_{1,k}(d) acting on V_1 (x) V*_2 (x) ... (x) V*_{k+1}:
%     Position 1 = V  (left of wall),  positions 2..k+1 = V* (right of wall)
%     Covariant nodes:     {a_1 (output V),  b_2,...,b_{k+1} (input V*)}
%     Contravariant nodes: {b_1 (input V),   a_2,...,a_{k+1} (output V*)}
%
%     sigma(1)=1:    delta(a_1, b_1)        left through-string
%     sigma(1)=j>1:  delta(a_1, a_j)        top contraction
%     sigma(i>1)=1:  delta(b_i, b_1)        bottom contraction
%     sigma(i>1)=j>1: delta(a_j, b_i)       right through-string
%
%   For B_{k,1}(d) acting on V_1 (x) ... (x) V_k (x) V*_{k+1}:
%     Positions 1..k = V (left of wall),  position k+1 = V* (right of wall)
%     Covariant nodes:     {a_1,...,a_k (output V),  b_{k+1} (input V*)}
%     Contravariant nodes: {b_1,...,b_k (input V),   a_{k+1} (output V*)}
%
%     sigma(i<=k)=j<=k:   delta(a_i, b_j)     left through-string
%     sigma(i<=k)=k+1:    delta(a_i, a_{k+1})  top contraction
%     sigma(k+1)=j<=k:    delta(b_{k+1}, b_j)  bottom contraction
%     sigma(k+1)=k+1:     delta(a_{k+1}, b_{k+1}) right through-string
%
%   Inputs:
%     sigma  - permutation of 1:(k+1)   (1-indexed)
%     d      - local Hilbert-space dimension
%     k      - number of programmer copies
%     sector - '1k' for B_{1,k}(d) or 'k1' for B_{k,1}(d)
%
%   Output:
%     M      - d^(k+1) x d^(k+1) real matrix

n    = k + 1;
Dsec = d^n;
M    = zeros(Dsec, Dsec);

%-- Precompute multi-index tables (row -> (i1,...,in), 1-indexed) --------
subs = zeros(Dsec, n);
for r = 1:Dsec
    tmp = r - 1;
    for p = n:-1:1
        subs(r, p) = mod(tmp, d) + 1;
        tmp        = floor(tmp / d);
    end
end

%-- Determine the wall position ----------------------------------------
if strcmp(sector, '1k')
    wall = 1;        % positions 1..wall are V, wall+1..n are V*
elseif strcmp(sector, 'k1')
    wall = k;        % positions 1..wall are V, wall+1..n are V*
else
    error('sector must be ''1k'' or ''k1''.');
end

%-- Build matrix element by element ------------------------------------
for r = 1:Dsec
    a = subs(r, :);   % output indices
    for c = 1:Dsec
        b = subs(c, :);   % input  indices
        val = 1;

        for node = 1:n
            target = sigma(node);

            % Classify the node and its target
            node_is_left   = (node   <= wall);
            target_is_left = (target <= wall);

            if node_is_left && target_is_left
                % Both on left side of wall:
                %   cov = output a(node), contrav = input b(target)
                %   left through-string:  delta(a_node, b_target)
                val = val * (a(node) == b(target));

            elseif node_is_left && ~target_is_left
                % cov left, contrav right:
                %   cov = output a(node), contrav = output a(target)
                %   top contraction:  delta(a_node, a_target)
                val = val * (a(node) == a(target));

            elseif ~node_is_left && target_is_left
                % cov right, contrav left:
                %   cov = input b(node), contrav = input b(target)
                %   bottom contraction:  delta(b_node, b_target)
                val = val * (b(node) == b(target));

            else  % ~node_is_left && ~target_is_left
                % Both on right side:
                %   cov = input b(node), contrav = output a(target)
                %   right through-string:  delta(a_target, b_node)
                val = val * (a(target) == b(node));
            end

            if val == 0, break; end   % short-circuit
        end

        M(r, c) = val;
    end
end

end

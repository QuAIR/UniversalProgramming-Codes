function [gam, pplus, pminus, info] = gamma_k_d2(k, mode, verbose)
% GAMMA_K_D2  Exact k-copy qubit programming cost gamma_k(CPTP, d=2),
%             via the SU(2) Schur-Weyl SYMMETRY-REDUCED SDP.
%
%   [gam,pplus,pminus,info] = gamma_k_d2(k, mode, verbose)
%
%   The PSD variables are the SMALL sector blocks  C^pm_{mu,nu}  on the SU(2)
%   multiplicity spaces (mu,nu = two-row Young diagrams of k+1 boxes; total size
%   = Catalan(k+1) = 2,5,14,42,132,... -- NOT the 4^{k+1} full space). The
%   covariant Choi is reconstructed as
%        Jtilde_pm = (+)_{mu,nu} I_{U_mu} (x) I_{U_nu} (x) C^pm_{mu,nu}   (Schur basis)
%        J_pm      = Theta' * Jtilde_pm * Theta                            (original frame)
%   where Theta applies the spin flip eps = -i*sigma_y on the conjugate-rep
%   factors (the A_i and S'), which is what makes the d=2 commutant ordinary
%   SU(2) Schur-Weyl (W* ~= W). Registers, GROUPED order:
%        S, A_1..A_k, B_1..B_k, S'   (H_U = S,A's ; H_V = B's,S')
%
%   Constraints:
%     (C1') C^pm_{mu,nu} >= 0                                   (small PSD blocks)
%     (C2') Tr_{S'}[J_pm] = p_pm I                              (trace preservation)
%     (C3') programming.  In 'full' mode this is imposed EXACTLY by
%           deterministic polarization over the 13 CPTP-Choi "letters"
%           {J0=I/2, G_1..G_12 (sigma_a x sigma_b, b!=0)}:
%             Tr_{P^k}[ J (I_S (x) Sym_M(L^T) (x) I_{S'}) ] = 2^k * {J0 | G_a | 0}
%
%   mode :
%     'full'   (default) -- all orders m=0..k of (C3') -> exact gamma_k.
%                 This implementation uses the redundant polarized multiset rows.
%     'linear' -- only m=0,1.  This drops the m>=2 rows, so it is only a
%                 lower-bound relaxation: gamma(linear) <= gamma(full).  A
%                 positive full-linear gap means the omitted rows are binding.
%   verbose : print a summary (default true).
%
%   Requires CVX (http://cvxr.com) + SDPT3/SeDuMi/MOSEK.
%   SELF-TEST:  gamma_k_d2(1,'full') = 5.5  ( = 2 d^2 - 3 + 2/d^2 at d=2 ).
%   (Validated against an independent Python/CVXPY solve.)

if nargin < 2 || isempty(mode),    mode    = 'full'; end
if nargin < 3 || isempty(verbose), verbose = true;   end
mode = lower(mode);
if ~ismember(mode, {'full', 'linear'})
    error('gamma_k_d2:badMode', 'mode must be ''full'' or ''linear'', got ''%s''.', mode);
end
d  = 2; m = k+1; nq = 2*m; D = 2^nq;
I2 = eye(2); sx=[0 1;1 0]; sy=[0 -1i;1i 0]; sz=[1 0;0 -1]; P={I2,sx,sy,sz};
ep = [0 -1;1 0];                          % eps = -i sigma_y

% --- 13 letters: J0 = I/2, and sigma_a (x) sigma_b with b in {x,y,z} ---
L = {eye(4)/2};
for a=1:4, for b=2:4, L{end+1}=kron(P{a},P{b}); end, end %#ok<AGROW>   % 13 total

% --- Theta (grouped order): eps on A_1..A_k (positions 2..k+1) and S' (last) ---
ops = cell(1,nq); ops{1}=I2;
for i=1:k, ops{1+i}=ep; end          % A_i
for i=1:k, ops{1+k+i}=I2; end        % B_i
ops{nq}=ep;                          % S'
Th = ops{1}; for q=2:nq, Th = kron(Th, ops{q}); end

% --- SU(2) Schur transform on m qubits: sectors + multiplicity-transfer ops ---
[spins, Mo, mult] = schur_data(m);  ns = numel(spins);
ranges = cell(ns,ns); off = 0;
for ai=1:ns, for bi=1:ns
    s = mult(ai)*mult(bi); ranges{ai,bi} = off+(1:s); off = off+s;
end, end
Stot = off;                          % = Catalan(m)

% --- multisets of the 13 letters of size k ---
if strcmp(mode,'full'),  MS = local_multisets(13,k);
else,  MS = {ones(1,k)};  for g=2:13, MS{end+1}=sort([g,ones(1,k-1)]); end %#ok<AGROW>
end

half = 2^(nq-1); nmid = 2^(nq-2); midshift = (0:nmid-1)*2;
Embed = local_embed_cache(L, k, nq);

cvx_begin sdp
  variable Cp(Stot,Stot) hermitian semidefinite     % diag blocks = C^+_{mu,nu}
  variable Cm(Stot,Stot) hermitian semidefinite     % diag blocks = C^-_{mu,nu}
  variable pplus  nonnegative
  variable pminus nonnegative

  Jtp = build_Jtilde(Cp, ranges, Mo, mult, ns, D);
  Jtm = build_Jtilde(Cm, ranges, Mo, mult, ns, D);
  Jpo = Th' * Jtp * Th;   Jmo = Th' * Jtm * Th;   J = Jpo - Jmo;   % original frame

  minimize( pplus + pminus )
  subject to
    % (C2') trace preservation (S' = last qubit)
    Jpo(1:2:D,1:2:D) + Jpo(2:2:D,2:2:D) == pplus  * eye(D/2);
    Jmo(1:2:D,1:2:D) + Jmo(2:2:D,2:2:D) == pminus * eye(D/2);
    % (C3') programming by polarization
    for c = 1:numel(MS)
        M  = MS{c};
        Oe = local_oper(M, Embed, k, nq); % I_S (x) Sym_M(L^T) (x) I_{S'}
        nz = M(M ~= 1);
        if     isempty(nz),    R = (d^k)*L{1};
        elseif numel(nz)==1,   R = (d^k)*L{nz(1)};
        else                   R = zeros(4,4);
        end
        M2 = J * Oe;                       % keep S (MSB) & S' (LSB), trace middle:
        for row=1:4
          s=floor((row-1)/2); sp=mod(row-1,2); ia = s*half + sp + 1 + midshift;
          for col=1:4
            s2=floor((col-1)/2); sp2=mod(col-1,2); ib = s2*half + sp2 + 1 + midshift;
            sum(diag( M2(ia,ib) )) == R(row,col);
          end
        end
    end
cvx_end

gam = cvx_optval; info.status = cvx_status; info.mode = mode;
info.isRelaxation = strcmp(mode, 'linear');
info.Stot = Stot; info.nMultisets = numel(MS); info.spins = spins; info.mult = mult;
if verbose
  fprintf('k=%d [%s]: gamma=%.8f (p+=%.4f p-=%.4f, p+-p-=%.4f)  [%s, blocks dim=%d, %d constraints]\n',...
          k, mode, gam, pplus, pminus, pplus-pminus, cvx_status, Stot, numel(MS));
end
end
% ======================================================================
function Jt = build_Jtilde(C, ranges, Mo, mult, ns, D)
% Jtilde = sum_{mu,nu} sum_{p,p',q,q'} C_{mu,nu}[(p,q),(p',q')] M^U_{mu,p p'} (x) M^V_{nu,q q'}
Jt = zeros(D,D);
for ai=1:ns
  for bi=1:ns
    Cb = C(ranges{ai,bi}, ranges{ai,bi}); na=mult(ai); nb=mult(bi);
    for p=1:na, for pp=1:na
      MU = Mo{ai}{p,pp};
      for q=1:nb, for qq=1:nb
        Jt = Jt + Cb((p-1)*nb+q, (pp-1)*nb+qq) * kron(MU, Mo{bi}{q,qq});
      end, end
    end, end
  end
end
end
% ======================================================================
function O = local_oper(M, Embed, k, nq)
% Sym over assignments of the (transposed) letters in M to the k program pairs;
% pair i = qubits (1+i, 1+k+i) in the GROUPED order (A_i in H_U, B_i in H_V).
PM = unique(perms(M),'rows'); O = zeros(2^nq);
for r=1:size(PM,1)
    T = eye(2^nq);
    for i=1:k, T = T * Embed{PM(r,i), i}; end
    O = O + T;
end
end
% ======================================================================
function Embed = local_embed_cache(L, k, nq)
Embed = cell(numel(L), k);
for g=1:numel(L)
  for i=1:k
    Embed{g,i} = local_embed(L{g}.', [1+i, 1+k+i], nq);
  end
end
end
% ======================================================================
function O = local_embed(X, targets, nq)
% place 2-qubit op X (4x4) on qubits 'targets' (1-indexed, MSB=qubit 1); I else.
kk = numel(targets); M0 = kron(X, eye(2^(nq-kk)));
rest = setdiff(1:nq, targets); newpos = [targets, rest];   % qubit j -> position newpos(j)
O = local_permute(M0, newpos, nq);
end
% ======================================================================
function O = local_permute(M, newpos, nq)
D = 2^nq; idx = (0:D-1)'; bits = zeros(D,nq);
for q=1:nq, bits(:,q) = bitget(idx, nq-q+1); end     % bits(:,1)=MSB
nb = zeros(D,nq); for q=1:nq, nb(:,newpos(q)) = bits(:,q); end
w = 2.^(nq-(1:nq)); nidx = nb*w(:); Pm = sparse(nidx+1, idx+1, 1, D, D);
O = Pm * M * Pm';
end
% ======================================================================
function MS = local_multisets(n,k)
C = nchoosek(1:(n+k-1), k); MS = cell(size(C,1),1);
for r=1:size(C,1), MS{r} = C(r,:) - (0:k-1); end
end
% ======================================================================
function [spins, Mo, mult] = schur_data(m)
% iterated Clebsch-Gordan Schur transform of (C^2)^{(x)m}.
st(1) = struct('j',0.5,'M', 0.5,'path',0.5,'vec',[1;0]);
st(2) = struct('j',0.5,'M',-0.5,'path',0.5,'vec',[0;1]);
n = 1;
while n < m
  keys={}; grp={};
  for s=1:numel(st)
    key = sprintf('%.1f|%s', st(s).j, mat2str(st(s).path));
    ix = find(strcmp(keys,key),1);
    if isempty(ix), keys{end+1}=key; grp{end+1}=s; else, grp{ix}(end+1)=s; end %#ok<AGROW>
  end
  new = struct('j',{},'M',{},'path',{},'vec',{});
  for g=1:numel(grp)
    ix=grp{g}; j=st(ix(1)).j; path=st(ix(1)).path;
    Mm = containers.Map('KeyType','double','ValueType','any');
    for ii=ix, Mm(st(ii).M)=st(ii).vec; end
    Js = j+0.5; if j-0.5>=0, Js=[j+0.5, j-0.5]; end
    for J = Js
      MM=-J;
      while MM < J+1e-9
        [cpv,cm]=cg_half(j,MM,J); v=zeros(2^(n+1),1);
        if isKey(Mm,MM-0.5), v=v+cpv*kron(Mm(MM-0.5),[1;0]); end
        if isKey(Mm,MM+0.5), v=v+cm *kron(Mm(MM+0.5),[0;1]); end
        new(end+1)=struct('j',J,'M',MM,'path',[path J],'vec',v); %#ok<AGROW>
        MM=MM+1;
      end
    end
  end
  st=new; n=n+1;
end
spins = sort(unique(arrayfun(@(s)s.j,st)),'descend'); ns=numel(spins);
Mo=cell(ns,1); mult=zeros(ns,1);
for a=1:ns
  j=spins(a); sel=find(arrayfun(@(s)abs(s.j-j)<1e-9, st));
  pstr=arrayfun(@(s)mat2str(s.path), st(sel),'UniformOutput',false);
  up=unique(pstr); mult(a)=numel(up); B=cell(mult(a),mult(a));
  for p=1:mult(a), for q=1:mult(a)
    Mt=zeros(2^m,2^m);
    for s=sel(:)'
      if strcmp(mat2str(st(s).path),up{p})
        for s2=sel(:)'
          if strcmp(mat2str(st(s2).path),up{q}) && abs(st(s2).M-st(s).M)<1e-9
            Mt = Mt + st(s).vec*st(s2).vec';
          end
        end
      end
    end
    B{p,q}=Mt;
  end, end
  Mo{a}=B;
end
end
% ======================================================================
function [cp,cm] = cg_half(j,M,J)
if abs(J-(j+0.5))<1e-9, cp=sqrt((j+M+0.5)/(2*j+1)); cm=sqrt((j-M+0.5)/(2*j+1));
else, cp=-sqrt((j-M+0.5)/(2*j+1)); cm=sqrt((j+M+0.5)/(2*j+1)); end
end

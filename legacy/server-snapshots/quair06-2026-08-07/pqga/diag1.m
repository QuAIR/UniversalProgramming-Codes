addpath(genpath("<QETLAB_ROOT>"));
fprintf("=== (i) PermuteSystems convention probe ===\n");
A2=[1 2;3 4]; B2=[0 1;1 0]; C2=[2 0;0 5];
X = Tensor(A2,B2,C2);
Y = PermuteSystems(X, [2 3 1], [2 2 2]);
fprintf("gather err  (out_j = in_perm(j)): %.3e\n", norm(Y - Tensor(B2,C2,A2),'fro'));
fprintf("scatter err (in_i -> out perm(i)): %.3e\n", norm(Y - Tensor(C2,A2,B2),'fro'));

fprintf("=== (ii) QETLAB Choi orientation ===\n");
d=2; JE = RandomSuperoperator(d);
fprintf("||tr_sys2(JE)-I|| = %.3e   ||tr_sys1(JE)-I|| = %.3e\n", ...
  norm(PartialTrace(JE,2,[d d])-eye(d),'fro'), norm(PartialTrace(JE,1,[d d])-eye(d),'fro'));

fprintf("=== (iii) k=1 witness: paper J_P* vs code conventions (d=2) ===\n");
k=1; n=k+1; Dsec=d^n; dk=d^k; dim_tp=d^(2*k+1); I_d=eye(d);
ket = reshape(eye(d),[],1); Phi = ket*ket';
JPstar = (1/d)*Tensor(eye(d^2),eye(d^2)) - Tensor(Phi,eye(d^2)) + d*Tensor(Phi,Phi);
maxA=0; maxA2=0;
for t=1:25
  JE = RandomSuperoperator(d);
  L1 = PartialTrace(JPstar*Tensor(I_d, transpose(JE), I_d), 2, [d, d^2, d]);
  maxA = max(maxA, norm(L1 - d*JE,'fro'));
  L2 = PartialTrace(JPstar*Tensor(I_d, PartialTranspose(JE,1,[d d]), I_d), 2, [d, d^2, d]);
  maxA2 = max(maxA2, norm(L2 - d*JE,'fro'));
end
fprintf("Test A  (full transpose, as coded): %.3e\n", maxA);
fprintf("Test A2 (partial transpose on leg 1): %.3e\n", maxA2);

fprintf("=== (iv) k=1 code-path basis + constraint witness ===\n");
all_perms = perms(1:n); n_diag = size(all_perms,1);
mats_1k=cell(1,n_diag); mats_k1=cell(1,n_diag);
for p=1:n_diag
  mats_1k{p}=build_walled_brauer(all_perms(p,:),d,k,'1k');
  mats_k1{p}=build_walled_brauer(all_perms(p,:),d,k,'k1');
end
V=zeros(Dsec^2,n_diag); for j=1:n_diag, V(:,j)=mats_1k{j}(:); end
[~,Rq,Eq]=qr(V,0); tol=max(size(V))*eps(norm(diag(Rq),'inf')); bl1=sum(abs(diag(Rq))>tol); kp=sort(Eq(1:bl1)); basis_1k=mats_1k(kp);
V=zeros(Dsec^2,n_diag); for j=1:n_diag, V(:,j)=mats_k1{j}(:); end
[~,Rq,Eq]=qr(V,0); bl2=sum(abs(diag(Rq))>tol); kp=sort(Eq(1:bl2)); basis_k1=mats_k1(kp);
fprintf("bl1=%d bl2=%d (theory 2,2)\n", bl1, bl2);
m=bl1*bl2;
perm=zeros(1,2*k+2); perm(1)=1;
for i=1:k, perm(i+1)=2*i; perm(k+1+i)=2*i+1; end
perm(2*k+2)=2*k+2; dims_all=d*ones(1,2*k+2);
B=cell(1,m);
for j1=1:bl1, for j2=1:bl2
  B{(j1-1)*bl2+j2}=PermuteSystems(kron(basis_1k{j1},basis_k1{j2}),perm,dims_all);
end, end
M=zeros((d^(2*k+2))^2,m); for j=1:m, M(:,j)=B{j}(:); end
bstar = M \ JPstar(:);
fprintf("span residual: %.3e ; b* = [%s]\n", norm(M*bstar-JPstar(:)), sprintf("%.4f ",bstar));
Tt=zeros(dim_tp^2,m); for j=1:m, tmp=PartialTrace(B{j},2*k+2,dims_all); Tt(:,j)=tmp(:); end
tpm=reshape(Tt*bstar,dim_tp,dim_tp);
fprintf("TP(J_P*): off-identity dev %.3e, mean diag %.4f\n", norm(tpm-trace(tpm)/dim_tp*eye(dim_tp),'fro'), trace(tpm)/dim_tp);
rng(0); maxB=0;
for c=1:40
  JCc=RandomSuperoperator(d)/d; ins=Tensor(I_d,transpose(JCc),I_d);
  lhs=zeros(d^2);
  for j=1:m, lhs=lhs+bstar(j)*PartialTrace(B{j}*ins,2,[d,dk^2,d]); end
  maxB=max(maxB,norm(lhs-d*JCc,'fro'));
end
fprintf("Test B residual (code-path prog with b*): %.3e\n", maxB);

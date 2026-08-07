addpath(genpath("<QETLAB_ROOT>"));
d=2; k=1; n=k+1; Dsec=d^n; dk=d^k; dim_tp=d^(2*k+1); I_d=eye(d);
rng(0);
% pipeline as in runner
all_perms = perms(1:n); n_diag=size(all_perms,1);
mats_1k=cell(1,n_diag); mats_k1=cell(1,n_diag);
for p=1:n_diag
  mats_1k{p}=build_walled_brauer(all_perms(p,:),d,k,'1k');
  mats_k1{p}=build_walled_brauer(all_perms(p,:),d,k,'k1');
end
V=zeros(Dsec^2,n_diag); for j=1:n_diag, V(:,j)=mats_1k{j}(:); end
[~,Rq,Eq]=qr(V,0); tol=max(size(V))*eps(norm(diag(Rq),'inf')); bl1=sum(abs(diag(Rq))>tol); kp=sort(Eq(1:bl1)); basis_1k=mats_1k(kp);
V=zeros(Dsec^2,n_diag); for j=1:n_diag, V(:,j)=mats_k1{j}(:); end
[~,Rq,Eq]=qr(V,0); bl2=sum(abs(diag(Rq))>tol); kp=sort(Eq(1:bl2)); basis_k1=mats_k1(kp);
m=bl1*bl2;
blocks1 = decompose_sector(basis_1k, d, k, '1k');
blocks2 = decompose_sector(basis_k1, d, k, 'k1');
red1=cell(length(blocks1),bl1); red2=cell(length(blocks2),bl2);
for bi=1:length(blocks1), G=blocks1(bi).G_sub; for j=1:bl1, red1{bi,j}=G'*basis_1k{j}*G; end, end
for bi=1:length(blocks2), G=blocks2(bi).G_sub; for j=1:bl2, red2{bi,j}=G'*basis_k1{j}*G; end, end
fprintf("red1 table (rows=blocks, cols=basis):\n");
for bi=1:length(blocks1), for j=1:bl1, fprintf(" %8.4f%+8.4fi", real(red1{bi,j}), imag(red1{bi,j})); end; fprintf("\n"); end
fprintf("red2 table:\n");
for bi=1:length(blocks2), for j=1:bl2, fprintf(" %8.4f%+8.4fi", real(red2{bi,j}), imag(red2{bi,j})); end; fprintf("\n"); end
% full basis B, T, P with runner conventions (perm=identity at k=1)
perm=[1 2 3 4]; dims_all=d*ones(1,2*k+2);
B=cell(1,m);
for j1=1:bl1, for j2=1:bl2, B{(j1-1)*bl2+j2}=PermuteSystems(kron(basis_1k{j1},basis_k1{j2}),perm,dims_all); end, end
s=500;
JC=zeros(d^2,d^2,s);
for c=1:s, JC(:,:,c)=RandomSuperoperator(d)/d; end
T=zeros(dim_tp,dim_tp,m); for j=1:m, T(:,:,j)=PartialTrace(B{j},2*k+2,dims_all); end
P=zeros(d^2,d^2,m,s);
for c=1:s
  ins=Tensor(I_d, JC(:,:,c).', I_d);
  for j=1:m, P(:,:,j,c)=PartialTrace(B{j}*ins,2,[d,dk^2,d]); end
end
% witness
ket=reshape(eye(d),[],1); Phi=ket*ket';
JPstar=(1/d)*Tensor(eye(d^2),eye(d^2))-Tensor(Phi,eye(d^2))+d*Tensor(Phi,Phi);
M=zeros(16^2,m); for j=1:m, M(:,j)=B{j}(:); end
bstar=M\JPstar(:);
res=0;
for c=1:s
  lhs=zeros(d^2); for j=1:m, lhs=lhs+bstar(j)*P(:,:,j,c); end
  res=max(res,norm(lhs-d*JC(:,:,c),'fro'));
end
fprintf("witness prog residual over all 500 runner channels: %.3e\n", res);
% tiny CVX problems: (solver, s_used)
for trial = 1:4
  if trial==1, slv="mosek"; su=500; elseif trial==2, slv="sedumi"; su=500; elseif trial==3, slv="mosek"; su=50; else, slv="sedumi"; su=50; end
  cvx_begin sdp quiet
    cvx_solver(char(slv))
    variable b1v(m)
    variable b2v(m)
    variable q1
    variable q2
    minimize(q1+q2)
    for bi=1:length(blocks1), for bj=1:length(blocks2)
      e1=0; e2=0;
      for j1=1:bl1, for j2=1:bl2
        idx=(j1-1)*bl2+j2; R=kron(red1{bi,j1},red2{bj,j2});
        e1=e1+b1v(idx)*R; e2=e2+b2v(idx)*R;
      end, end
      (e1+e1')/2 >= 0; (e2+e2')/2 >= 0;
    end, end
    TP1=0; TP2=0;
    for j=1:m, TP1=TP1+b1v(j)*T(:,:,j); TP2=TP2+b2v(j)*T(:,:,j); end
    TP1 == q1*eye(dim_tp); TP2 == q2*eye(dim_tp);
    for c=1:su
      pr=0; for j=1:m, pr=pr+(b1v(j)-b2v(j))*P(:,:,j,c); end
      pr == d*JC(:,:,c);
    end
  cvx_end
  fprintf("trial %d: solver=%s s=%d -> cost=%.6f status=%s\n", trial, slv, su, q1+q2, cvx_status);
end

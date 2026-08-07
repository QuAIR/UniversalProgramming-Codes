addpath(genpath("<QETLAB_ROOT>"));
d=2; k=1; n=k+1; Dsec=d^n; dk=d^k; dim_tp=d^(2*k+1); I_d=eye(d);
rng(0);
all_perms = perms(1:n); n_diag=size(all_perms,1);
mats_1k=cell(1,n_diag); mats_k1=cell(1,n_diag);
for p=1:n_diag
  mats_1k{p}=build_walled_brauer(all_perms(p,:),d,k,'1k');
  mats_k1{p}=build_walled_brauer(all_perms(p,:),d,k,'k1');
end
basis_1k=mats_1k([1 2]); basis_k1=mats_k1([1 2]);  % {Phi, I} order as in runner
bl1=2; bl2=2; m=4;
blocks1 = decompose_sector(basis_1k, d, k, '1k');
blocks2 = decompose_sector(basis_k1, d, k, 'k1');
red1=cell(2,2); red2=cell(2,2);
for bi=1:2, G=blocks1(bi).G_sub; for j=1:2, red1{bi,j}=G'*basis_1k{j}*G; end, end
for bi=1:2, G=blocks2(bi).G_sub; for j=1:2, red2{bi,j}=G'*basis_k1{j}*G; end, end
perm=[1 2 3 4]; dims_all=d*ones(1,4);
B=cell(1,4);
for j1=1:2, for j2=1:2, B{(j1-1)*2+j2}=PermuteSystems(kron(basis_1k{j1},basis_k1{j2}),perm,dims_all); end, end
s=50; JC=zeros(4,4,s);
for c=1:s, JC(:,:,c)=RandomSuperoperator(d)/d; end
T=zeros(8,8,4); for j=1:4, T(:,:,j)=PartialTrace(B{j},4,dims_all); end
P=zeros(4,4,4,s);
for c=1:s
  ins=Tensor(I_d, JC(:,:,c).', I_d);
  for j=1:4, P(:,:,j,c)=PartialTrace(B{j}*ins,2,[d,4,d]); end
end
% explicit paper-split point, idx order (PhiPhi, PhiI, IPhi, II)
bstar=[2; -1; 0; 0.5];
b2x=[-1.5; 0.75; 2.25; 0];
b1x=b2x+bstar;
p1x=3.25; p2x=2.25;
TPof=@(b) reshape(reshape(T,[],4)*b,8,8);
fprintf("check TP(b1)-p1 I: %.3e   TP(b2)-p2 I: %.3e\n", norm(TPof(b1x)-p1x*eye(8),'fro'), norm(TPof(b2x)-p2x*eye(8),'fro'));
sec=@(b,bi,bj) real(b(1)*red1{bi,1}*red2{bj,1}+b(2)*red1{bi,1}*red2{bj,2}+b(3)*red1{bi,2}*red2{bj,1}+b(4)*red1{bi,2}*red2{bj,2});
fprintf("sectors b1: "); for bi=1:2, for bj=1:2, fprintf("%.4f ", sec(b1x,bi,bj)); end, end, fprintf("\n");
fprintf("sectors b2: "); for bi=1:2, for bj=1:2, fprintf("%.4f ", sec(b2x,bi,bj)); end, end, fprintf("\n");
rmax=0; for c=1:s
  lhs=zeros(4); for j=1:4, lhs=lhs+(b1x(j)-b2x(j))*P(:,:,j,c); end
  rmax=max(rmax,norm(lhs-d*JC(:,:,c),'fro'));
end
fprintf("prog residual at explicit point: %.3e\n", rmax);
% CVX bisection: add families one at a time
for stage=1:3
  cvx_begin sdp quiet
    cvx_solver mosek
    variable b1v(4)
    variable b2v(4)
    variable q1
    variable q2
    minimize(q1+q2)
    for c=1:s
      pr=0; for j=1:4, pr=pr+(b1v(j)-b2v(j))*P(:,:,j,c); end
      pr == d*JC(:,:,c);
    end
    if stage>=2
      reshape(reshape(T,[],4)*b1v,8,8) == q1*eye(8);
      reshape(reshape(T,[],4)*b2v,8,8) == q2*eye(8);
    end
    if stage>=3
      for bi=1:2, for bj=1:2
        e1=0; e2=0;
        for j1=1:2, for j2=1:2
          idx=(j1-1)*2+j2; R=kron(red1{bi,j1},red2{bj,j2});
          e1=e1+b1v(idx)*R; e2=e2+b2v(idx)*R;
        end, end
        (e1+e1')/2 >= 0; (e2+e2')/2 >= 0;
      end, end
    end
  cvx_end
  fprintf("stage %d (families<=%d): cost=%.6f status=%s\n", stage, stage, q1+q2, cvx_status);
end

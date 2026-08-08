addpath(genpath("<QETLAB_ROOT>"));
d=2; k=1; n=k+1; Dsec=d^n; dk=d^k; dim_tp=d^(2*k+1); I_d=eye(d);
rng(0);
all_perms = perms(1:n);
mats_1k=cell(1,2); mats_k1=cell(1,2);
for p=1:2
  mats_1k{p}=build_walled_brauer(all_perms(p,:),d,k,'1k');
  mats_k1{p}=build_walled_brauer(all_perms(p,:),d,k,'k1');
end
basis_1k=mats_1k; basis_k1=mats_k1; bl1=2; bl2=2; m=4;
blocks1=decompose_sector(basis_1k,d,k,'1k'); blocks2=decompose_sector(basis_k1,d,k,'k1');
red1=cell(2,2); red2=cell(2,2);
for bi=1:2, G=blocks1(bi).G_sub; for j=1:2, red1{bi,j}=G'*basis_1k{j}*G; end, end
for bi=1:2, G=blocks2(bi).G_sub; for j=1:2, red2{bi,j}=G'*basis_k1{j}*G; end, end
B=cell(1,4);
for j1=1:2, for j2=1:2, B{(j1-1)*2+j2}=PermuteSystems(kron(basis_1k{j1},basis_k1{j2}),[1 2 3 4],d*ones(1,4)); end, end
s=50; JC=zeros(4,4,s);
for c=1:s, JC(:,:,c)=RandomSuperoperator(d)/d; end
T=zeros(8,8,4); for j=1:4, T(:,:,j)=PartialTrace(B{j},4,d*ones(1,4)); end
P=zeros(4,4,4,s);
for c=1:s
  ins=Tensor(I_d, JC(:,:,c).', I_d);
  for j=1:4, P(:,:,j,c)=PartialTrace(B{j}*ins,2,[d,4,d]); end
end
b1x=[0.5; -0.25; 2.25; 0.5]; b2x=[-1.5; 0.75; 2.25; 0];  % explicit split (b1=b2+bstar)
% (a) PIN TEST: fully pinned point with original redundant equalities
cvx_begin sdp quiet
  cvx_solver mosek
  variable b1v(4)
  variable b2v(4)
  variable q1
  variable q2
  minimize(q1+q2)
  b1v == b1x; b2v == b2x; q1 == 3.25; q2 == 2.25;
  for c=1:s
    pr=0; for j=1:4, pr=pr+(b1v(j)-b2v(j))*P(:,:,j,c); end
    pr == d*JC(:,:,c);
  end
  reshape(reshape(T,[],4)*b1v,8,8) == q1*eye(8);
  reshape(reshape(T,[],4)*b2v,8,8) == q2*eye(8);
cvx_end
fprintf("(a) pinned point: cost=%.6f status=%s\n", q1+q2, cvx_status);
% (b) PRE-REDUCED equalities, free problem
Apr=zeros(32*s,4); bpr=zeros(32*s,1);
for c=1:s
  Mc=reshape(P(:,:,:,c),16,4); rh=d*reshape(JC(:,:,c),16,1);
  Apr(32*(c-1)+(1:16),:)=real(Mc);  bpr(32*(c-1)+(1:16))=real(rh);
  Apr(32*(c-1)+(17:32),:)=imag(Mc); bpr(32*(c-1)+(17:32))=imag(rh);
end
AB=[Apr bpr]; [~,Rr,Er]=qr(AB,0); rk=sum(abs(diag(Rr))>1e-10*abs(Rr(1,1)));
% re-extract reduced rows in original column order
[Qq,~]=qr(AB',0); Ared_full=Qq(:,1:rk)'; % rk x 5 spanning row space
Ared=Ared_full(:,1:4); bred=Ared_full(:,5);
fprintf("(b) prog rows: %d -> rank %d ; reduced residual at delta*: %.3e\n", 32*s, rk, norm(Ared*(b1x-b2x)-bred));
Atp=[reshape(T,[],4), -reshape(eye(8),[],1)];
[Qt,~]=qr(Atp',0); rkt=rank(Atp,1e-10); Atp_red=Qt(:,1:rkt)';
fprintf("    TP rows: 64 -> rank %d ; residual at (b1x,q1): %.3e\n", rkt, norm(Atp_red*[b1x;3.25]));
cvx_begin sdp quiet
  cvx_solver mosek
  variable b1v(4)
  variable b2v(4)
  variable q1
  variable q2
  minimize(q1+q2)
  Ared*(b1v-b2v) == bred;
  Atp_red*[b1v;q1] == 0;
  Atp_red*[b2v;q2] == 0;
  for bi=1:2, for bj=1:2
    e1=0; e2=0;
    for j1=1:2, for j2=1:2
      idx=(j1-1)*2+j2; R=kron(red1{bi,j1},red2{bj,j2});
      e1=e1+b1v(idx)*R; e2=e2+b2v(idx)*R;
    end, end
    (e1+e1')/2 >= 0; (e2+e2')/2 >= 0;
  end, end
cvx_end
fprintf("(b) reduced-equality free problem: cost=%.6f status=%s  (expect 5.5)\n", q1+q2, cvx_status);

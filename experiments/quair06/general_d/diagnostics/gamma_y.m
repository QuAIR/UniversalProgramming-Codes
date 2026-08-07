% Structured-constraint gamma_k(CPTP,d) solver + certificate.
% TP family imposed exactly via Gram reduction (no dim_tp^2 x m array);
% programming family via the validated M1*Y*M2 factorization;
% PSD blocks assembled as single vectorized CVX ops.
scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(fileparts(fileparts(scriptDir))));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();
up_setup(cfg, true);
outputDir = fullfile(cfg.resultsRoot, 'quair06', 'general_d', 'diagnostics');
if exist(outputDir, 'dir') ~= 7; mkdir(outputDir); end
d=2; k=5; s=500;
n=k+1; Dsec=d^n; D=d^(2*k+2); dk=d^k; I_d=eye(d);
rng(0);
fprintf("=== struct run: gamma_%d(CPTP, d=%d), D=%d ===\n", k, d, D);
all_perms=perms(1:n); n_diag=size(all_perms,1);
mats_1k=cell(1,n_diag); mats_k1=cell(1,n_diag);
for p=1:n_diag
  mats_1k{p}=build_walled_brauer(all_perms(p,:),d,k,'1k');
  mats_k1{p}=build_walled_brauer(all_perms(p,:),d,k,'k1');
end
V=zeros(Dsec^2,n_diag); for j=1:n_diag, V(:,j)=mats_1k{j}(:); end
[~,Rq,Eq]=qr(V,0); tol=max(size(V))*eps(norm(diag(Rq),'inf')); bl1=sum(abs(diag(Rq))>tol); kp=sort(Eq(1:bl1)); basis_1k=mats_1k(kp);
V=zeros(Dsec^2,n_diag); for j=1:n_diag, V(:,j)=mats_k1{j}(:); end
[~,Rq,Eq]=qr(V,0); bl2=sum(abs(diag(Rq))>tol); kp=sort(Eq(1:bl2)); basis_k1=mats_k1(kp);
clear V mats_1k mats_k1
m=bl1*bl2;
fprintf("bl1=%d bl2=%d m=%d\n", bl1, bl2, m);
blocks1=decompose_sector(basis_1k,d,k,'1k'); blocks2=decompose_sector(basis_k1,d,k,'k1');
nb1=length(blocks1); nb2=length(blocks2);
red1=cell(nb1,bl1); red2=cell(nb2,bl2);
for bi=1:nb1, G=blocks1(bi).G_sub; for j=1:bl1, red1{bi,j}=G'*basis_1k{j}*G; end, end
for bi=1:nb2, G=blocks2(bi).G_sub; for j=1:bl2, red2{bi,j}=G'*basis_k1{j}*G; end, end
fprintf("blocks: %dx%d pairs, w1=[%s], w2=[%s]\n", nb1, nb2, num2str([blocks1.w]), num2str([blocks2.w]));
% Hermiticity involution + reduced rows
V1=zeros(Dsec^2,bl1); for jj=1:bl1, tmp=basis_1k{jj}; V1(:,jj)=tmp(:); end; V1i=pinv(V1);
A1=zeros(bl1); for jj=1:bl1, tt=transpose(basis_1k{jj}); A1(:,jj)=real(V1i*tt(:)); end
V2=zeros(Dsec^2,bl2); for jj=1:bl2, tmp=basis_k1{jj}; V2(:,jj)=tmp(:); end; V2i=pinv(V2);
A2=zeros(bl2); for jj=1:bl2, tt=transpose(basis_k1{jj}); A2(:,jj)=real(V2i*tt(:)); end
AhermC=kron(A1,A2)-eye(m); AhermC(abs(AhermC)<1e-9)=0; [~,Sv,Vv]=svd(AhermC); NS=Vv(:,diag(Sv)<1e-7); nn=size(NS,2);
clear AhermC
fprintf("null-space dim: %d of m=%d" + newline, nn, m);
% TP family via exact Gram reduction:
%   tr_{S'}[ B1 (x) B2 ] = B1 (x) T2,  T2 = tr_last(B2);  constraint in grouped order.
T2v=zeros(d^(2*k),bl2);
for j=1:bl2
  t2=PartialTrace(basis_k1{j}, k+1, d*ones(1,k+1));
  T2v(:,j)=t2(:);
end
Q1=orth(V1); G1=Q1'*V1; g1=Q1'*reshape(eye(Dsec),[],1);
Q2=orth(T2v); G2=Q2'*T2v; g2=Q2'*reshape(eye(dk),[],1);
TPb=kron(G1,G2)*NS; tpv=kron(g1,g2);
clear V1 V2 T2v Q1 Q2
fprintf("TP rows: %d (exact, full row rank)\n", size(TPb,1));
% programming family via fast factorized assembly + orth reduction
JC=zeros(d^2,d^2,s);
for c=1:s, JC(:,:,c)=RandomSuperoperator(d)/d; end
M1=cell(1,bl1); M2=cell(1,bl2);
for j=1:bl1
  R4=reshape(full(basis_1k{j}),[dk d dk d]);
  M1{j}=reshape(permute(R4,[2 4 1 3]), d*d, dk*dk);
end
for j=1:bl2
  R4=reshape(full(basis_k1{j}),[d dk d dk]);
  M2{j}=reshape(permute(R4,[1 3 2 4]), d*d, dk*dk);
end
gperm=[1:2:2*k-1, 2:2:2*k];
APR=zeros(2*d^4*s,m); BPR=zeros(2*d^4*s,1);
Pc=zeros(d^2,d^2,m);
for c=1:s
  temp=JC(:,:,c); for kk=1:k-1, temp=kron(temp,JC(:,:,c)); end
  Xt=temp.';
  Xg=PermuteSystems(Xt,gperm,d*ones(1,2*k));
  R4x=reshape(Xg,[dk dk dk dk]);
  Y=reshape(permute(R4x,[4 2 3 1]), dk^2, dk^2);
  for j1=1:bl1
    Z=M1{j1}*Y;
    for j2=1:bl2
      G=Z*M2{j2}.';
      R4g=reshape(G,[d d d d]);
      Pc(:,:,(j1-1)*bl2+j2)=reshape(permute(R4g,[3 1 4 2]), d^2, d^2);
    end
  end
  Mc=reshape(Pc,d^4,m); rh=d*reshape(JC(:,:,c),d^4,1);
  APR((c-1)*2*d^4+(1:d^4),:)=real(Mc); BPR((c-1)*2*d^4+(1:d^4))=real(rh);
  APR((c-1)*2*d^4+d^4+(1:d^4),:)=imag(Mc); BPR((c-1)*2*d^4+d^4+(1:d^4))=imag(rh);
end
APR=APR*NS; RowB=orth([APR BPR]')'; ARED=RowB(:,1:end-1); BRED=RowB(:,end);
clear APR BPR RowB
fprintf("prog rows: %d\n", size(ARED,1));
% vectorized PSD block maps
nbp=nb1*nb2; Rmat=cell(nbp,1); wsz=zeros(nbp,1);
for bi=1:nb1, for bj=1:nb2
  w=blocks1(bi).w*blocks2(bj).w; ip=(bi-1)*nb2+bj; wsz(ip)=w;
  RM=zeros(w*w,m);
  for j1=1:bl1, for j2=1:bl2
    kr=kron(red1{bi,j1},red2{bj,j2});
    RM(:,(j1-1)*bl2+j2)=kr(:);
  end, end
  Rmat{ip}=RM*NS;
end, end
yalmip('clear');
y1v = sdpvar(nn,1); y2v = sdpvar(nn,1); q1 = sdpvar(1); q2 = sdpvar(1);
F = [TPb*y1v == q1*tpv, TPb*y2v == q2*tpv, ARED*(y1v-y2v) == BRED];
for ip=1:nbp
  w=wsz(ip);
  Jb1=reshape(Rmat{ip}*y1v,w,w); Jb2=reshape(Rmat{ip}*y2v,w,w);
  F = [F, (Jb1+Jb1')/2 >= 0, (Jb2+Jb2')/2 >= 0];
end
opts = sdpsettings('solver','mosek','verbose',1);
sol = optimize(F, q1+q2, opts);
disp(sol.info);
b1 = NS*value(y1v); b2 = NS*value(y2v); p1 = value(q1); p2 = value(q2);
cvx_status = sol.info;
cost=p1+p2;
fprintf("SOLVE: gamma_%d(CPTP,%d) = %.12f  [%s]\n", k, d, cost, cvx_status);
% certificate on reconstructed full-space J
perm=zeros(1,2*k+2); perm(1)=1;
for i=1:k, perm(i+1)=2*i; perm(k+1+i)=2*i+1; end
perm(2*k+2)=2*k+2;
ipm=zeros(1,2*k+2); ipm(perm)=1:(2*k+2); perm=ipm;
dims_all=d*ones(1,2*k+2);
Jd1=zeros(D); Jd2=zeros(D);
for j1=1:bl1, for j2=1:bl2
  Bj=PermuteSystems(kron(sparse(basis_1k{j1}),sparse(basis_k1{j2})),perm,dims_all);
  idx=(j1-1)*bl2+j2;
  Jd1=Jd1+b1(idx)*full(Bj); Jd2=Jd2+b2(idx)*full(Bj);
end, end
herm1=norm(Jd1-Jd1','fro'); herm2=norm(Jd2-Jd2','fro');
e1=min(eig((Jd1+Jd1')/2)); e2=min(eig((Jd2+Jd2')/2));
dim_tp=d^(2*k+1);
tpr1=norm(PartialTrace(Jd1,2*k+2,dims_all)-p1*eye(dim_tp),'fro');
tpr2=norm(PartialTrace(Jd2,2*k+2,dims_all)-p2*eye(dim_tp),'fro');
rng(777); nf=50; fres=0;
for c=1:nf
  JCf=RandomSuperoperator(d)/d;
  temp=JCf; for kk=1:k-1, temp=kron(temp,JCf); end
  insf=Tensor(I_d, temp.', I_d);
  resf=norm(PartialTrace((Jd1-Jd2)*insf,2,[d,dk^2,d])-d*JCf,'fro');
  fres=max(fres,resf);
end
fprintf("CERT: herm %.2e/%.2e ; min eig %.3e/%.3e ; TP %.2e/%.2e ; fresh prog res (%d ch): %.3e\n", herm1, herm2, e1, e2, tpr1, tpr2, nf, fres);
save(fullfile(outputDir, sprintf("yalmip_d%d_k%d.mat",d,k)),"cost","d","k","s","b1","b2","p1","p2","cvx_status","e1","e2","fres","tpr1","tpr2");
fprintf("saved\n");

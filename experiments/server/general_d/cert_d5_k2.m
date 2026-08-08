scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(fileparts(scriptDir)));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();
up_setup(cfg, false);
outputDir = fullfile(cfg.resultsRoot, 'server', 'general_d', 'certificates');
if exist(outputDir, 'dir') ~= 7; mkdir(outputDir); end
d=5; k=2; s=500; n=k+1; Dsec=d^n; D=d^(2*k+2); dk=d^k; dim_tp=d^(2*k+1); I_d=eye(d);
rng(0);
fprintf("=== cert run: gamma_%d(CPTP, d=%d), D=%d ===\n", k, d, D);
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
m=bl1*bl2;
fprintf("bl1=%d bl2=%d m=%d\n", bl1, bl2, m);
blocks1=decompose_sector(basis_1k,d,k,'1k'); blocks2=decompose_sector(basis_k1,d,k,'k1');
nb1=length(blocks1); nb2=length(blocks2);
red1=cell(nb1,bl1); red2=cell(nb2,bl2);
for bi=1:nb1, G=blocks1(bi).G_sub; for j=1:bl1, red1{bi,j}=G'*basis_1k{j}*G; end, end
for bi=1:nb2, G=blocks2(bi).G_sub; for j=1:bl2, red2{bi,j}=G'*basis_k1{j}*G; end, end
fprintf("blocks: %dx%d pairs\n", nb1, nb2);
% Hermiticity involution
V1=zeros(Dsec^2,bl1); for jj=1:bl1, tmp=basis_1k{jj}; V1(:,jj)=tmp(:); end; V1i=pinv(V1);
A1=zeros(bl1); for jj=1:bl1, tt=transpose(basis_1k{jj}); A1(:,jj)=real(V1i*tt(:)); end
V2=zeros(Dsec^2,bl2); for jj=1:bl2, tmp=basis_k1{jj}; V2(:,jj)=tmp(:); end; V2i=pinv(V2);
A2=zeros(bl2); for jj=1:bl2, tt=transpose(basis_k1{jj}); A2(:,jj)=real(V2i*tt(:)); end
AhermC=kron(A1,A2)-eye(m); AhermC(abs(AhermC)<1e-9)=0; AHR=orth(AhermC')';
% full basis (sparse, gather-corrected perm)
perm=zeros(1,2*k+2); perm(1)=1;
for i=1:k, perm(i+1)=2*i; perm(k+1+i)=2*i+1; end
perm(2*k+2)=2*k+2;
ipm=zeros(1,2*k+2); ipm(perm)=1:(2*k+2); perm=ipm;
dims_all=d*ones(1,2*k+2);
B=cell(1,m);
for j1=1:bl1, for j2=1:bl2
  B{(j1-1)*bl2+j2}=PermuteSystems(kron(sparse(basis_1k{j1}),sparse(basis_k1{j2})),perm,dims_all);
end, end
fprintf("B built\n");
T=zeros(dim_tp,dim_tp,m);
for j=1:m, T(:,:,j)=full(PartialTrace(B{j},2*k+2,dims_all)); end
fprintf("T built\n");
% channels + fast P assembly
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
P=zeros(d^2,d^2,m,s);
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
      P(:,:,(j1-1)*bl2+j2,c)=reshape(permute(R4g,[3 1 4 2]), d^2, d^2);
    end
  end
end
fprintf("P built (fast)\n");
% reduced equality families
TPR = orth([reshape(T,[],m), -reshape(eye(dim_tp),[],1)]')';
APR=zeros(2*d^4*s,m); BPR=zeros(2*d^4*s,1);
for c=1:s
  Mc=reshape(P(:,:,:,c),d^4,m); rh=d*reshape(JC(:,:,c),d^4,1);
  APR((c-1)*2*d^4+(1:d^4),:)=real(Mc); BPR((c-1)*2*d^4+(1:d^4))=real(rh);
  APR((c-1)*2*d^4+d^4+(1:d^4),:)=imag(Mc); BPR((c-1)*2*d^4+d^4+(1:d^4))=imag(rh);
end
RowB=orth([APR BPR]')'; ARED=RowB(:,1:end-1); BRED=RowB(:,end);
clear APR BPR RowB V V1 V2;
fprintf("equalities reduced: TP %d rows, prog %d rows, herm %d rows\n", size(TPR,1), size(ARED,1), size(AHR,1));
cvx_begin sdp quiet
  cvx_solver mosek
  variable b1(m)
  variable b2(m)
  variable p1
  variable p2
  minimize(p1+p2)
  if ~isempty(AHR); AHR*b1 == 0; AHR*b2 == 0; end
  ARED*(b1-b2) == BRED;
  TPR*[b1;p1] == 0;
  TPR*[b2;p2] == 0;
  for bi=1:nb1, for bj=1:nb2
    J1b=0; J2b=0;
    for j1=1:bl1, for j2=1:bl2
      idx=(j1-1)*bl2+j2; R=kron(red1{bi,j1},red2{bj,j2});
      J1b=J1b+b1(idx)*R; J2b=J2b+b2(idx)*R;
    end, end
    (J1b+J1b')/2 >= 0; (J2b+J2b')/2 >= 0;
  end, end
cvx_end
cost=p1+p2;
fprintf("SOLVE: gamma_%d(CPTP,%d) = %.6f  [%s]\n", k, d, cost, cvx_status);
% ===== CERTIFICATION on reconstructed full-space J1, J2 =====
Jd1=zeros(D); Jd2=zeros(D);
for j=1:m, Jd1=Jd1+b1(j)*full(B{j}); Jd2=Jd2+b2(j)*full(B{j}); end
herm1=norm(Jd1-Jd1','fro'); herm2=norm(Jd2-Jd2','fro');
e1=min(eig((Jd1+Jd1')/2)); e2=min(eig((Jd2+Jd2')/2));
tpr1=norm(PartialTrace(Jd1,2*k+2,dims_all)-p1*eye(dim_tp),'fro');
tpr2=norm(PartialTrace(Jd2,2*k+2,dims_all)-p2*eye(dim_tp),'fro');
rng(777); nf=25; fres=0;
for c=1:nf
  JCf=RandomSuperoperator(d)/d;
  temp=JCf; for kk=1:k-1, temp=kron(temp,JCf); end
  insf=Tensor(I_d, temp.', I_d);
  resf=norm(PartialTrace((Jd1-Jd2)*insf,2,[d,dk^2,d])-d*JCf,'fro');
  fres=max(fres,resf);
end
fprintf("CERT: herm res %.2e / %.2e ; min eig %.3e / %.3e ; TP res %.2e / %.2e ; max fresh-channel prog res over %d channels: %.3e\n", herm1, herm2, e1, e2, tpr1, tpr2, nf, fres);
outputFile = fullfile(outputDir, 'cert_d5_k2.mat');
save(outputFile,"cost","d","k","s","b1","b2","p1","p2","cvx_status","e1","e2","herm1","herm2","tpr1","tpr2","fres");
fprintf("saved %s\n", outputFile);

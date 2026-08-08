scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(fileparts(fileparts(scriptDir))));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();
up_setup(cfg, false);
d=4; k=4; n=k+1; Dsec=d^n; D=d^(2*k+2); dk=d^k; I_d=eye(d);
fprintf("d=%d k=%d : D=%d Dsec=%d dk^2=%d\n", d,k,D,Dsec,dk^2);
t=tic;
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
fprintf("[%.0fs] bl1=%d bl2=%d m=%d\n", toc(t), bl1, bl2, m);
tb=tic; blocks1=decompose_sector(basis_1k,d,k,'1k'); blocks2=decompose_sector(basis_k1,d,k,'k1');
fprintf("[%.0fs] decompose done. w1=[%s] w2=[%s], max block %dx%d\n", toc(tb), num2str([blocks1.w]), num2str([blocks2.w]), max([blocks1.w])*max([blocks2.w]), max([blocks1.w])*max([blocks2.w]));
% Hermiticity SVD cost probe
th=tic;
V1=zeros(Dsec^2,bl1); for jj=1:bl1, tmp=basis_1k{jj}; V1(:,jj)=tmp(:); end; V1i=pinv(V1);
A1=zeros(bl1); for jj=1:bl1, tt=transpose(basis_1k{jj}); A1(:,jj)=real(V1i*tt(:)); end
V2=zeros(Dsec^2,bl2); for jj=1:bl2, tmp=basis_k1{jj}; V2(:,jj)=tmp(:); end; V2i=pinv(V2);
A2=zeros(bl2); for jj=1:bl2, tt=transpose(basis_k1{jj}); A2(:,jj)=real(V2i*tt(:)); end
AhermC=kron(A1,A2)-eye(m); AhermC(abs(AhermC)<1e-9)=0;
[~,Sv,Vv]=svd(AhermC); NS=Vv(:,diag(Sv)<1e-7); nn=size(NS,2);
fprintf("[%.0fs] Hermiticity svd(%dx%d) done. null dim nn=%d\n", toc(th), m, m, nn);
% one-channel Y formation + multiply timing
gperm=[1:2:2*k-1, 2:2:2*k];
M1=cell(1,bl1);
for j=1:bl1, R4=reshape(full(basis_1k{j}),[dk d dk d]); M1{j}=reshape(permute(R4,[2 4 1 3]), d*d, dk*dk); end
JC=RandomSuperoperator(d)/d; temp=JC; for kk=1:k-1, temp=kron(temp,JC); end
ty=tic; Xt=temp.'; Xg=PermuteSystems(Xt,gperm,d*ones(1,2*k)); R4x=reshape(Xg,[dk dk dk dk]); Y=reshape(permute(R4x,[4 2 3 1]),dk^2,dk^2); tY=toc(ty);
yinfo=whos('Y');
tm=tic; for j1=1:bl1, Z=M1{j1}*Y; end; tMult=toc(tm);
fprintf("ONE CHANNEL: form Y %.1fs (Y=%.1f GB), all M1*Y %.1fs -> per-channel ~%.1fs\n", tY, yinfo.bytes/1e9, tMult, tY+tMult);
fprintf("PROJECTED assembly: s=160 -> %.1f h ; s=300 -> %.1f h\n", 160*(tY+tMult)/3600, 300*(tY+tMult)/3600);
mem=memory;

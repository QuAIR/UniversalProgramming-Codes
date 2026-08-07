scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(fileparts(scriptDir)));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();
up_setup(cfg, false);
for cfg = [2 2; 2 3]'
  d=cfg(1); k=cfg(2); n=k+1; Dsec=d^n; dk=d^k; I_d=eye(d);
  rng(0);
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
  % fixed perm (scatter->gather inversion)
  perm=zeros(1,2*k+2); perm(1)=1;
  for i=1:k, perm(i+1)=2*i; perm(k+1+i)=2*i+1; end
  perm(2*k+2)=2*k+2;
  ipm=zeros(1,2*k+2); ipm(perm)=1:(2*k+2); perm=ipm;
  dims_all=d*ones(1,2*k+2);
  B=cell(1,m);
  for j1=1:bl1, for j2=1:bl2
    B{(j1-1)*bl2+j2}=PermuteSystems(kron(sparse(basis_1k{j1}),sparse(basis_k1{j2})),perm,dims_all);
  end, end
  % M1/M2 sector matrices
  M1=cell(1,bl1); M2=cell(1,bl2);
  for j=1:bl1
    R4=reshape(full(basis_1k{j}),[dk d dk d]);          % (a, s, a', t)
    M1{j}=reshape(permute(R4,[2 4 1 3]), d*d, dk*dk);    % rows (s,t) s fast; cols (a,a') a fast
  end
  for j=1:bl2
    R4=reshape(full(basis_k1{j}),[d dk d dk]);           % (s', b, t', b')
    M2{j}=reshape(permute(R4,[1 3 2 4]), d*d, dk*dk);    % rows (s',t') s' fast; cols (b,b') b fast
  end
  gperm=[1:2:2*k-1, 2:2:2*k];
  s_test=3; maxdiff=0;
  for c=1:s_test
    JC=RandomSuperoperator(d)/d;
    temp=JC; for kk=1:k-1, temp=kron(temp,JC); end
    Xt=temp.';
    Xg=PermuteSystems(Xt,gperm,d*ones(1,2*k));
    R4x=reshape(Xg,[dk dk dk dk]);                       % (b', a', b, a)
    Y=reshape(permute(R4x,[4 2 3 1]), dk^2, dk^2);       % rows (a,a') a fast; cols (b,b') b fast
    ins=Tensor(I_d, Xt, I_d);
    for j1=1:bl1
      Z=M1{j1}*Y;
      for j2=1:bl2
        idx=(j1-1)*bl2+j2;
        Pslow=full(PartialTrace(B{idx}*ins,2,[d,dk^2,d]));
        G=Z*M2{j2}.';
        R4g=reshape(G,[d d d d]);                        % (s, t, s', t')
        Pfast=reshape(permute(R4g,[3 1 4 2]), d^2, d^2); % rows (s',s) s' fast = code layout
        maxdiff=max(maxdiff, max(abs(Pslow(:)-Pfast(:))));
      end
    end
  end
  fprintf("d=%d k=%d: max |Pslow - Pfast| over all %d basis x %d channels = %.3e\n", d, k, m, s_test, maxdiff);
end

files = {"results/gamma_d2_k2_s500_r7.mat","results/gamma_d2_k2_fix.mat","results/gamma_d2_k2.mat","results/gamma_d3_k2_fix.mat"};
for f = files
  S = load(f{1});
  fprintf("%-38s cost=%.16f\n", f{1}, S.cost);
end

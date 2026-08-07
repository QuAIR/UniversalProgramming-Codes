files = {"results/gamma_d2_k1_s500_r0.mat","results/gamma_d3_k1_s500_r0.mat","results/gamma_d2_k2_s500_r0.mat","results/gamma_d3_k2_s500_r0.mat","results/gamma_d3_k2_s800_r1.mat","results/cert_d2_k3.mat","results/cert_d2_k4.mat","results/gamma_d2_k3_s500_r0.mat","results/gamma_d2_k4_s500_r0.mat","results/brute_d2_k1_s500_r0.mat"};
for f = files
  S = load(f{1});
  fprintf("%-38s d=%d k=%d cost=%.14f\n", f{1}, S.d, S.k, S.cost);
end

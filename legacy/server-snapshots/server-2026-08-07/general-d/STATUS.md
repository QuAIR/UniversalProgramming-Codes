# general-d run status (recall manifest)
Updated 2026-06-13.

DONE/CERTIFIED: gamma_k(CPTP,2) k=1..5; gamma_2(CPTP,d) d=2..5;
  gamma_k(CPTP,3) k=1,2,3 (k=4=3.6196 solved, not cert-grade, D=59049 too big).
  d=4: k=1=29.125, k=2=14.366215273519 (reduced-cert clean).

RUNNING (setsid-detached, survives disconnect):
- struct3_d4k3 : gamma_3(CPTP,4). D=65536 but solve is in REDUCED space (struct3
                 uses reduced-space certificate, never forms D x D). Log
                 logs/struct3_d4k3.log; result results/struct3_d4_k3.mat.

Recall: grep -h "SOLVE\|CERT" logs/struct3_d4k3.log ; ls results/struct3_d4_k3.mat
Reduced cert metrics: min eig (PSD), nonherm, TP res, fresh-channel programming.
NOTE d=4 k=4: D=4^10~1e6, per-channel Y=65536^2=34GB -> programming assembly
intractable without a streaming/tensor-contraction rewrite. Deferred.

RUNNING (2026-06-13): y3_d4k4 = gamma_4(CPTP,4), D=4^10=1048576.
  Engine: YALMIP+MOSEK, null-space, reduced-space cert. s=128, nf=12.
  Assembly ~4.4h (per-channel 125s, Y=68.7GB complex, mem cleared each iter ~140GB peak),
  then MOSEK solve ~3-4h. Log logs/y3_d4k4.log; result results/y3_d4_k4.mat.
  Gate passed: gamma_y3 reproduced gamma_3(CPTP,4)=9.453845 (cert clean).

RUNNING (2026-06-14): y3_d5k3 = gamma_3(CPTP,5), D=5^8=390625. YALMIP+MOSEK,
  reduced cert, s=256, Y=3.9GB/channel. Log logs/y3_d5k3.log; result results/y3_d5_k3.mat.
  Gate: gamma_y3 reproduced gamma_2(CPTP,5)=23.324402 (cert clean).
DEFERRED: d=5 k=4 -- per-channel Y = 5^16*16B = 2.44 TB >> 440 GB RAM. The
  M1*Y*M2 assembly cannot materialise Y. Needs combinatorial Brauer-diagram
  contraction (d^2 x d^2 per copy, never forming d^(4k)). Solve itself would be
  feasible (m<=14400 like d=4,k=4); only the programming assembly is blocked.

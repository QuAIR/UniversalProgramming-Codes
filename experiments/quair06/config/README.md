# Portable quair06 configuration

The experiment definitions use `up_config` from `src/matlab` rather than
machine-specific paths. Configure optional dependencies with these environment
variables before starting MATLAB:

| Variable | Purpose | Default |
| --- | --- | --- |
| `UP_CVX_ROOT` | CVX installation directory | empty |
| `UP_QETLAB_ROOT` | QETLAB installation directory | empty |
| `UP_YALMIP_ROOT` | YALMIP installation directory | empty |
| `UP_MATLAB_BIN` | MATLAB executable for shell wrappers | `matlab` |
| `UP_SDP_SOLVER` | CVX solver name | `sdpt3` |
| `UP_RESULTS_ROOT` | Generated-output root | `results/generated` under the repository |

`test_paths.m` deliberately checks only portable source resolution. It does
not call `up_setup`, because a dependency-free machine must be able to verify
the repository layout without pretending that CVX, QETLAB, or an SDP solver is
available. Solver-backed tests fail normally with the dependency-specific
`up_setup` error when those dependencies are not configured.

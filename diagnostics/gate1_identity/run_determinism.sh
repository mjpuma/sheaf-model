#!/bin/zsh
# Sequential t_max=2 determinism runs. Refuses to start if git is dirty.
set -euo pipefail
ROOT=/Users/mjp38/GitHub/sheaf-model
JULIA=/Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia
cd "$ROOT"
if [ -n "$(git status --porcelain)" ]; then
  echo "refusing to run: git status is dirty" >&2
  git status --porcelain >&2
  exit 1
fi
launch() {
  echo "=== $* $(date) ==="
  if [ "$(uname -m)" = "arm64" ]; then
    arch -x86_64 "$JULIA" --project="$ROOT/agrimate_julia" \
      "$ROOT/diagnostics/gate1_identity/determinism_t2.jl" "$@"
  else
    "$JULIA" --project="$ROOT/agrimate_julia" \
      "$ROOT/diagnostics/gate1_identity/determinism_t2.jl" "$@"
  fi
}
launch cold maize cold1
launch cold maize cold2
launch after maize after1
launch coupled maize coupled1
launch cold rice rice_cold
echo "=== compare $(date) ==="
python3 "$ROOT/diagnostics/gate1_identity/compare_determinism.py" \
  "$ROOT/agrimate_julia/data_g1prep_identity/determinism" \
  cold1 cold2 maize \
  cold1 after1 maize \
  cold1 coupled1 maize \
  rice_cold coupled1 rice
echo "=== DONE $(date) ==="

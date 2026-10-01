# J0b — Load AgrimateModel

Loaded. `simulate()` was not called.

## Command

From `/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/`:

```bash
arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia --project=. -e 'using Pkg; Pkg.develop(path="src/AgrimateModel")'
```

Exit code 0. About 49 seconds. `Pkg.resolve()` and `Pkg.update()` were not typed. `Pkg.develop` itself printed `Resolving package versions...` and upgraded many registry packages (JuMP, NLopt, COSMO, and a long list of jlls). The paper `Manifest.toml` is no longer a bit-for-bit pin of the Zenodo archive.

`Manifest.toml` path line is now:

```text
path = "src/AgrimateModel"
```

was:

```text
path = "/home/kikuhla/research/code/agrimate/src/AgrimateModel"
```

AgrimateModel uuid and version are unchanged: `4da19ca3-7b67-453c-a8f9-78404829864f`, `0.1.0`.

## Load

```bash
arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia --project=. -e 'using AgrimateModel; println(pathof(AgrimateModel))'
```

Exit code 0. About 157 seconds (first precompile). Printed:

```text
/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/src/AgrimateModel/src/AgrimateModel.jl
```

That is the unpacked local source. No error. Julia source was not edited.

# G1-prep maize: `t_max=0` (2026-10-08)

Public-data CSVs (`inputs/from_data.py --crop maize`). Every Agrimate
region has positive maize production, so the rice 0/0 path was not
taken.

```
python drivers/run.py --crop maize --anomalies --restrictions --t-max 0
```

Nash in 393 iterations, `maize_exit=0`. NetCDF:
`agrimate_julia/data_g1prep_maize/netcdf/`.

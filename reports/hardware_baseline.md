# Hardware baseline: observed host, 12 November 2026

Measurement: **16:30:55 Africa/Nairobi** (`2026-11-12T13:30:55.317Z`).
Machine-readable observation: `hardware_baseline.json`.

| Item | Observed result |
|---|---|
| CPU | Intel Core i5-13420H |
| OS-visible physical RAM | 8,201,113,600 bytes (about 7.64 GiB) |
| Free RAM at measurement | 357,158,912 bytes (about 341 MiB) |
| GPU | NVIDIA GeForce RTX 3050 6GB Laptop GPU |
| GPU total/free | 6144 / 5957 MiB, per nvidia-smi |
| NVIDIA driver | 621.14 |
| Python used for checks | 3.14.7 |
| Node | v26.8.1 |

The observed GPU is the RTX 3050 6 GB named in the project plan. This session
has not independently confirmed that the exposed machine is Athena; do not
overwrite the planned hardware identity or make model-capacity claims from this
result.

`Get-CimInstance` could not access CIM resources. Memory was instead read using
Node's `os.totalmem()` and `os.freemem()`; these are system values, not model peak
usage. Free RAM is a momentary reading and is too low to justify loading a model.

`http://127.0.0.1:1234/v1/models` was inaccessible under socket permissions.
`lms ls --json` failed to connect/find a valid running installation. This proves
runtime access is unavailable in this session, not that the user has no models.
No model/license/profile has been selected, and this session loaded no model.

The default `python`, `python3` and `py` aliases were inaccessible. An existing
`Q:\rag_env` points to a missing interpreter and was not modified. The working
interpreter used was:

```text
C:\Users\wisdo\AppData\Local\Python\pythoncore-3.14-64\python.exe
```

All admission tests use the standard library only. No heavy packages, weights,
services or paid providers were installed or enabled.

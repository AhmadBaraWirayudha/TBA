# RobustOpt FreeCAD Workbench — Maintainer Handover

**Status date:** 2026-07-13  
**Targeted environment (not yet certified):** Windows 10/11, FreeCAD 0.21 or later

## Scope and status

RobustOpt is packaged for manual installation as a FreeCAD Python workbench and contains a three-stage optimization pipeline. Successful loading and FEM execution remain uncertified until tested in the target environment:

1. L9/L27 Taguchi screening with repeated additive noise and S/N ranking.
2. Gaussian-process Bayesian optimization through `scikit-optimize`, with a bounded random-search contingency when `skopt` cannot be imported.
3. Optional single-parameter PID adjustment against the same selected scalar response.

The GUI uses PySide2 and delegates optimization orchestration to a `QThread`. Each FEM evaluation runs in a native `freecadcmd.exe` subprocess using temporary JSON. The final result is applied through a cross-thread Qt signal on the GUI thread.

This is a **code-complete candidate**, not a claim of universal FEM compatibility. Pure-Python engine tests pass. End-to-end behavior must be validated against the user's exact FreeCAD release, CalculiX installation, analysis object layout, and result properties.

## Delivered files

The archive includes `README.md`, `TUTORIAL.md`, `ADDENDUM.md`, `TESTED_ENVIRONMENTS.md`, source modules, icons, metadata, dependency files, and `tests/test_engine.py`. `TESTED_ENVIRONMENTS.md` currently records that no end-to-end FreeCAD/CalculiX environment is certified.

It intentionally does **not** include:

* `cantilever.FCStd` — users prepare and validate their own FEM model.
* `RobustOpt_config.json` — this implementation uses the live dialog and does not persist that legacy configuration format.
* `RobustOpt_Advanced_Guide.md` — advanced implementation decisions are recorded in `ADDENDUM.md`.

No document in this package should instruct maintainers to depend on those absent files.

## Known risks and limitations

### FEM integration — high risk, version-sensitive

`eval_script.py` uses `femtools.ccxtools.FemToolsCcx`. FreeCAD FEM APIs and result-property names can vary between releases and model setups. The evaluator supports an explicitly selected numeric result object/property and scans a few common properties as a fallback, but it does not guarantee automatic extraction of mass, stress, and displacement for every model. Run the analysis manually first and regression-test each supported FreeCAD version.

Detected evaluator failures (exceptions, timeouts, missing JSON, or explicit error results) receive a large penalty and the search continues. CalculiX convergence is not independently classified if the FreeCAD API returns without raising. This is fault tolerance, not proof that failed designs are physically infeasible.

Spreadsheet writes support an optional per-factor unit suffix. Literal quantity cells can be auto-detected, but formula-driven cells may require manual unit entry. Unit conversion and correctness are not inferred; validate each factor against the model before engineering use.

### MCMC — optional and experimental

MCMC mode adds `emcee`, scikit-learn/SciPy behavior, posterior sampling cost, and a random candidate acquisition search. It is expected to add the highest surrogate-computation overhead and is the least field-validated path; no comparative benchmark is bundled. It is disabled by default and installed separately with `requirements-mcmc.txt`. Use standard GP mode first. Validate convergence and reproducibility before relying on MCMC results.

### Optimization scope

The workbench minimizes one scalar objective. Explicit multi-objective optimization and a general constraint editor are not implemented. Constraints can be encoded in a model-derived penalized scalar. PID tunes one selected control factor and assumes the user chooses gain signs appropriate to the response direction.

### Cancellation

Cancellation is cooperative between evaluations. It does not forcibly terminate an active CalculiX subprocess.

## Dependency contingencies

* Standard installation: run FreeCAD's bundled Python, for example `"C:\\Program Files\\FreeCAD 0.21\\bin\\python.exe" -m pip install -r requirements.txt`.
* Experimental MCMC: use the same FreeCAD Python with `-m pip install -r requirements-mcmc.txt`.
* If `skopt` cannot be imported in standard mode, the engine logs the issue and performs bounded uniform random search for the configured iteration count.
* If `emcee` is absent while MCMC is selected, that mode fails clearly; it does not silently downgrade, preventing accidental misrepresentation of the algorithm used.

## Verification performed

The included pure-Python tests verify L9 dimensions and per-column balance, L27 dimensions and pairwise level balance, S/N calculations, unit-string formatting, evaluator-error logging, deterministic Taguchi and PID behavior, the random-search contingency, and the standard-GP/MCMC branch contracts with mocked optimizer modules. The branch-contract tests do not validate real `scikit-optimize` or `emcee` numerical behavior. No test exercises FreeCAD, CalculiX, Windows Registry discovery, subprocess behavior, or real FEM result extraction.

Recommended acceptance test:

1. Install in a disposable FreeCAD profile.
2. Validate a small FEM model manually.
3. Copy `examples/eval_request.example.json`, replace every model-specific value, then run `"C:\\Program Files\\FreeCAD 0.21\\bin\\freecadcmd.exe" "%APPDATA%\\FreeCAD\\Mod\\RobustOpt\\eval_script.py" path\\to\\request.json`. Verify the final JSON objective against the GUI result.
4. Run a reduced pipeline with a coarse mesh.
5. Confirm cancellation, penalties, model update, units, and saved-document behavior.
6. Repeat for every FreeCAD release claimed as supported.

## Runtime estimates and assumptions

No benchmark measurements are bundled. Runtime is approximately:

`Taguchi rows × noise repeats × average FEM solve time`

plus

`(Bayesian iterations + 1 start-point evaluation) × average FEM solve time`

plus

`(PID adjustment evaluations + 1 initial evaluation) × average FEM solve time`.

For example, L9 with three repeats means 27 FEM solves before Bayesian or PID work. MCMC adds surrogate-computation overhead that depends on observations, walkers, chain steps, candidate count, CPU, and dependency versions. Any minute/hour figures are planning estimates only, not runtime guarantees. Benchmark the actual model and machine.

## Maintainer priorities

1. Add Windows/FreeCAD integration tests and a redistributable, license-compatible example model if desired.
2. Pin dependency versions per supported FreeCAD Python version.
3. Add structured evaluation history export and richer solver diagnostics.
4. Add explicit constraint configuration before claiming general constrained optimization.
5. Treat Addon Manager publication as future work until repository metadata and release hosting are real.

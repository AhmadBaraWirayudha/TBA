# RobustOpt handover audit

**Audit date:** 2026-07-13  
**Scope:** the supplied handover (`deepseek_markdown_20260713_5f1dcc.md`) checked against the current `RobustOpt.zip` source tree. This is a static code/document review; FreeCAD and CalculiX were not available for an end-to-end execution test.

## Executive finding

The archive is a credible **prototype / code-complete integration candidate**. Its pure-Python optimization core, Windows subprocess wrapper, Qt worker structure, documentation, and tests are real. It is **not yet release-validated as a production FreeCAD FEM workbench**. The highest risks are the version-sensitive CalculiX API sequence, result extraction, unit handling, optional MCMC path, and missing FreeCAD-level integration tests.

## 1. Confirmed strengths

| Handover claim | Finding |
|---|---|
| “Architected a modular workbench: `InitGui.py`, `Commands.py`, `TaskPanel.py`, `OptimizationEngine.py`, `Evaluator.py`, plus a standalone `eval_script.py`” | **Confirmed.** All named modules are present, along with `MCMCBayesianOptimizer.py`, metadata, icons, and documentation. |
| “Taguchi: orthogonal arrays (L9, L27)” | **Confirmed in code.** L9 is a 9-run, four-column, three-level array. L27 is generated from three base columns and five linear combinations. The included tests check L9 balance and array lengths, though not full pairwise orthogonality of every L27 column. |
| “optional MCMC surrogate using `emcee` to sample GP hyperparameters and compute Expected Improvement” | **Substantially confirmed, but experimental.** `MCMCBayesianOptimizer.py` samples log length scale, signal variance, and noise variance, then averages EI across posterior samples. It is not merely a placeholder. |
| “PID: closed-loop controller that varies one parameter” | **Confirmed.** The selected factor is bounded and updated with configurable Kp/Ki/Kd. The response is the same scalar objective selected for the pipeline. |
| “locating `freecadcmd.exe` via registry” | **Confirmed.** `Evaluator.py` checks configured path, PATH, Windows registry locations, and `FreeCAD.getHomePath()`. |
| “passing parameters through temporary JSON files” | **Confirmed.** Input is written to a temporary JSON file and final JSON-looking stdout is parsed. Cleanup occurs in `finally`. |
| “GUI with configuration dialog, progress logging, progress bar, cancellation, and auto-apply” | **Confirmed with qualifications.** These controls exist. Cancellation is cooperative only, and auto-apply has document/unit edge cases described below. |
| “QThread” and headless subprocess evaluation | **Confirmed structurally.** `Worker` subclasses `QThread`; optimization and blocking subprocess calls execute in `run()`. Qt signals report progress and results. |
| Failure penalty and continuation | **Confirmed.** Evaluator exceptions return objective `1e30`, allowing later evaluations to continue. |
| Random-search contingency if `skopt` is absent | **Confirmed in the current archive.** Standard Bayesian mode now logs the fallback and performs bounded uniform random search. This was absent in the earlier build described by the original audit. |
| Pure-Python tests pass | **Confirmed from the included test suite and build run.** Three tests cover array shape/balance, S/N ordering, and fake-evaluator Taguchi selection. They do not test FreeCAD or FEM. |

## 2. Risks and gaps

### Critical / high

1. **No end-to-end FreeCAD/CalculiX validation is supplied.** The tests never import FreeCAD, launch `freecadcmd.exe`, run CalculiX, extract a result, or update a real Spreadsheet. Passing three pure-Python tests does not establish workbench operability.

2. **The FEM runner is version-sensitive.** `eval_script.py` calls `femtools.ccxtools.FemToolsCcx` methods in a fixed sequence: `setup_working_dir`, `setup_ccx`, `check_prerequisites`, `purge_results`, `write_inp_file`, `ccx_run`, and `load_results`. Method availability, signatures, prerequisite semantics, solver object discovery, and load behavior may differ among FreeCAD 0.21, 0.22, 1.x, and packaged builds. `check_prerequisites()` is called but its return value is not examined.

3. **Result extraction is not general.** The reliable path requires the user to name an object and numeric property. The fallback searches a small set of names and assumes scalar/list values convertible to `float`. It does not robustly derive von Mises stress, displacement, or mass across FreeCAD result representations.

4. **Unit handling can invalidate models.** The evaluator writes `str(number)` to aliases. A cell originally containing `150 mm` can become unitless. `load_aliases()` converts a `Quantity` to its base scalar value but does not retain the unit for bounds or later writes. Dimensioned expressions may reject or misinterpret these values.

5. **No general constraint implementation exists.** The optimizer minimizes one scalar. There is no constraint UI, no probability-of-feasibility model, and no built-in stress/deflection penalty. Users can only expose a pre-penalized scalar in their model.

6. **MCMC is dependency-heavy and insufficiently validated.** It requires `emcee`, NumPy, SciPy, and scikit-learn behavior compatible with FreeCAD's bundled Python. It repeatedly fits many GPs and samples a finite random candidate pool. There are no tests for posterior sampling, EI correctness, numerical singularities, constant objectives, or Windows wheels.

### Medium

7. **Cancellation does not cancel the active solve.** `Worker.cancel()` sets a flag checked before the next evaluation. A long-running `subprocess.run()` continues until completion or timeout (default 3600 seconds). “Cancellation” must not be interpreted as immediate process termination.

8. **Auto-apply is only conditionally safe.** Cross-thread signals normally queue the `done()` slot onto the dialog's GUI thread, which is the correct Qt pattern. However, the code applies results to whatever `App.ActiveDocument` exists at completion, not necessarily the optimized document. Closing or switching documents during a run can update the wrong target or fail.

9. **Repeated result objects are mishandled.** Each run calls `addObject("App::FeaturePython", "RobustOptResult")`; on later runs FreeCAD may create `RobustOptResult001`, but the code then writes to `getObject("RobustOptResult")`. This can leave extra objects and update the old object instead of the newly created one.

10. **Nominal-is-best S/N is nonstandard and incompletely configured.** The implementation computes `10 log10(mean²/variance) - abs(mean-target)`. The subtraction mixes dB with response units, and the dialog does not provide the Taguchi target to `cfg`, so the target defaults to zero. This mode should be corrected or labeled experimental.

11. **Noise modeling differs from the narrative.** Noise is Gaussian additive perturbation applied to every listed control factor using its row's sigma. There is no separate noise-factor mapping, distribution selector, or explicit 90/100/110 N set. Bounds are not enforced after noise perturbation.

12. **Dependency management is basic.** `DependencyCheck.py` has an install function but no dialog that offers installation. Base startup warns about core packages only. Selecting MCMC without `emcee` produces a worker failure rather than a preflight warning. `pyDOE2` is listed but the hardcoded arrays do not use it.

13. **Fallback nomenclature is misleading.** When `skopt` is absent, the “Bayesian” stage becomes random search. This is a useful contingency, but logs/results should record the actual algorithm so users cannot mistake it for GP optimization.

14. **PID robustness is limited.** There is no anti-windup, output-rate limit, response monotonicity check, automatic gain direction, or filtering. A failed FEM evaluation becomes `1e30`, which can create an enormous PID error and saturate the parameter bound.

15. **Subprocess protocol is pragmatic, not collision-proof.** Parsing the final line beginning with `{` tolerates banners, but any unrelated FreeCAD output that begins with JSON syntax could be mistaken for the result. There is no protocol marker or result-file fallback.

### Packaging / distribution

16. **Addon Manager readiness is unconfirmed.** `package.xml` has no real repository URL and has not been demonstrated against metadata validation or the Addon Manager. Manual installation is supported in documentation; public Addon Manager distribution is not established.

17. **Compatibility is asserted, not demonstrated.** There is no CI matrix, pinned dependency lock, or recorded test on FreeCAD 0.21+. The package cannot presently substantiate broad “FreeCAD ≥0.21” compatibility.

18. **Icons are placeholders.** Four stage-named SVG files are copies of the same icon, and only the single run command is registered. This is cosmetic but inconsistent with documents that imply four dedicated command buttons.

## 3. Unsupported or overstated claims

The following quotations are from the supplied handover.

### “A fully functional, installable FreeCAD workbench”

**Unsupported as written.** It is installable in structure and code-complete, but no packaged evidence demonstrates a successful FreeCAD GUI load, CalculiX run, result extraction, or model update. Replace “fully functional” with “code-complete prototype requiring validation against the target FreeCAD/CalculiX installation.”

### “One-click robust screening, global Bayesian search, and PID fine-tuning.”

**Overstated.** One Run button launches the configured pipeline, but setup requires a saved and manually validated FEM document, exact aliases, factor bounds, analysis/result selection, dependencies, and optional executable configuration. Bayesian search is skipped in favor of random search if `skopt` is unavailable, and PID can be disabled. Use “single-run pipeline after model preparation and configuration.”

### “Real FEM extraction (von Mises stress, displacement, mass) via CalculiX.”

**Unsupported/generalized beyond the code.** The evaluator returns one selected numeric property and has a narrow common-property scan. It does not reliably calculate all three metrics, and it contains no general mass calculation. Replace with “executes an existing CalculiX analysis and reads a user-selected numeric result property, subject to FreeCAD version/model conventions.”

### “Bayesian: `scikit-optimize`'s `gp_minimize` with constraint handling”

**Incorrect in two respects.** The code uses the lower-level `skopt.Optimizer`, not `gp_minimize`, and implements no general constraints. Replace with “sequential `skopt.Optimizer` GP search over box bounds; constraints must be encoded into the scalar objective.”

### “Thread-safe execution and automatic model update.”

**Partially supported, too absolute.** Worker/UI communication follows the appropriate signal pattern, and model update occurs in the receiver slot. It is not proven thread-safe across FreeCAD versions, and active-document switching can target the wrong document. Replace with “optimization runs in a QThread and reports via Qt signals; final GUI-document update is signal-driven and requires integration testing.”

### “Works only on Windows ... requires FreeCAD ≥0.21”

**Target constraint, not verified compatibility.** Windows executable discovery is implemented, but no test matrix proves every FreeCAD release from 0.21 onward. Say “targets Windows 10/11 and FreeCAD 0.21+; exact FEM API compatibility must be tested per release.”

### “Distribution via manual folder copy or FreeCAD Addon Manager.”

**Only manual distribution is currently supported by evidence.** There is no published repository/release URL or Addon Manager acceptance evidence. Replace with “manual installation package; Addon Manager publication is future work.”

### “MCMC sampling can be slow (mitigated by adjustable chain length and walker count).”

**Incomplete.** Chain length/walker count are constructor parameters in code but are not exposed in the GUI. Ordinary users must edit source. Replace “adjustable” with “source-configurable,” or add controls.

### “PID ... until a target metric (deflection, stress) is met.”

**Overgeneralized.** There is no metric selector specific to PID. PID uses the pipeline's one selected scalar objective property. Replace with “until the selected scalar response approaches its target.”

### “Only one analysis object per document supported.”

**Misphrased.** The dialog can select one analysis for a run; the document may contain multiple analyses. Replace with “one analysis object is selected per optimization run.”

### “Open the sample `cantilever.FCStd` model”

**Referenced-but-absent.** No such file exists. Remove this instruction or add a tested, redistributable sample with documented FreeCAD version and license.

### “review ... `RobustOpt_Advanced_Guide.md`”

**Referenced-but-absent.** Remove or redirect to `ADDENDUM.md` and `TUTORIAL.md`.

### “backward compatibility with existing configuration files (`RobustOpt_config.json`...)”

**Unsupported.** The current dialog does not read or write that file. Remove the claim or implement/version a persistent configuration schema.

### Runtime claims such as “Taguchi (9 runs) ~2 minutes” and “MCMC ... ~30 minutes”

**Unverified planning assumptions.** Taguchi with nine rows and three noise repeats actually invokes 27 FEM solves. Runtime depends on mesh, solver, hardware, failures, timeout, and MCMC settings. Use formulas and label any example as hypothetical, not measured or guaranteed.

## 4. Missing, placeholder, or absent material

* Absent but referenced by the supplied handover: `cantilever.FCStd`, `RobustOpt_Advanced_Guide.md`, and `RobustOpt_config.json`.
* No end-to-end test fixture, solver output fixture, FRD parser test, Windows test log, screenshots, dependency lock file, changelog, or release notes.
* No real repository URL in `package.xml`; therefore Addon Manager distribution is not configured.
* SVGs are simple placeholders/copies.
* There is no explicit constraint editor, evaluation-history export, persistent configuration file, dedicated stage commands, multi-objective implementation, or surrogate viewer.
* `pymc` is mentioned in historical/source notes but is not used by the implementation. The current split requirements correctly keep MCMC optional through `requirements-mcmc.txt`.

## 5. Recommended document corrections

1. Use the status phrase: **“Code-complete prototype; pure-Python core tested; FreeCAD/CalculiX integration requires target-environment validation.”**
2. Replace all `gp_minimize` references with `skopt.Optimizer` and remove “constraint handling” unless a constraint/penalty interface is implemented.
3. Describe the FEM output accurately as one user-selected scalar result property; do not promise mass, stress, and displacement extraction generally.
4. Replace “one-click” with “single-run pipeline after configuration and manual FEM validation.”
5. Qualify “thread-safe” as a design approach, not a verified guarantee; mention cooperative cancellation and active-document risk.
6. Mark MCMC **optional, experimental, source-tuned, and not part of base requirements**.
7. Replace broad compatibility claims with a target/support matrix once real versions are tested.
8. Remove Addon Manager claims until a real repository, valid metadata, release tag, and acceptance test exist.
9. Remove absent-file references or add the files. Do not imply compatibility with a configuration format the code never reads.
10. Replace minute estimates with the evaluation-count formula and explicitly identify assumptions.
11. Document the random-search fallback as a change in algorithm, not equivalent Bayesian behavior.
12. Add a unit-handling limitation and require users to validate dimensioned spreadsheet cells.
13. Correct nominal-is-best wording or fix its formula/UI target before presenting it as standard Taguchi behavior.
14. State that one analysis is selected per run, not that a document can contain only one analysis.

## 6. Final verdict on release readiness

### Manual alpha / engineering prototype: **Conditionally ready**

Suitable for a technically capable maintainer to install manually in a controlled Windows/FreeCAD environment, inspect logs, and test on noncritical models. The architecture is coherent enough for further development.

### Public beta: **Not ready**

Before beta, complete at least one reproducible end-to-end Windows test; correct unit preservation and nominal S/N behavior; harden result extraction; fix repeated result-object handling; preflight MCMC dependencies; and document actual tested FreeCAD/CalculiX versions.

### Production engineering use / Addon Manager release: **Not ready**

Production readiness requires a supported-version matrix, real integration tests, representative sample model or fixtures, dependency pinning, validated solver/result APIs, stronger configuration/constraint handling, release metadata, and clear safety/verification guidance. Optimization results must be independently verified with a refined FEM model before engineering use.

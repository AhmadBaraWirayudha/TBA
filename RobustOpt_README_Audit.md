# RobustOpt audit continuation — `README.md`

**Document reviewed:** `RobustOpt/README.md` from the current archive  
**Comparison basis:** current source, package structure, dependency files, and prior handover/addendum findings. Static review only; no FreeCAD or CalculiX execution was performed.

## 1. Confirmed support

### “RobustOpt drives an **existing, saved, spreadsheet-parametric FEM model**”

**Supported.** `TaskPanel.py` requires an existing `.FCStd` path, `SubprocessEvaluator` passes that path to `eval_script.py`, and the subprocess opens it with `App.openDocument()`. The workbench does not create a FEM analysis, which matches the statement.

### “Every FEM solve runs in a fresh native Windows `freecadcmd.exe` process”

**Supported structurally.** Every `SubprocessEvaluator.evaluate()` call executes a new `subprocess.run([freecadcmd, eval_script.py, request.json])`. This creates one process per evaluation. “Native Windows” accurately describes the target executable and process flags, although successful execution has not been demonstrated in a Windows integration test.

### “the GUI orchestration runs in a `QThread`”

**Supported.** `Worker` subclasses `QtCore.QThread`, and its `run()` method executes `Pipeline.run()`. Progress, result, and failure communication uses Qt signals.

### Architecture claims: “Taguchi L9/L27 + noise S/N”, “PID fine tuner”, “temporary JSON”, and “JSON objective or penalty”

**Supported with qualifications discussed below.** Those components and data paths exist. The diagram is accurate for the ordinary successful path but omits random-search fallback and the separate MCMC acquisition path.

### “Standard GP mode uses `requirements.txt`. Experimental MCMC mode additionally requires `emcee`; install it with `requirements-mcmc.txt`. PyMC is not required.”

**Supported.** Both requirement files exist. Base requirements contain NumPy, scikit-optimize, and pyDOE2; the MCMC file includes the base file and `emcee`. No shipped code imports PyMC.

### “For a complete worked workflow, see [TUTORIAL.md](TUTORIAL.md).”

**File reference supported.** `TUTORIAL.md` exists. “Complete” means procedural guidance, not a runnable fixture: no example `.FCStd` model ships.

### “Factor names ... must exactly match aliases (a cell address also works).”

**Supported by the intended Spreadsheet API usage.** The evaluator passes each name to `sheet.set()`, which accepts a cell address and, in relevant FreeCAD versions, aliases. Alias behavior remains dependent on the FreeCAD Spreadsheet implementation.

### “Noise sigma is applied additively ... per Taguchi repeat.”

**Supported.** The engine samples `random.gauss(0, sigma)` for each factor/repeat, and `eval_script.py` adds the perturbation to the control value. The document correctly calls it additive sigma rather than fixed noise levels.

### “Cancellation takes effect between evaluations.”

**Supported and appropriately limited.** The stop flag is checked immediately before an evaluator call. The active subprocess is not terminated.

### “A subprocess opens the saved file, not unsaved GUI state.”

**Supported.** Only the file path and JSON request are sent to the subprocess. No unsaved document state is serialized.

### “The evaluator uses `femtools.ccxtools.FemToolsCcx`, whose details can vary among FreeCAD releases.”

**Supported and correctly qualified.** This is consistent with the prior audit. The exact method sequence still requires target-version testing.

### JSON input contract

**Supported.** `Evaluator.py` writes `document`, `spreadsheet`, `analysis`, `parameters`, `noise`, `metric_object`, and `metric_property`. `eval_script.py` returns an `ok` Boolean and either an objective or error.

## 2. Gaps or contradictions

### “MCMC samples a PyMC hyperparameter prior while `skopt` remains the acquisition driver.”

**Directly contradicted by the implementation and by the README's own installation paragraph.** MCMC mode imports `MCMCBayesianOptimizer`, which uses `emcee`, scikit-learn Gaussian processes, and posterior-averaged Expected Improvement. It returns before the `skopt.Optimizer` branch, so `skopt` is not the acquisition driver in MCMC mode. PyMC is not imported. Replace this sentence entirely.

### Architecture arrow “B[skopt GP + EI/PI/LCB]”

**Incomplete.** It describes standard mode only. If MCMC is selected, the implementation uses `emcee` and integrated EI only; PI/LCB are ignored. If `skopt` cannot be imported, bounded random search is used. The diagram should branch into standard GP, experimental MCMC-EI, and random fallback.

### “L9 (up to 4 factors) or L27 (up to 8), repeat count, smaller-is-better or nominal-is-best S/N.”

**Partly supported, but nominal-is-best is not a sound standard implementation.** The UI offers both modes and enforces factor counts. However, `sn_ratio()` subtracts `abs(mean-target)` directly from a dB ratio, and the TaskPanel never supplies the Taguchi target, so it defaults to zero. This mixes units and does not implement a clearly documented Taguchi nominal-the-best formula. The README presents the option as mature when it should be corrected or marked experimental.

### “Failures and solver non-convergence become a large penalty”

**Too broad.** Python exceptions, timeouts, missing output, and explicit evaluator errors become `1e30`. The code does not explicitly inspect a CalculiX convergence status or the return value of `check_prerequisites()`/`ccx_run()`. A non-converged run is penalized only if the FreeCAD API raises or no usable result is produced. Replace with “detected evaluator failures receive a large penalty.”

### “On success, values are applied to the active spreadsheet and `RobustOptResult.Summary` is created.”

**Supported only for the ordinary first-run case.** `done()` performs those operations. On repeated runs, `addObject(..., "RobustOptResult")` may create `RobustOptResult001`, while the code writes to `getObject("RobustOptResult")`, leaving an extra object. If the user changes active documents during optimization, the result can be applied to the wrong document or fail. The README should state the active document must remain open and unchanged during a run.

### “A generic result scan is the fallback.”

**Technically true but underspecified.** The scan checks only result-like objects and four property names: `MaxVonMises`, `MaxDisplacement`, `vonMises`, and `DisplacementLengths`. It is not a general FRD parser or cross-version result extractor, despite the original project prompt mentioning such fallbacks.

### “values must be compatible with the model's expected units.”

**A warning exists, but it understates a code-level limitation.** Discovered quantities are converted to scalar `.Value`, and all evaluator writes use bare `str(number)`. Units are not preserved or reattached. This can break dimensioned Spreadsheet expressions even when the user's initial values were valid.

### Base dependency list includes `pyDOE2`

**Present but unused.** Orthogonal arrays are implemented internally. This is not a missing dependency, but it is unnecessary installation surface unless retained for planned arrays. The README does not explain why it is installed.

## 3. Unsupported claims

### “RobustOpt for FreeCAD 0.21+”

**Compatibility is asserted, not established.** The source targets FreeCAD APIs associated with 0.21-era builds, but the archive contains no FreeCAD-version matrix, CI, integration log, or recorded successful FEM run. The title should say “targeting FreeCAD 0.21+” until tested versions are listed.

### “Restart FreeCAD and select **RobustOpt** in the workbench selector.”

**Plausible but not verified by bundled evidence.** `InitGui.py` registers a workbench in the conventional layout, so this is expected. `package.xml` and import behavior have not been validated in an actual FreeCAD profile. Phrase as installation instructions rather than a guaranteed outcome, and add a tested-version note.

### “Expose the objective as a numeric property ... for example `MaxVonMises`.”

**The mechanism is supported; the example property is version/model-dependent.** The code does not create `MaxVonMises`, and many FreeCAD result objects may expose arrays or differently named fields. The example should be explicitly labeled illustrative and checked in the user's Data properties/Python console.

### “Constraints can be represented by a derived objective property that adds a penalty.”

**Conceptually possible but not implemented by RobustOpt.** The workbench can minimize any scalar property, so an externally prepared penalized property could work. No helper, expression template, constraint editor, or tested example is shipped. This must be labeled a user/model-side technique, not a workbench feature.

### “FreeCAD banner output is tolerated.”

**Reasonably supported but not guaranteed.** The parser chooses the last stdout line beginning with `{`. Ordinary non-JSON banners are tolerated. A later JSON-looking diagnostic or output emitted after the evaluator result could break the protocol. Use “ordinary non-JSON banner lines are usually tolerated.”

## 4. Recommended document corrections

1. Replace the false MCMC bullet with: **“Experimental MCMC mode uses `emcee` to sample GP hyperparameters and averages Expected Improvement over those samples; it bypasses the standard `skopt` branch.”**
2. Update the Mermaid diagram to show standard `skopt`, experimental MCMC-EI, and random-search fallback branches.
3. Change the title to “targeting FreeCAD 0.21+” and add a tested-version table once end-to-end runs exist.
4. Replace “solver non-convergence” with “detected evaluator errors, timeouts, and unusable results.”
5. Mark nominal-is-best S/N experimental or remove it until the formula and target UI are corrected.
6. Describe the fallback scan as a limited common-property scan, not a generic result extractor.
7. Add an explicit unit limitation: the current implementation writes bare scalar strings and may not preserve dimensioned Spreadsheet units.
8. State that the optimized document must remain the active open document until completion.
9. Clarify that constraints are user-encoded in the model's scalar objective; no constraint interface ships.
10. Add the exact optional installation command:

   ```bat
   "C:\Program Files\FreeCAD 0.21\bin\python.exe" -m pip install -r "%APPDATA%\FreeCAD\Mod\RobustOpt\requirements-mcmc.txt"
   ```

11. Remove `pyDOE2` from base requirements if no shipped code needs it, or document its planned/optional role.
12. Qualify the JSON parser statement and document that it uses the last JSON-looking stdout line rather than a dedicated protocol marker.

## 5. Final verdict

**Partially supported.** The README is substantially aligned with the ordinary pipeline and is more accurate than the original handover. Its largest factual error is the MCMC description, which contradicts both code and dependencies. Compatibility, nominal S/N maturity, solver non-convergence detection, result extraction generality, unit safety, and repeat-run model updates remain overstated or insufficiently qualified.

**Next file to audit:** `RobustOpt/TUTORIAL.md`.

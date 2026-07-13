# RobustOpt audit continuation — `TUTORIAL.md`

**Document reviewed:** `RobustOpt/TUTORIAL.md` from the current archive  
**Method:** static comparison with the shipped implementation and prior audit findings. No FreeCAD model was created and no CalculiX solve was executed.

## 1. Confirmed support

### “This tutorial matches the UI and behavior of this distribution. RobustOpt runs the complete **Taguchi → Bayesian → PID** pipeline from one dialog.”

**Mostly supported.** The workbench registers one `RobustOpt_Run` command, opens one `RobustOptDialog`, and `Pipeline.run()` invokes the three methods in that order. PID is optional when its parameter field is blank. “Complete” should not imply that every stage is production-validated.

### “Save the document as `cantilever.FCStd`. Subprocesses read the saved file”

**Supported.** The dialog passes `ActiveDocument.FileName`; `SubprocessEvaluator` resolves it to an absolute path; `eval_script.py` opens that saved path. The named file is an instruction for the user to create, not a claim that a sample file ships.

### “Run the analysis manually once. Correct every prerequisite error before optimizing.”

**Appropriate and consistent with implementation risk.** RobustOpt assumes a complete existing Analysis and does not construct or validate the FEM setup comprehensively.

### “MCMC mode additionally requires `emcee`”

**Supported.** The optional code imports `emcee`, and `requirements-mcmc.txt` includes it. The base requirements do not.

### “RobustOpt minimizes one scalar returned by the FEM subprocess.”

**Supported.** `evaluate()` returns one `objective`; all three stages consume that scalar.

### “The current release treats the selected scalar as the objective; it does not silently assume fixed 250 MPa or 0.5 mm limits.”

**Supported and important.** No such built-in limits or general constraint interface exists.

### “Click **Load spreadsheet aliases** to discover numeric aliases, or enter rows manually.”

**Supported.** That button calls `load_aliases()`, and the factor table is editable.

### “Select **L9** for up to four factors or **L27** for up to eight.”

**Supported.** `start()` enforces those limits, and the engine supplies arrays with corresponding column capacities.

### “Enable MCMC to integrate Expected Improvement over `emcee` GP-hyperparameter posterior samples.”

**Supported, with experimental qualifications.** The implementation averages EI over retained hyperparameter samples and selects the best member of a random candidate set.

### “Leave the parameter blank to skip PID.”

**Supported.** `Pipeline.pid()` detects an empty parameter and returns without adjustment, although it performs one additional objective evaluation.

### “The progress bar allocates approximately 0–30% to Taguchi, 30–85% to Bayesian optimization, and 85–100% to PID.”

**Supported.** Those ranges are hard-coded in the three stages.

### “**Cancel** requests cooperative cancellation. An active CalculiX evaluation is allowed to finish; cancellation takes effect before the next evaluation.”

**Supported.** The worker sets a Boolean checked by `_eval()` before each subprocess call. It does not terminate the running process.

### “PID gain sign depends on the model response.”

**Supported by the controller equation.** The code updates the selected parameter with `Kp*(target-response)` plus integral and derivative terms. A response that changes in the opposite direction requires the corresponding gain sign.

### “Optimization does not replace verification.”

**Appropriate and necessary.** The recommendation to rerun with a refined mesh and review engineering assumptions is consistent with the prototype's limitations.

## 2. Gaps or contradictions

### “For mass minimization with stress/deflection constraints, create a numeric derived property in the model that returns mass plus a large penalty when a limit is violated, then select that property.”

**Conceptually plausible but not demonstrated.** No sample object, expression, macro, or code is provided to create or refresh such a property after `load_results()`. A normal static FreeCAD property does not automatically calculate mass and inspect newly generated FEM results. This technique requires user-authored model logic and may not execute in the headless subprocess. Present it as an advanced custom integration pattern, not a straightforward built-in workflow.

### “Unit-aware aliases should use bounds in the same base scalar convention accepted by the model.”

**Too vague and does not resolve the implementation defect.** `load_aliases()` converts cell content to `App.Units.Quantity(raw).Value`, discards its unit, and the evaluator later writes `str(number)` with no unit suffix. The tutorial should explicitly say that unit preservation is not implemented and that dimensioned cells may fail. “Same base scalar convention” is not a reliable FreeCAD Spreadsheet contract.

### “When complete, the queued Qt result signal applies the best parameters on FreeCAD's GUI thread”

**Structurally likely, not proven.** `Worker.result` is connected to a method on the dialog object, so Qt's cross-thread auto connection should queue it to the receiver thread. The code does not explicitly request `Qt.QueuedConnection`, assert thread affinity, or use `QTimer.singleShot`. More importantly, it updates `App.ActiveDocument`, which may no longer be the document that was optimized.

### “and creates `RobustOptResult.Summary`.”

**Supported on the first ordinary run, defective on repeated runs.** A later `addObject(..., "RobustOptResult")` may create `RobustOptResult001`, but the code writes to the original `getObject("RobustOptResult")`. The tutorial should not imply clean repeat-run behavior.

### “If the selected property is unavailable, the evaluator scans common FEM result properties.”

**Supported but narrower than a reader may infer.** It scans four names on objects whose TypeId/name appears result-related. It is not a generic result-mesh reader or FRD fallback and may miss the actual properties in a given FreeCAD release.

### “MCMC is most useful with sparse/noisy observations”

**Inferred guidance, not established for this package.** This is a general modeling heuristic, but no benchmark, calibration study, or convergence comparison demonstrates improved RobustOpt results. Rephrase as “may be useful” and identify the mode as experimental.

## 3. Unsupported claims

### “The final stdout JSON line is either ...” indirectly relied upon by the troubleshooting workflow

The tutorial does not quote the protocol, but its troubleshooting assumes detailed evaluator diagnostics reach the user. That assumption is not satisfied consistently.

### “All objectives are `1e30` | Read the evaluator error in the log”

**Unsupported by the current logging path.** `SubprocessEvaluator.evaluate()` returns `(penalty, detail)` containing the error, but `Pipeline._eval()` discards `detail` and logs only `objective=%g parameters=%s`. The user normally sees `1e30` and parameters, not the underlying evaluator error. Only an exception escaping the pipeline produces a traceback through `Worker.failed`. The code must log `detail["error"]`, or the tutorial must instruct users to run `eval_script.py` manually / inspect additional diagnostics that actually exist.

### “Run one evaluation through `eval_script.py`” is not in this tutorial, but the setup implies ordinary users can diagnose it

**No direct command is supplied.** The JSON request schema exists, but the tutorial does not show how to construct a request file or invoke `freecadcmd.exe`. This limits troubleshooting of the version-sensitive evaluator.

### “The evaluator scans common FEM result properties” as a practical fallback for all supported versions

**Not established.** The property names and result object types vary. The tutorial appropriately says property names vary, but it still presents the fallback as a usable recovery path without listing its narrow supported names or tested versions.

### “MCMC is ... slower than standard `skopt` GP mode.”

**Highly likely, but not measured in this package.** MCMC repeatedly fits GPs, so the expectation is technically reasonable; no bundled benchmark proves a runtime relationship on a target FreeCAD installation. Phrase it as expected overhead, not measured behavior.

### Beam/FEM setup instructions as version-independent steps

Claims such as **“Bind the force magnitude to `Spreadsheet.Force` where supported”** are already qualified, which is good. However, menu names, object types, solver availability, expression support, and Netgen packaging vary by FreeCAD version. The tutorial should state which exact FreeCAD release was used to verify the workflow; currently none is identified.

## 4. Recommended document corrections

1. Replace “matches the UI and behavior” with **“describes the intended UI and behavior; FEM steps must be adapted and tested for the installed FreeCAD release.”**
2. Mark the penalized-property constraint technique as custom model scripting and provide a tested implementation before recommending it as a normal workflow.
3. Add an explicit warning that factor writes do not preserve Spreadsheet units; recommend dimensionless driver cells or implement unit-aware values.
4. Replace “queued Qt result signal applies” with a qualified statement and instruct users not to close or switch the active document during a run.
5. Correct repeated `RobustOptResult` handling in code, then document repeat runs.
6. Replace “Read the evaluator error in the log” because errors are currently discarded by `Pipeline._eval()`. Preferably fix the engine to log `detail["error"]`.
7. List the exact fallback property names and state that no FRD parser/general result-mesh extraction ships.
8. Label MCMC optional and experimental wherever it is recommended; describe speed as expected rather than benchmarked.
9. Add a tested-version field for the GUI/FEM instructions, or explicitly state that no end-to-end version has yet been certified.
10. Include a concrete diagnostic command and sample request JSON if users are expected to test `eval_script.py` independently.
11. State that noise is applied to every configured control factor, not through a separate noise-factor table, and may move effective values outside control bounds.
12. Clarify that leaving PID blank still causes one final objective evaluation in the current implementation.

## 5. Final verdict

**Partially supported.** The tutorial is substantially more accurate than the original handover and correctly describes the one-dialog pipeline, optional PID, MCMC dependency, additive noise, cooperative cancellation, and independent engineering verification. Its most consequential unsupported instruction is to “read the evaluator error in the log,” because the pipeline currently discards that error detail. Unit handling, custom penalized objectives, result fallback, GUI-thread wording, repeated-run behavior, and version-specific FEM setup also require stronger qualification.

**Next file to audit:** `RobustOpt/HANDOVER.md`.

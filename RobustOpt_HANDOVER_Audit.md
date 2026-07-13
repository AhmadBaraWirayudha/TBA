# RobustOpt audit continuation — `HANDOVER.md`

**Document reviewed:** `RobustOpt/HANDOVER.md` from the current archive  
**Method:** static comparison with shipped code, tests, requirements, and previously audited documentation. No FreeCAD/CalculiX integration run was performed.

## 1. Confirmed support

### “containing a three-stage optimization pipeline”

**Supported.** `Pipeline.run()` invokes Taguchi, Bayesian, then PID. PID can be disabled by leaving its parameter blank.

### “L9/L27 Taguchi screening with repeated additive noise and S/N ranking.”

**Supported at implementation level.** `orthogonal_array()` supplies L9/L27 rows; `taguchi()` performs Gaussian additive perturbations for the configured repeat count and ranks candidates using `sn_ratio()`. This does not validate the correctness of the nominal-is-best variant, which remains a separate known issue.

### “Gaussian-process Bayesian optimization through `scikit-optimize`, with a bounded random-search contingency when `skopt` cannot be imported.”

**Supported.** Standard mode uses `skopt.Optimizer(..., base_estimator="GP")`. The `ImportError` branch performs seeded uniform sampling inside factor bounds and reports progress.

### “Optional single-parameter PID adjustment against the same selected scalar response.”

**Supported.** PID uses the same evaluator objective and changes one named factor subject to its min/max bounds.

### “Each FEM evaluation runs in a native `freecadcmd.exe` subprocess using temporary JSON.”

**Supported structurally.** Each call invokes a new subprocess with a temporary request file. Cleanup occurs in `finally`. Successful execution remains target-environment dependent.

### “This is a **code-complete candidate**, not a claim of universal FEM compatibility.”

**Appropriately qualified.** This is materially more accurate than “fully functional.” The source tree contains the intended modules and main branches, while the document acknowledges missing end-to-end validation.

### Delivered-file inventory

**Supported.** `README.md`, `TUTORIAL.md`, `ADDENDUM.md`, source, icons, metadata, dependency files, and `tests/test_engine.py` exist. `cantilever.FCStd`, `RobustOpt_config.json`, and `RobustOpt_Advanced_Guide.md` do not exist, as stated.

### “`eval_script.py` uses `femtools.ccxtools.FemToolsCcx`.”

**Supported.** The import and runner sequence are present. The handover correctly calls the integration high-risk and version-sensitive.

### “The workbench minimizes one scalar objective. Explicit multi-objective optimization and a general constraint editor are not implemented.”

**Supported.** The evaluator contract returns one objective, and no constraint/multi-objective UI or model exists.

### “Cancellation is cooperative between evaluations.”

**Supported.** The stop flag is checked before evaluation; the active process is not terminated.

### “If `skopt` cannot be imported ... bounded uniform random search”

**Supported in the current archive.** This accurately reflects the revised engine.

### “If `emcee` is absent while MCMC is selected, that mode fails clearly; it does not silently downgrade”

**Substantially supported.** The import error escapes the pipeline, `Worker.failed` emits a traceback, and the GUI log displays it. There is no preflight dialog specific to MCMC, so “clearly” means a technical traceback rather than a tailored dependency message.

### “No benchmark measurements are bundled.”

**Supported.** No benchmark report or measured run log ships. The handover appropriately labels time figures as assumptions rather than guarantees.

### “Treat Addon Manager publication as future work”

**Supported and accurate.** No real repository URL/release hosting is configured.

## 2. Gaps or contradictions

### “The final result is applied through a cross-thread Qt signal on the GUI thread.”

**Supported by expected Qt auto-connection behavior, but too definite without integration evidence.** `Worker.result` is connected to `RobustOptDialog.done`. Because sender execution and receiver affinity differ, Qt should queue the call. The connection is not explicitly declared `Qt.QueuedConnection`, and no thread-affinity assertion/test ships. Additionally, `done()` updates whichever document is `App.ActiveDocument` at completion, not a captured document identity. Qualify this as the intended threading design.

### “No document in this package should instruct maintainers to depend on those absent files.”

**The dependency claim is narrowly true, but the documentation remains inconsistent.** `ADDENDUM.md` explicitly refers to “the supplied `add.md`” and “The subsequent advanced guide,” neither of which is included or identified. It does not instruct runtime dependence, but it does make the distributed documentation rely on absent historical context. The handover should require removal or inclusion of those references.

### “Solver failures receive a large penalty and the search continues.”

**Incomplete.** Exceptions, timeouts, absent JSON, and explicit evaluator errors receive `1e30`. The code does not inspect all solver return/prerequisite/convergence states, so undetected non-convergence may not be classified as a failure. Also, the underlying error detail is discarded by `Pipeline._eval()`, reducing diagnosability. Use “detected evaluator failures.”

### “It is the slowest and least field-validated path.”

**Half confirmed, half inferred.** “Least field-validated” is consistent with the absence of any MCMC tests or integration evidence. “Slowest” is technically likely because it repeatedly samples/fits GPs, but no bundled benchmark compares modes. Change to “expected to add the highest surrogate-computation overhead.”

### “Constraints can be encoded in a model-derived penalized scalar.”

**Conceptually possible but not demonstrated.** No shipped example shows a derived property that updates after headless FEM result loading. This is a custom model/plugin extension pattern, not a verified workbench capability.

### “Standard installation: `python.exe -m pip install -r requirements.txt`.”

**Ambiguous in a Windows FreeCAD handover.** Running an arbitrary `python.exe` can install packages into the system Python rather than FreeCAD's bundled interpreter. The README gives a safer full path. The handover should explicitly say `C:\Program Files\FreeCAD ...\bin\python.exe` or “FreeCAD's bundled Python.”

### “Run one evaluation through `eval_script.py`”

**Valid as an acceptance objective but not operationally documented.** `eval_script.py` expects a JSON request file as its final argument. No sample request fixture or command is supplied in the handover. A maintainer can infer the schema from code/README, but the acceptance step is incomplete.

### Runtime formula: “`Bayesian iterations × average FEM solve time`”

**Under-counts the implementation.** Standard, random-fallback, and MCMC branches first evaluate the Taguchi start point and then perform the configured number of iterations: approximately `(iterations + 1)` FEM evaluations. PID also performs an initial evaluation and, even when disabled, performs one extra evaluation. The formula is explicitly approximate but should include these fixed evaluations.

### “Confirm ... units” in the acceptance test

**Correct as a test priority but insufficient as disclosure.** Unit loss is a known implementation risk: aliases are converted to scalar values and written without unit suffixes. It belongs in “Known risks and limitations,” not only in an acceptance checklist.

## 3. Unsupported claims

### “The included pure-Python tests verify L9/L27 dimensions and balance”

**Not fully supported.** `test_arrays()` checks L9 and L27 row counts, but the explicit balance assertion iterates only over the four L9 columns. It does not verify L27 column balance or pairwise orthogonality. Replace with: “verify L9 dimensions and per-column balance, and L27 row/column dimensions.”

### “RobustOpt is an installable FreeCAD Python workbench”

**Supported as packaging structure, not as tested behavior.** `InitGui.py`, the workbench class, command registration, and archive layout are conventional. No bundled evidence shows installation and loading in FreeCAD. Prefer “packaged for manual installation as a FreeCAD Python workbench.”

### “MCMC mode adds `emcee`, scikit-learn/SciPy behavior”

**Implementation fact, but dependency compatibility is not established.** `emcee`, SciPy, and scikit-learn are imported transitively/directly. `requirements-mcmc.txt` does not pin versions, and no FreeCAD-bundled Python compatibility matrix or Windows wheel test ships. The handover correctly calls this risky but should not imply known compatibility.

### “Run the analysis manually first and regression-test each supported FreeCAD version.”

**Sound recommendation, but “supported” versions are undefined.** The header says FreeCAD 0.21 or later, while no version has documented end-to-end verification. Replace “supported” with “targeted,” or add a tested-version table.

### “one analysis object layout” / target “FreeCAD 0.21 or later”

**Target rather than confirmed support.** The handover mostly qualifies compatibility correctly, but the header can still be read as a support claim. Use “Targeted, not yet certified: Windows 10/11 and FreeCAD 0.21+.”

## 4. Recommended document corrections

1. Change the header to **“Targeted environment (not yet certified): Windows 10/11, FreeCAD 0.21+.”**
2. Replace “installable” with “packaged for manual installation” until an actual FreeCAD load test is recorded.
3. Correct the test claim to distinguish L9 balance checks from L27 dimension-only checks.
4. Qualify GUI-thread application as the intended Qt signal design and document the active-document switching hazard.
5. Replace “solver failures” with “detected evaluator failures” and note that detailed errors are currently discarded by `Pipeline._eval()`.
6. Move unit loss into the high-risk limitations section.
7. Change the installation commands to explicitly invoke FreeCAD's bundled Python.
8. Add a concrete `freecadcmd.exe eval_script.py request.json` acceptance example and a sample request JSON fixture.
9. Correct evaluation-count formulas to include the extra Bayesian start evaluation and PID initial/disabled evaluation.
10. Reword MCMC speed as expected overhead unless benchmark data is added.
11. Label penalized scalar constraints as an unverified custom-model integration pattern.
12. Remove the absent historical references from `ADDENDUM.md`, or include and identify those source documents.
13. Define a tested-version matrix before using “supported FreeCAD version.”
14. Add MCMC, random-fallback, PID, nominal S/N, evaluator protocol, and repeat-run tests to make “code-complete candidate” easier to defend.

## 5. Final verdict

**Partially supported.** This handover is the most cautious and technically accurate document in the bundle. It correctly distinguishes code completeness from universal FEM compatibility, identifies MCMC and FEM risks, separates optional requirements, removes absent-file promises, and avoids Addon Manager readiness claims. Remaining issues are narrower but material: it overstates the scope of L27 testing, treats intended Qt thread behavior as verified, undercounts evaluations, omits unit loss from known risks, uses an ambiguous Python installation command, and retains an unverified FreeCAD 0.21+ target as if it were a support range.

**Next file to audit:** there are no further `.md` files in `RobustOpt.zip`. If continuing beyond Markdown, audit `package.xml` next, followed by `InitGui.py` and `Commands.py`.

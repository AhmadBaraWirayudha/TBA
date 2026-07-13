# RobustOpt audit continuation — `ADDENDUM.md`

**Document reviewed:** `RobustOpt/ADDENDUM.md` from the current archive  
**Method:** static comparison with the shipped Python, dependency files, icons, tests, and tutorial. No FreeCAD/CalculiX execution was performed.

## Supported statements

### “L9/L27 orthogonal arrays are used instead of `fullfact`.”

**Supported.** `OptimizationEngine.orthogonal_array()` contains a hard-coded L9 and constructs an eight-column L27 over three levels. No `fullfact` call is present. The tests verify L9 balance and L9/L27 row counts, although they do not verify every L27 pairwise column combination.

### “Bounds and aliases come from the UI rather than hard-coded Length/Width/Height ranges.”

**Supported with limitations.** `TaskPanel.py` accepts factor names and min/max values in a table. `load_aliases()` enumerates `getNonEmptyCells()`, calls `getAlias()`, and suggests bounds. There are no hard-coded beam-factor ranges in the engine. However, unit metadata is not retained when discovered values are converted to `Quantity.Value` and later written as bare numbers.

### “FEM metrics are extracted from a selected result property; no fake stress, displacement, or mass constants are returned.”

**Mostly supported.** The evaluator reads the selected object/property and converts it to a scalar. No fake engineering constants are present. The wording “metrics” is broader than the actual contract: one scalar objective is returned per evaluation. Its fallback scans a small list of property names but is not a general stress/displacement/mass extractor.

### “`freecadcmd.exe` output tolerates FreeCAD banners and reads the final JSON record.”

**Supported with a protocol caveat.** `Evaluator.evaluate()` selects JSON-looking stdout lines and parses the last one, which tolerates ordinary banner lines. It has no unique protocol marker, so an unrelated later line beginning with `{` could be misidentified.

### “Temporary files are removed in `finally`, timeouts become penalties, and subprocesses use Windows no-window flags.”

**Supported.** JSON cleanup occurs in `finally`; exceptions including `TimeoutExpired` are caught and converted to the configured penalty; `CREATE_NO_WINDOW` is used where available. The timeout defaults to 3600 seconds and cancellation does not interrupt an active subprocess.

### “The complete three-stage pipeline runs from one command.”

**Supported, but ‘complete’ should be qualified.** `RobustOpt_Run` opens one dialog and `Pipeline.run()` invokes Taguchi, Bayesian/random fallback, and PID in sequence. PID is intentionally skipped if its parameter is blank. This is a single-run pipeline after substantial model preparation and configuration, not literal zero-configuration one-click optimization.

### “The four named SVG resources ... are included.”

**Supported.** `RobustOpt_Setup.svg`, `RobustOpt_Taguchi.svg`, `RobustOpt_Bayesian.svg`, and `RobustOpt_PID.svg` exist. They are copies of the same placeholder artwork and are not attached to four shipped commands; only `RobustOpt_Run` is registered. “future command splitting” is explicitly aspirational.

### “Windows Registry executable discovery, spreadsheet alias/bounds discovery, and pure-Python engine tests.”

**Supported.** Registry checks, alias loading, and `tests/test_engine.py` exist. The tests are narrow and do not validate FreeCAD, Windows registry access, subprocess execution, FEM, or GUI behavior.

## Mismatches and overstatements

### “The existing evaluator already uses the supported `FemToolsCcx` workflow ... rather than the guide’s version-sensitive `Fem.ccxFemTools` example.”

**Overstated and internally misleading.** The archive does use `femtools.ccxtools.FemToolsCcx`, but calling it “the supported workflow” implies stable cross-version compatibility that has not been demonstrated. Its constructor and methods—`setup_working_dir()`, `setup_ccx()`, `check_prerequisites()`, `purge_results()`, `write_inp_file()`, `ccx_run()`, and `load_results()`—are themselves FreeCAD-version-sensitive. The code also ignores the value returned by `check_prerequisites()`. The correct wording is: “uses the `FemToolsCcx` API available in the targeted FreeCAD build; this sequence must be tested per release.”

### “real result properties”

**Technically true but too reassuring without qualification.** A named property is read rather than a fabricated value, but the code assumes the property exists after the subprocess creates/loads results and is scalar or quantity-convertible. Actual object names, types, arrays, and result properties vary by FreeCAD release and analysis. “Real” does not mean generally compatible or validated.

### “This revision adds ... pure-Python engine tests.”

**Supported but incomplete as a quality claim.** Only three tests ship. They do not test the MCMC optimizer, standard GP branch, random fallback, PID, nominal S/N, evaluator error protocol, unit handling, or any FreeCAD integration. The addendum should state the exact scope.

### “`MCMCBayesianOptimizer.py` now implements an actual emcee posterior over GP length scale, signal variance, and noise variance.”

**Substantially supported, experimental.** The code samples those three log-hyperparameters using the GP log marginal likelihood and bounded uniform log-priors. Risks omitted by the statement include dependency compatibility, repeated expensive GP fits, possible singular/constant-response behavior, no MCMC diagnostics, no convergence test, no GUI controls for walkers/steps/candidate count, and no unit test for this path.

### “Expected Improvement is integrated over posterior samples and maximized over a bounded random candidate set.”

**Supported with terminology qualification.** EI is averaged over retained samples and the highest-EI member of 256 uniformly random candidates is chosen. This is approximate candidate search, not continuous/global acquisition maximization. The candidate count and MCMC settings are source-level defaults.

### “Inputs are normalized, hyperparameters have bounded weak priors, and reproducible local randomness is used.”

**Supported.** Inputs are scaled to box bounds, the log-parameter support is bounded, and a local `RandomState(seed)` initializes candidates and walkers. Reproducibility still depends on NumPy/emcee/scikit-learn versions and deterministic FEM behavior.

### “the initial Taguchi candidate is retained as an observation.”

**Supported.** The MCMC branch evaluates and adds the Taguchi point before suggestions. Note that the point is evaluated again even though Taguchi already evaluated it under noise repeats, increasing solve count.

### “`TUTORIAL.md` documents ... real scalar objective selection, additive noise sigma, cooperative cancellation, MCMC mode, PID gain direction, and final engineering verification.”

**Supported.** Those topics appear in `TUTORIAL.md` and are broadly consistent with code. The tutorial appropriately says constraints must be encoded in a derived objective and warns that optimization requires independent verification.

### “Claims about four separate stage buttons, hard-coded force levels, fake mass output, and implicit stress/deflection constraints were corrected.”

**Supported for `TUTORIAL.md`.** The current tutorial does not make those promises. Historical source notes are not shipped as operational instructions.

## Referenced or absent material

1. **“the supplied `add.md`”** — `add.md` is not in `RobustOpt.zip`. The heading reads as provenance from an external conversation, not useful standalone product documentation. Either include it under a clearly marked `docs/reference/` directory with provenance/license, or rewrite the addendum without relying on an absent attachment.
2. **“The subsequent advanced guide”** — no file is identified and no advanced-guide document ships. This is an opaque reference. Name and include the document, or remove the reference.
3. The four icon files exist, but no four-command implementation exists. The addendum correctly calls splitting “future,” so it is not a direct false claim.
4. `emcee` is not in base `requirements.txt`; it is correctly isolated in `requirements-mcmc.txt`. The addendum should explicitly direct users to that optional file when describing MCMC.

## New risks introduced by this document

* It may give maintainers false confidence by contrasting the selected FEM API with a “version-sensitive” alternative while failing to acknowledge that the shipped API sequence is also version-sensitive.
* It presents MCMC mechanics accurately but omits its experimental status, absence of diagnostics/tests, and optional dependency installation.
* It uses historical, conversation-specific references (`add.md`, “subsequent advanced guide,” “supplied tutorial”) that make the distributed documentation look incomplete.
* “safer implementations” is a subjective comparative claim. Some choices are safer than placeholders, but unit loss, active-document update risk, cooperative-only cancellation, and unvalidated FEM APIs remain.

## Recommended edits

1. Rename the document to a conventional `IMPLEMENTATION_NOTES.md` or rewrite it as standalone release notes.
2. Replace “supported `FemToolsCcx` workflow” with a version-qualified statement requiring per-release integration tests.
3. Replace “FEM metrics” with “one selected scalar result property.”
4. State that the test suite is pure Python and excludes FreeCAD/FEM/MCMC integration.
5. Label MCMC optional and experimental; reference `requirements-mcmc.txt` and describe acquisition maximization as random-candidate approximation.
6. Remove or include the references to `add.md` and the unnamed advanced guide.
7. State that the four icons are placeholders and only one command is currently registered.
8. Add warnings about spreadsheet units, active-document changes, and cooperative cancellation.

## Verdict

**Partially supported.** Most concrete implementation statements in `ADDENDUM.md` correspond to shipped code. The principal unsupported implication is that `FemToolsCcx` provides a proven, stable workflow. The document also understates MCMC and integration-test risk and references source documents absent from the archive. It is suitable as internal development history after correction, but not yet as polished standalone release documentation.

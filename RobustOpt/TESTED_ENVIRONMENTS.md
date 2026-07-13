# Tested environments and validation status

**Status date:** 2026-07-13

## Certified end-to-end environments

**None.** No Windows FreeCAD/CalculiX end-to-end run is bundled or claimed. FreeCAD 0.21+ is a targeted API range, not a verified compatibility matrix.

## Verification completed in this source bundle

These static checks were last run in a Linux x86_64 sandbox with CPython 3.13.13. That is not the targeted Windows/FreeCAD runtime and does not demonstrate compatibility with FreeCAD's bundled Python.

The following checks are independent of FreeCAD and CalculiX:

* Python source compilation with `py_compile`.
* Pure-Python unit and branch-contract tests in `tests/test_engine.py`.
* Repository metadata tests in `tests/test_metadata.py`, including XML well-formedness for `package.xml`, local Markdown links, and documented-file presence.
* ZIP integrity check.

Mock-based branch tests verify control flow only; they do not validate the numerical behavior or Windows compatibility of `scikit-optimize`, `emcee`, FreeCAD, or CalculiX.

`tools/validate_with_freecad_python.bat` is provided to repeat compilation and these tests with a specified FreeCAD-bundled Python on Windows. `tools/run_evaluator_smoke_test.py` can launch one prepared JSON request through `freecadcmd.exe` and reject a nonzero exit or `{"ok": false}` result. The presence and mocked tests of these helpers are not evidence that either has been run against FreeCAD; no Windows result is currently recorded.

## Required record before claiming compatibility

For each environment tested, record all of the following without generalizing beyond that exact configuration:

| Field | Required value |
|---|---|
| Windows edition/build | Exact version and architecture |
| FreeCAD | Exact version/build and download source |
| Bundled Python | Exact version |
| CalculiX | Exact executable/version and discovery method |
| Dependencies | Exact installed versions of NumPy, scikit-optimize, scikit-learn, SciPy, and optional emcee |
| Model | Model name/hash and license; mesh and solver settings |
| Objective | Exact result object and property |
| Command | Exact smoke-test command and request JSON |
| Result | Expected and observed JSON objective, return code, and relevant log |
| GUI run | Workbench load, progress, cancellation, and final Spreadsheet update observations |

## Acceptance boundary

A successful smoke test on one configuration demonstrates only that the recorded scenario completed once; it does not certify that configuration for production or engineering use. Do not replace “targeting FreeCAD 0.21+” with a broad compatibility claim until representative releases and failure cases have been tested repeatedly and recorded.

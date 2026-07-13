# RobustOpt implementation notes

This document records implementation choices in the shipped package:

* L9/L27 orthogonal arrays are used instead of `fullfact`.
* Bounds and aliases come from the UI rather than hard-coded Length/Width/Height ranges.
* One scalar objective is read from a selected result property; no fake stress, displacement, or mass constants are returned.
* `freecadcmd.exe` output tolerates FreeCAD banners and reads the final JSON record.
* Temporary files are removed in `finally`, timeouts become penalties, and subprocesses use Windows no-window flags.
* One command starts the configured Taguchi and Bayesian stages followed by optional PID tuning.

The four named SVG resources from the addendum are included for compatibility and future command splitting.

## Evaluator and test scope

The package includes Windows Registry executable discovery, spreadsheet alias/bounds discovery, and pure-Python engine tests. The evaluator uses `femtools.ccxtools.FemToolsCcx` and reads a selected scalar result property. That API sequence and result-property naming are version-sensitive and require an end-to-end test for every targeted FreeCAD release. The included tests do not exercise FreeCAD, CalculiX, subprocess execution, or MCMC.

## Experimental MCMC mode

MCMC is optional, not installed by the base requirements, and has no bundled FreeCAD integration benchmark or convergence diagnostic. Install `requirements-mcmc.txt` to enable it. `MCMCBayesianOptimizer.py` implements an actual emcee posterior over GP length scale, signal variance, and noise variance. Expected Improvement is integrated over posterior samples and maximized over a bounded random candidate set. Inputs are normalized, hyperparameters have bounded weak priors, and reproducible local randomness is used. Unlike the supplied sketch, EI uses the full normal CDF/PDF formula and the initial Taguchi candidate is retained as an observation.

## Tutorial integration

`TUTORIAL.md` documents the single-dialog three-stage pipeline, real scalar objective selection, additive noise sigma, cooperative cancellation, MCMC mode, PID gain direction, and final engineering verification. Claims about four separate stage buttons, hard-coded force levels, fake mass output, and implicit stress/deflection constraints were corrected rather than presented as implemented behavior.

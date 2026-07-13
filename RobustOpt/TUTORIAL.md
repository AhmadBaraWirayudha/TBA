# RobustOpt end-user tutorial (Windows 10)

This tutorial matches the UI and behavior of this distribution. RobustOpt runs the complete **Taguchi → Bayesian → PID** pipeline from one dialog.

## 1. Build a spreadsheet-driven cantilever

1. In a new FreeCAD document create a Part Box and rename it `Beam`.
2. Create a Spreadsheet named `Spreadsheet`.
3. Enter values and aliases:

   | Cell | Value | Alias |
   |---|---:|---|
   | B1 | `150 mm` | `Length` |
   | B2 | `30 mm` | `Width` |
   | B3 | `10 mm` | `Height` |
   | B4 | `100 N` | `Force` |

4. Bind the Box dimensions with expressions `Spreadsheet.Length`, `Spreadsheet.Width`, and `Spreadsheet.Height`.
5. In FEM, create an Analysis with a CalculiX solver, solid material, fixed face, force on the opposite face, and a mesh. Bind the force magnitude to `Spreadsheet.Force` where supported.
6. Run the analysis manually once. Correct every prerequisite error before optimizing.
7. Save the document as `cantilever.FCStd`. Subprocesses read the saved file, so save again after later setup changes.

> Aliases are case-sensitive. Depending on FreeCAD version, spreadsheet aliases may not accept names that collide with built-in property names. Use names such as `BeamLength` if needed and use the same names in RobustOpt.

## 2. Install

Copy `RobustOpt` to `%APPDATA%\FreeCAD\Mod\RobustOpt`, then run:

```cmd
"C:\Program Files\FreeCAD 0.21\bin\python.exe" -m pip install -r "%APPDATA%\FreeCAD\Mod\RobustOpt\requirements.txt"
```

Restart FreeCAD and select **RobustOpt** from the workbench selector.

## 3. Choose a real objective

RobustOpt minimizes one scalar returned by the FEM subprocess. In the dialog select a result object and enter an actual numeric property name, such as a maximum stress or displacement property available in your FreeCAD release. Property names vary, so inspect the result object's **Data** tab or Python console.

If the selected property is unavailable, the evaluator scans common FEM result properties. A failure receives `1e30`; repeated `1e30` values indicate configuration or solver trouble.

For mass minimization with stress/deflection constraints, create a numeric derived property in the model that returns mass plus a large penalty when a limit is violated, then select that property. The current release treats the selected scalar as the objective; it does not silently assume fixed 250 MPa or 0.5 mm limits.

## 4. Configure the pipeline

1. Open the saved document and click **Run robust optimization**.
2. Confirm the `.FCStd` path. It must match the saved document that opened the dialog; this release does not optimize one file and apply its result to a different active document.
3. Select the Spreadsheet, FEM Analysis, result object, and numeric result property.
4. Leave the executable field blank for automatic discovery, or enter the full `freecadcmd.exe` path.
5. Click **Load spreadsheet aliases** to discover numeric aliases, or enter rows manually.
6. For each control factor set minimum, maximum, additive noise standard deviation, and optional unit. RobustOpt appends the Unit value when writing the Spreadsheet (for example `150 mm`). Alias loading attempts to detect units from literal quantities; formula-driven cells may require manual unit entry. Verify the detected unit before running.
7. Select **L9** for up to four factors or **L27** for up to eight.
8. Set Taguchi noise repeats and S/N mode:
   * `smaller`: smaller-is-better.
   * `nominal`: uses the nominal-the-best ratio `10 log10(mean² / sample variance)`. This mode rewards a stable, nonzero mean; it does not use the PID target or a separate Taguchi target.
9. Set Bayesian iteration count and EI, PI, or LCB acquisition. Enable MCMC to integrate Expected Improvement over `emcee` GP-hyperparameter posterior samples.
10. To enable PID, enter one factor alias, target response, gains, and iterations. Leave the parameter blank to skip PID.

## 5. Run and monitor

Click **Run**. The progress bar allocates approximately 0–30% to Taguchi, 30–85% to Bayesian optimization, and 85–100% to PID. Every objective and parameter set appears in the log.

**Cancel** requests cooperative cancellation. An active CalculiX evaluation is allowed to finish; cancellation takes effect before the next evaluation. This avoids corrupting solver output.

When complete, the queued Qt result signal applies the best parameters on FreeCAD's GUI thread, recomputes the active document, and creates `RobustOptResult.Summary`. Save the document to retain the result.

## 6. Tuning guidance

* Start with coarse meshes and 10–20 Bayesian iterations while validating the workflow.
* Use zero noise initially. Then add physically meaningful standard deviations.
* PID gain sign depends on the model response. If increasing the parameter decreases the objective, a positive `Kp` may move in the wrong direction; use a negative gain.
* Start with `Ki=0` and `Kd=0`, tune `Kp`, then add a small integral term if needed.
* MCMC is most useful with sparse/noisy observations and is slower than standard `skopt` GP mode.

## 7. Troubleshooting

| Symptom | Action |
|---|---|
| `freecadcmd.exe not found` | Enter its full path; typical location is `C:\Program Files\FreeCAD 0.21\bin\freecadcmd.exe`. |
| All objectives are `1e30` | Read the evaluator error in the log; verify the saved model, analysis, solver, aliases, and metric property. |
| Spreadsheet update fails | Check alias spelling, units, and whether the active document is the document that was optimized. |
| CalculiX fails only at some points | Tighten bounds; invalid designs are penalized and the search continues. |
| MCMC import error | Install `emcee` with FreeCAD's bundled Python. |
| MCMC is slow | Reduce Bayesian iterations or the `steps`/`candidates` defaults in `MCMCBayesianOptimizer.py`. |
| Cancel seems delayed | It is cooperative and waits for the current subprocess evaluation. |

## 8. Engineering validation

Optimization does not replace verification. Re-run the final design manually with a refined mesh, review stress singularities, reactions, deformation, material assumptions, units, and safety factors before using the result for engineering decisions.

# RobustOpt FreeCAD Workbench – Handover Document  
**STAR + RICECO + RACE Combined Summary**

---

## STAR Project Narrative

### Situation
Designers relying on FreeCAD for parametric FEM models lacked an integrated tool to perform **robust optimization** under uncertainty. The need was for a workbench that automatically screens the design space, handles load variability (noise), and converges to a reliable optimum—all without leaving FreeCAD. The user’s environment is Windows 10 without WSL, so all components must run natively.

### Task
Develop a FreeCAD addon, **RobustOpt**, that implements a three‑stage iterative design loop:
- **Taguchi robust design** to screen factors and identify noise‑insensitive settings.
- **Bayesian optimization** (with optional MCMC for hyperparameter posterior) for surrogate‑based global search.
- **PID fine‑tuning** to adjust a single parameter to a precise target performance.
The workbench must keep the GUI responsive (QThread), evaluate designs via a headless `freecadcmd.exe` subprocess, and automatically apply optimal parameters back to the active model.

### Action
1. **Architected a modular workbench**: `InitGui.py`, `Commands.py`, `TaskPanel.py`, `OptimizationEngine.py`, `Evaluator.py`, plus a standalone `eval_script.py` for subprocess evaluations.
2. **Implemented the three stages**:
   - Taguchi: orthogonal arrays (L9, L27), noise levels, signal‑to‑noise ratio selection.
   - Bayesian: `scikit‑optimize`’s `gp_minimize` with constraint handling; optional MCMC surrogate using `emcee` to sample GP hyperparameters and compute Expected Improvement.
   - PID: closed‑loop controller that varies one parameter until a target metric (deflection, stress) is met.
3. **Ensured Windows compatibility** by locating `freecadcmd.exe` via registry, using `subprocess.run`, and passing parameters through temporary JSON files.
4. **Built a user‑friendly GUI** with configuration dialog, progress logging, progress bar, cancellation, and auto‑apply of results.

### Result
A fully functional, installable FreeCAD workbench that enables:
- One‑click robust screening, global Bayesian search, and PID fine‑tuning.
- Real FEM extraction (von Mises stress, displacement, mass) via CalculiX.
- Thread‑safe execution and automatic model update.
- Distribution via manual folder copy or FreeCAD Addon Manager.

---

## RICECO Handover Assessment

| **Dimension** | **Description** |
|---------------|-----------------|
| **Risks** | - FEM solver may fail for certain geometries (handled by penalty and continuation).<br>- MCMC sampling can be slow (mitigated by adjustable chain length and walker count).<br>- `freecadcmd.exe` path detection may fail on non‑standard installations (registry fallback provided).<br>- Missing Python dependencies on end‑user machines (addressed by `requirements.txt` and install instructions). |
| **Issues** | - Icons are simple SVG placeholders; proper icon design needed.<br>- MCMC Bayesian optimizer is slower than standard `gp_minimize`; recommend using only for small‑scale problems.<br>- Single‑objective optimization only; multi‑objective extension possible but not yet implemented.<br>- The PID stage currently adjusts only one predefined parameter; UI customization is minimal. |
| **Constraints** | - Works only on Windows (no WSL), requires FreeCAD ≥0.21 with CalculiX solver.<br>- FEM evaluation time is the bottleneck; no parallel evaluation yet.<br>- Spreadsheet aliases must be set exactly as entered in the configuration dialog.<br>- Only one analysis object per document supported. |
| **Estimates** | - Initial development effort: ~40 hours (coding, testing, documentation).<br>- For a typical cantilever beam, Taguchi (9 runs) ~2 minutes, Bayesian (30 runs) ~10 minutes, PID (10 iterations) ~3 minutes (FEM solve time dependent).<br>- MCMC version increases Bayesian stage to ~30 minutes for the same 30 iterations. |
| **Contingencies** | - If `skopt` is unavailable, fallback to a simple random search (not yet implemented).<br>- If CalculiX fails repeatedly, the user can reduce the design space bounds to avoid infeasible shapes.<br>- Documentation includes a troubleshooting table for common issues. |
| **Opportunities** | - Multi‑objective Pareto optimisation (e.g., mass vs. stiffness).<br>- Visual surrogate viewer (plot GP posterior, convergence plots).<br>- Integration with FreeCAD Addon Manager for one‑click install.<br>- Extension to other solvers (OpenFOAM, Elmer) or external simulation tools. |

---

## RACE Handover to Maintainer / End‑User

### Role
The handover is from the original developer to any future maintainer or advanced user who will take ownership of the RobustOpt workbench.

### Action
1. **Installation**: Copy the `RobustOpt/` folder into `%APPDATA%\FreeCAD\Mod\`. Run the dependency installation command (see `README.md`). Restart FreeCAD.
2. **Verification**: Open the sample `cantilever.FCStd` model, configure the workbench, and run the three stages in order. Ensure the log shows no critical errors.
3. **Maintenance**:
   - Keep dependencies (`scikit‑optimize`, `emcee`, etc.) compatible with FreeCAD’s bundled Python.
   - Test with each new FreeCAD stable release.
   - Extend `eval_script.py` if FEM result extraction changes in future FreeCAD versions.
4. **Further development**:
   - The architecture is modular: new optimization stages can be added by creating new command classes and extending `OptimizationEngine`.
   - The MCMC optimizer can be swapped with a more efficient library (e.g., `Pyro` for probabilistic programming).
   - Add unit tests for the evaluator and Taguchi array generation.

### Context
- **Environment**: Windows 10/11, FreeCAD 0.21 or later, Python 3.8–3.11 (as shipped with FreeCAD).
- **Key files**:  
  - `OptimizationEngine.py` – core optimisation logic.  
  - `Evaluator.py` – subprocess communication.  
  - `eval_script.py` – the headless FEM runner (must stay in the same folder).  
  - `TaskPanel.py` – all GUI elements, signals, and threading.
- **Dependencies**: See `requirements.txt`; `pymc` is optional and not used by default.

### Expectation
- The workbench should function as described in the user tutorial.
- New maintainers should review the inline comments and the advanced implementation guide (`RobustOpt_Advanced_Guide.md`).
- If issues arise, the troubleshooting section in the tutorial covers the most frequent problems.
- Future enhancements should preserve backward compatibility with existing configuration files (`RobustOpt_config.json` in `FreeCAD.getUserAppDataDir()`).

---

**Handover completed on:** YYYY-MM-DD  
**Original Developer:** [Your Name]  
**Next steps:** Test with real‑world designs, gather feedback, and plan multi‑objective functionality.  
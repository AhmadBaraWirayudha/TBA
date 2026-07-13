
# Prompt: Build FreeCAD "RobustOpt" Workbench for Windows 10

You are an expert Python developer specialized in FreeCAD workbench creation.  
Follow the **STAR+RACE** structure below to build a complete, installable FreeCAD addon that combines **Taguchi robust design**, **Bayesian optimization with MCMC**, and a **PID fine‑tuner** for iterative parametric design. The addon must run on **Windows 10** without WSL, using only native FreeCAD Python and subprocess calls to `freecadcmd.exe`.

---

## STAR

### Situation
Designers need an integrated tool inside FreeCAD to perform multi‑stage robust optimization of parametric models driven by FEM simulations. The tool must automatically explore the design space, handle uncertainty in loads, and converge to a reliable optimum without leaving the FreeCAD environment. The user's laptop cannot use WSL, so everything must run natively on Windows.

### Task
Create a FreeCAD workbench named **RobustOpt** that provides:
- A configuration dialog to select a spreadsheet‑driven model and define control/noise factors.
- A **Taguchi** stage using orthogonal arrays to screen for robust settings.
- A **Bayesian optimization** stage with a Gaussian Process surrogate and optional MCMC sampling for hyperparameter uncertainty.
- A **PID controller** to fine‑tune a single parameter to a target performance value.
- Execution via a `QThread` to keep the GUI responsive, with each FEM evaluation run safely in a headless FreeCAD subprocess (`freecadcmd.exe`).
- Results written back to the active document.

### Action
1. **Design the workbench structure** as per FreeCAD’s addon conventions (`Init.py`, `InitGui.py`, `Commands.py`, `TaskPanel.py`, `OptimizationEngine.py`, `Evaluator.py`, `Resources/`).
2. **Build the configuration dialog** (PySide2) where the user picks the spreadsheet, FEM analysis, maps factor names, sets algorithm parameters.
3. **Implement the Taguchi engine**:
   - Generate orthogonal arrays (L9, L27, etc.) using `pyDOE2` or hardcoded arrays.
   - Run experiments with multiple noise levels for each row.
   - Calculate signal‑to‑noise ratios (smaller‑is‑better, nominal‑is‑best) and select the best robust candidate.
4. **Implement the Bayesian optimizer**:
   - Use `scikit‑optimize`’s `gp_minimize` with constraints.
   - Allow a checkbox to replace standard GP with a fully Bayesian GP using `pymc` and MCMC to sample hyperparameter posterior.
   - Acquisition function: Expected Improvement with constraint penalties.
5. **Implement the PID fine‑tuner**:
   - Let the user choose a target response and a single parameter to adjust.
   - Run a PID loop (proportional, integral, derivative) that calls the evaluator until convergence.
6. **Create the evaluator subprocess**:
   - Write a helper script `eval_script.py` that accepts JSON parameters, opens the FreeCAD document, modifies the spreadsheet, runs the FEM solver (CalculiX), and outputs results as JSON.
   - The main workbench calls this via `subprocess.run(["freecadcmd.exe", ...])` on Windows.
7. **Ensure thread safety** by running the optimization loop in a `QThread` and marshalling all GUI updates via signals.
8. **Package the workbench** with a `package.xml` for the FreeCAD Addon Manager and a `requirements.txt` for `scikit‑optimize`, `pyDOE2`, `pymc`, `numpy`.

### Result
A drop‑in FreeCAD addon that enables users to:
- Configure a parametric FEM model for optimization.
- Run the three‑stage optimization pipeline with a single click.
- View progress and final metrics in a log panel.
- See the optimal parameters automatically applied to the model.

---

## RACE

### Role
You are acting as a **senior Python/C++ developer for FreeCAD workbench development**. Your code must follow FreeCAD’s API conventions, be well‑documented, and handle Windows‑specific issues (paths, process creation, file locking).

### Action
Write all required Python files for the **RobustOpt** workbench, plus a standalone `eval_script.py` to be used as the subprocess. Include detailed comments and error handling. Provide a `README.md` explaining installation and usage.

### Context
The workbench will be used on **Windows 10** without WSL. FreeCAD is installed in the default location (e.g., `C:\Program Files\FreeCAD 0.21\`). The Python environment is the one bundled with FreeCAD (usually `...\bin\python.exe`). `freecadcmd.exe` is available in the same directory.

All heavy FEM computations must run in a separate process to avoid freezing the GUI. The main workbench must run on FreeCAD’s main thread and delegate the optimization loop to a `QThread`. The `QThread` calls `subprocess.run()` for each design evaluation.

The user’s parametric model is expected to have a spreadsheet with named cells and a fully configured FEM analysis (including mesh, material, constraints). The workbench will not create the FEM setup; it only drives existing analysis objects.

### Expectation
Deliver a complete, functioning FreeCAD workbench that can be unzipped into `%APPDATA%\FreeCAD\Mod\` and appear in the workbench selector. The code must:
- Use PySide2 for GUI elements.
- Use `FreeCAD`, `FreeCADGui`, `Fem` modules correctly.
- Include a Mermaid diagram of the architecture in the documentation.
- Handle all potential errors gracefully (e.g., FEM convergence failure) and continue the optimization loop.
- Be compatible with FreeCAD 0.21 or later.

---

## Technical Architecture Diagram (Mermaid)

flowchart TD
    User((User)) -->|Opens workbench| Setup[Setup Dialog\n- Spreadsheet & FEM selection\n- Factor mapping]
    Setup -->|Triggers optimization| Worker[OptimizationWorker QThread]

    subgraph OptimizationLoop[RobustOpt Engine]
        Worker --> Stage1[1️⃣ Taguchi Screening\n- Orthogonal array\n- Noise variation\n- S/N ratio selection]
        Stage1 -->|Robust start point| Stage2[2️⃣ Bayesian Optimization\n- GP surrogate (skopt)\n- Optional MCMC (pymc)\n- Constraint handling]
        Stage2 -->|Best candidate| Stage3[3️⃣ PID Fine-Tuning\n- Target setpoint\n- Single parameter adjustment]
    end

    Stage3 -->|Final parameters| UpdateModel[Update FreeCAD Spreadsheet]
    UpdateModel -->|Recompute| Doc[Active Document]
    Doc -->|Ready| User

    subgraph Evaluation[Evaluation Subprocess (freecadcmd.exe)]
        Stage1 & Stage2 & Stage3 -->|Send parameters JSON| EvalScript[ eval_script.py\n- Open & modify doc\n- Run FEM analysis\n- Extract results]
        EvalScript -->|Return metrics JSON| Worker
    end

    style User fill:#d0e0ff,stroke:#333,stroke-width:2px
    style Stage1 fill:#fff3cd,stroke:#333
    style Stage2 fill:#ffeeba,stroke:#333
    style Stage3 fill:#f5c6cb,stroke:#333
    style EvalScript fill:#d4edda,stroke:#333
```
flowchart TD
    User((User)) -->|Opens workbench| Setup[Setup Dialog\n-Select spreadsheet\n-Define factors & FEM]
    Setup -->|Triggers optimization| Worker[OptimizationWorker QThread]

    subgraph OptimizationLoop[RobustOpt Engine]
        Worker --> Stage1[1️⃣ Taguchi Screening\n- Orthogonal array\n- Noise variation\n- S/N ratio selection]
        Stage1 -->|Robust start point| Stage2[2️⃣ Bayesian Optimization\n- Gaussian Process surrogate\n- MCMC for hyperparameters\n- Constraint modeling]
        Stage2 -->|Best candidate| Stage3[3️⃣ PID Fine-Tuning\n- Setpoint target\n- Adjust single parameter\n- Rapid convergence]
    end

    Stage3 -->|Final parameters| UpdateModel[Update FreeCAD Spreadsheet]
    UpdateModel -->|Recompute| Doc[Active Document]
    Doc -->|Ready| User

    subgraph Evaluation[Evaluation Subprocess]
        Stage1 & Stage2 & Stage3 -->|Send parameters| Subprocess[freecadcmd script\n- Modify spreadsheet\n- Run FEM (CalculiX)\n- Extract results]
        Subprocess -->|Return metrics| Worker
    end

    style User fill:#d0e0ff,stroke:#333,stroke-width:2px
    style Stage1 fill:#fff3cd,stroke:#333
    style Stage2 fill:#ffeeba,stroke:#333
    style Stage3 fill:#f5c6cb,stroke:#333
    style Subprocess fill:#d4edda,stroke:#333
---

## Additional Constraints & Details

- **Windows Paths**: Use `os.path.join`, `tempfile`, and resolve `freecadcmd.exe` via `shutil.which("freecadcmd.exe")` or a configurable path.
- **Subprocess Communication**: Pass parameters as a temporary JSON file, receive results via `stdout` in JSON. Avoid pickling.
- **FEM Result Extraction**: Use `FemVTKTools` or `FemTools` to read von Mises stress and displacement; fallback to parsing `frd` files if needed.
- **Optimization Settings**: The setup dialog must allow choosing:
  - Taguchi array size.
  - Number of noise levels and noise factor distribution.
  - Bayesian optimization iterations, acquisition function type, MCMC on/off.
  - PID target, parameter to tune, gains.
- **Progress Reporting**: Emit `progress` signal with status messages (e.g., "Taguchi run 5/9", "Bayes iteration 12/50").
- **Error Handling**: If a design fails FEM, assign a penalty value and continue; log failures.
- **Dependencies**: Include a `requirements.txt` and a `DependencyCheck.py` that warns the user if required packages are missing and offers to install them via FreeCAD’s pip.

Please generate the complete workbench code now.



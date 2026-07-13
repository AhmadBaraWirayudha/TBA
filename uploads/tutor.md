
# RobustOpt Workbench – End‑User Tutorial (Windows 10)

This tutorial assumes you have installed the RobustOpt addon and its dependencies (see `README.md`).  
You will design a simple parametric cantilever beam and optimise it for minimum mass while staying below stress and deflection limits, even when the applied force varies (noise).

---

## 1. Prepare the Parametric Model

### 1.1 Create the Beam
1. Open FreeCAD, start a new document, switch to the **Part** workbench.
2. Create a **Cube** (`Part → Cube`).
3. In the Data tab, rename it to `Beam`.
4. Set `Length = 150 mm`, `Width = 30 mm`, `Height = 10 mm` (arbitrary starting values).

### 1.2 Create a Spreadsheet for Parameters
1. Switch to the **Spreadsheet** workbench.
2. Click **Create a new spreadsheet**.
3. In the spreadsheet:
   - Cell `A1` → `Length`, cell `B1` → `150`
   - Cell `A2` → `Width`, cell `B2` → `30`
   - Cell `A3` → `Height`, cell `B3` → `10`
   - Cell `A4` → `Force`, cell `B4` → `100` (newtons)
4. Set aliases:
   - Right‑click `B1` → **Properties** → **Alias**: `Length`
   - `B2` → `Width`
   - `B3` → `Height`
   - `B4` → `Force`
5. **Bind the dimensions**:
   - Select `Beam` in the tree view.
   - In the Data tab, click the `f(x)` icon next to `Length`.
   - Enter `Spreadsheet.Length` (or `<<Spreadsheet>>.Length`).
   - Repeat for `Width` and `Height` using the corresponding aliases.
6. Recompute (F5). The cube should now follow the spreadsheet values.

### 1.3 Set Up the FEM Analysis
1. Switch to the **FEM** workbench.
2. Select the `Beam` solid.
3. **Create an analysis container**:
   - `Model → Analysis container` (or toolbar button).
4. **Assign material**:
   - Select the analysis, then `Model → Material for solid`.
   - Choose `Steel` (or any material, we’ll manually adjust density later).
5. **Apply fixed constraint**:
   - Select one face of the beam (e.g., the face at `X=0`).
   - Click `Model → Fixed constraint`.
6. **Apply force load**:
   - Select the opposite face (e.g., `X=150`).
   - Click `Model → Force load`.
   - In the Data tab, set `Force = Spreadsheet.Force` (via the `f(x)` button).
7. **Mesh the part**:
   - Select the `Beam` solid.
   - `Mesh → FEM mesh from shape by Netgen`.
   - Choose a coarse mesh (e.g., Max size = 5 mm).
   - Click `Apply` and `OK`.
8. The analysis tree should look like:
   ```
   Analysis
   ├── SolverCcxTools
   ├── MaterialSolid
   ├── FixedConstraint
   ├── Force
   └── Beam_Mesh
   ```
9. Save the document as `cantilever.FCStd` in a convenient location (important: the workbench will open it by path).

---

## 2. Install Dependencies (One‑Time)

Open a **Command Prompt** (Admin) and run:

```cmd
"C:\Program Files\FreeCAD 0.21\bin\python.exe" -m pip install -r "%APPDATA%\FreeCAD\Mod\RobustOpt\requirements.txt"
```

(Adjust FreeCAD path if needed.) Restart FreeCAD.

---

## 3. Launch the Workbench and Configure

1. In FreeCAD, switch to the **RobustOpt** workbench (dropdown menu).
2. Click the **Configure Model** button (gear icon).
3. **Spreadsheet**: Choose `Spreadsheet` from the dropdown (should auto‑detect).
4. **FEM Analysis**: Choose the analysis object (often named `Analysis`).
5. **Control factors**: Enter `Length, Width, Height` (comma‑separated).
6. **Noise factors**: Enter `Force` (the load we cannot control perfectly).
7. Click **Save Configuration**. A message confirms saving.

---

## 4. Stage 1 – Taguchi Screening

1. Click **Run Taguchi Screening** (icon with “T”).
2. A panel opens with a log area. Click **Start**.
3. The workbench runs an L9 orthogonal array. For each design, it evaluates three force levels (90 N, 100 N, 110 N) to simulate noise.
4. The log will show something like:
   ```
   Starting optimization...
   Taguchi run 1/9: stress=180, deflection=0.6, mass=0.234
   ...
   Best S/N ratio: -12.3 dB, parameters: Length=150, Width=30, Height=10
   ```
5. When finished, the best robust parameters are automatically written into the spreadsheet and the model recomputes. You can inspect the values.

---

## 5. Stage 2 – Bayesian Optimisation (No MCMC)

1. Click **Bayesian Optimization** (icon with “B”).
2. Click **Start**.
3. The optimizer starts from the Taguchi result and calls the FEM evaluator for each new design point, aiming to minimise mass while satisfying:
   - Stress < 250 MPa
   - Deflection < 0.5 mm
4. The log shows iterations and the current best mass.
5. After 30 calls (default), it prints:
   ```
   Bayesian optimization finished: {'params': {'Length': 142.3, 'Width': 28.7, 'Height': 9.1}, 'fun': 0.201}
   ```
6. The model updates automatically. You now have a lighter beam that still meets constraints.

---

## 6. Stage 3 – PID Fine‑Tuning

Suppose you want exactly **0.3 mm** maximum deflection for stiffness matching.

1. Click **PID Fine‑Tuning** (icon with “PID”).
2. In the popup (if you added extra fields), select:
   - Target metric: Deflection
   - Target value: 0.3 mm
   - Parameter to adjust: Height
3. Click **Start**.
4. The PID controller varies `Height` and repeatedly runs FEM. You’ll see:
   ```
   PID iteration 1: deflection=0.45, error=0.15, new height=9.5
   ...
   PID converged after 8 iterations. Final height=9.72 mm, deflection=0.301 mm
   ```
5. The spreadsheet is updated again. Your beam now hits the stiffness target precisely.

---

## 7. (Optional) MCMC‑Bayesian Optimisation

If you want a more thorough treatment of uncertainty, enable MCMC:

1. In the configuration (or a dedicated checkbox), set `Use MCMC` to True.
2. Run Bayesian optimisation again. This time, instead of point estimates of the GP hyperparameters, it draws posterior samples and computes Expected Improvement over them.
3. Warning: each iteration takes longer (the MCMC chain runs), but the search may be more robust to sparse data.
4. The log shows “MCMC iteration …” and the best point found.

---

## 8. Interpreting and Exporting Results

- The final parameters are written directly into the spreadsheet. You can edit them further if desired.
- The log window contains a record of all evaluations; you can copy‑paste it into a text editor.
- The document is automatically recomputed, so you can immediately export the final shape via `File → Export` for 3D printing or further analysis.

---

## 9. Troubleshooting

| Problem | Solution |
|---------|----------|
| “freecadcmd.exe not found” | Set the correct path in `Evaluator.py` or ensure FreeCAD’s `bin` folder is in the system PATH. |
| FEM fails with “CalculiX error” | Check if the mesh is too coarse, constraints are incorrectly applied, or the design leads to geometric errors. The optimiser assigns a penalty and continues. |
| Progress bar doesn’t move | Ensure you installed `requirements.txt` with FreeCAD’s Python; some packages may be missing. |
| MCMC runs extremely slowly | Reduce `mcmc_steps` and `walkers` in `MCMCBayesianOptimizer.py`. |

---

## 10. Next Steps

- Experiment with different objective functions (e.g., minimise stress instead of mass) by editing the `run_bayesian()` objective.
- Add multiple noise factors (e.g., material variability) to the Taguchi stage.
- Create your own parametric models and let RobustOpt find the best design automatically!


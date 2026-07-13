import importlib.util, math, os, traceback
import FreeCAD as App
from PySide2 import QtCore, QtWidgets
from Evaluator import SubprocessEvaluator
from OptimizationEngine import Pipeline

class Worker(QtCore.QThread):
    message=QtCore.Signal(str); percent=QtCore.Signal(int); result=QtCore.Signal(dict,float); failed=QtCore.Signal(str)
    def __init__(self,evaluator,factors,cfg): super().__init__(); self.evaluator=evaluator; self.factors=factors; self.cfg=cfg; self.cancelled=False
    def run(self):
        try:
            p,y=Pipeline(self.evaluator,self.message.emit,self.percent.emit,lambda:self.cancelled).run(self.factors,self.cfg)
            self.result.emit(p,y)
        except Exception: self.failed.emit(traceback.format_exc())
    def cancel(self): self.cancelled=True

class RobustOptDialog(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super().__init__(parent or QtWidgets.QApplication.activeWindow()); self.worker=None
        self.setWindowTitle("RobustOpt configuration"); self.resize(760,700); root=QtWidgets.QVBoxLayout(self)
        form=QtWidgets.QFormLayout(); root.addLayout(form); doc=App.ActiveDocument
        self.document_name=doc.Name if doc else ""
        self.file=QtWidgets.QLineEdit(doc.FileName if doc else ""); form.addRow("Saved .FCStd model",self.file)
        names=[o.Name for o in doc.Objects] if doc else []
        self.sheet=QtWidgets.QComboBox(); self.sheet.addItems([o.Name for o in doc.Objects if o.TypeId=="Spreadsheet::Sheet"] if doc else []); form.addRow("Spreadsheet",self.sheet)
        analyses=[o.Name for o in doc.Objects if o.TypeId=="Fem::FemAnalysis"] if doc else []
        self.analysis=QtWidgets.QComboBox(); self.analysis.addItems(analyses); form.addRow("FEM analysis",self.analysis)
        self.metricObj=QtWidgets.QComboBox(); self.metricObj.setEditable(True); self.metricObj.addItems(names); form.addRow("Result object",self.metricObj)
        self.metricProp=QtWidgets.QLineEdit("MaxVonMises"); form.addRow("Numeric result property",self.metricProp)
        self.exe=QtWidgets.QLineEdit(); form.addRow("freecadcmd.exe (optional)",self.exe)
        root.addWidget(QtWidgets.QLabel("Control factors (alias/cell, minimum, maximum, noise σ, optional unit)"))
        self.table=QtWidgets.QTableWidget(3,5); self.table.setHorizontalHeaderLabels(["Name","Min","Max","Noise σ","Unit"]); root.addWidget(self.table)
        for r,row in enumerate((("Length",1,10,0,""),("Width",1,10,0,""),("Thickness",1,5,0,""))):
            for c,v in enumerate(row): self.table.setItem(r,c,QtWidgets.QTableWidgetItem(str(v)))
        factorButtons=QtWidgets.QHBoxLayout()
        add=QtWidgets.QPushButton("Add factor"); add.clicked.connect(lambda:self.table.insertRow(self.table.rowCount())); factorButtons.addWidget(add)
        load=QtWidgets.QPushButton("Load spreadsheet aliases"); load.clicked.connect(self.load_aliases); factorButtons.addWidget(load)
        root.addLayout(factorButtons)
        tabs=QtWidgets.QTabWidget(); root.addWidget(tabs)
        t=QtWidgets.QWidget(); tf=QtWidgets.QFormLayout(t); self.array=QtWidgets.QComboBox(); self.array.addItems(["L9","L27"]); self.noiseN=QtWidgets.QSpinBox(); self.noiseN.setRange(1,20); self.noiseN.setValue(3); self.sn=QtWidgets.QComboBox(); self.sn.addItems(["smaller","nominal"]); tf.addRow("Array",self.array);tf.addRow("Noise repeats",self.noiseN);tf.addRow("S/N mode",self.sn);tabs.addTab(t,"Taguchi")
        b=QtWidgets.QWidget();bf=QtWidgets.QFormLayout(b);self.bIter=QtWidgets.QSpinBox();self.bIter.setRange(1,1000);self.bIter.setValue(20);self.acq=QtWidgets.QComboBox();self.acq.addItems(["EI","PI","LCB"]);self.mcmc=QtWidgets.QCheckBox("Experimental: integrate EI over emcee GP-hyperparameter samples");bf.addRow("Iterations",self.bIter);bf.addRow("Acquisition",self.acq);bf.addRow(self.mcmc);tabs.addTab(b,"Bayesian")
        p=QtWidgets.QWidget();pf=QtWidgets.QFormLayout(p);self.pidParam=QtWidgets.QLineEdit();self.target=QtWidgets.QDoubleSpinBox();self.target.setRange(-1e12,1e12);self.kp=QtWidgets.QDoubleSpinBox();self.kp.setValue(.1);self.ki=QtWidgets.QDoubleSpinBox();self.kd=QtWidgets.QDoubleSpinBox();self.pIter=QtWidgets.QSpinBox();self.pIter.setValue(10)
        for label,w in (("Parameter (blank disables PID)",self.pidParam),("Target",self.target),("Kp",self.kp),("Ki",self.ki),("Kd",self.kd),("Iterations",self.pIter)):pf.addRow(label,w)
        tabs.addTab(p,"PID")
        self.progress=QtWidgets.QProgressBar();self.log=QtWidgets.QPlainTextEdit();self.log.setReadOnly(True);root.addWidget(self.progress);root.addWidget(self.log)
        buttons=QtWidgets.QDialogButtonBox();self.runBtn=buttons.addButton("Run",QtWidgets.QDialogButtonBox.AcceptRole);self.cancelBtn=buttons.addButton("Cancel",QtWidgets.QDialogButtonBox.RejectRole);root.addWidget(buttons);self.runBtn.clicked.connect(self.start);self.cancelBtn.clicked.connect(self.cancel)
    def load_aliases(self):
        """Populate factors from aliased numeric cells and suggest ±50% bounds."""
        try:
            sheet=App.ActiveDocument.getObject(self.sheet.currentText())
            rows=[]
            for cell in sheet.getNonEmptyCells():
                alias=sheet.getAlias(cell)
                if not alias:
                    continue
                raw=sheet.getContents(cell).lstrip("=")
                try:
                    quantity=App.Units.Quantity(raw)
                    current=float(quantity.Value)
                    unit=str(quantity.Unit)
                    if unit in ("1","Dimensionless"): unit=""
                except Exception:
                    continue
                span=max(abs(current)*0.5,1.0)
                rows.append((alias,current-span,current+span,0.0,unit))
            if not rows:
                raise ValueError("No aliased numeric spreadsheet cells found")
            self.table.setRowCount(len(rows))
            for r,row in enumerate(rows):
                for c,value in enumerate(row):
                    self.table.setItem(r,c,QtWidgets.QTableWidgetItem(str(value)))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,"RobustOpt",str(e))

    def factors(self):
        out=[]
        for r in range(self.table.rowCount()):
            vals=[self.table.item(r,c).text().strip() if self.table.item(r,c) else "" for c in range(5)]
            if vals[0]:
                lo,hi,noise=float(vals[1]),float(vals[2]),float(vals[3] or 0)
                if not all(math.isfinite(x) for x in (lo,hi,noise)): raise ValueError("Factor %s contains a non-finite value"%vals[0])
                if lo>=hi: raise ValueError("Factor %s requires Min < Max"%vals[0])
                if noise<0: raise ValueError("Factor %s requires Noise σ >= 0"%vals[0])
                out.append({"name":vals[0],"min":lo,"max":hi,"noise":noise,"unit":vals[4]})
        if not out: raise ValueError("Add at least one factor")
        if len(out)>8: raise ValueError("L27 supports at most 8 factors")
        return out
    def start(self):
        try:
            if not self.file.text() or not os.path.isfile(self.file.text()): raise ValueError("Save the active document first")
            doc=App.getDocument(self.document_name) if self.document_name else None
            if doc is None or not doc.FileName: raise ValueError("The document that opened this dialog is no longer available or saved")
            if os.path.normcase(os.path.abspath(self.file.text())) != os.path.normcase(os.path.abspath(doc.FileName)):
                raise ValueError("The model path must match the document that opened this dialog")
            if not self.sheet.currentText(): raise ValueError("No Spreadsheet::Sheet is available")
            if not self.analysis.currentText(): raise ValueError("No Fem::FemAnalysis object is available")
            factors=self.factors()
            if self.mcmc.isChecked():
                optional=(("emcee","emcee"),("sklearn","scikit-learn"),("scipy","scipy"))
                missing=[package for module,package in optional if importlib.util.find_spec(module) is None]
                if missing:
                    raise ValueError("MCMC mode is missing %s. Install requirements-mcmc.txt with FreeCAD's bundled Python." % ", ".join(missing))
            if self.array.currentText() == "L9" and len(factors) > 4:
                raise ValueError("L9 supports at most 4 factors; select L27 for up to 8")
            cfg={"taguchi":{"array":self.array.currentText(),"noise_levels":self.noiseN.value(),"sn":self.sn.currentText()},"bayes":{"iterations":self.bIter.value(),"acq":self.acq.currentText(),"mcmc":self.mcmc.isChecked()},"pid":{"parameter":self.pidParam.text().strip(),"target":self.target.value(),"kp":self.kp.value(),"ki":self.ki.value(),"kd":self.kd.value(),"iterations":self.pIter.value()}}
            self.running_sheet=self.sheet.currentText()
            units={f["name"]:f.get("unit","") for f in factors if f.get("unit","")}
            self.running_units=units
            ev=SubprocessEvaluator(self.file.text(),self.running_sheet,self.analysis.currentText(),self.metricObj.currentText(),self.metricProp.text(),self.exe.text(),units=units)
            self.worker=Worker(ev,factors,cfg);self.worker.message.connect(self.log.appendPlainText);self.worker.percent.connect(self.progress.setValue);self.worker.result.connect(self.done);self.worker.failed.connect(self.failure);self.runBtn.setEnabled(False);self.worker.start()
        except Exception as e: QtWidgets.QMessageBox.critical(self,"RobustOpt",str(e))
    def done(self,p,y):
        try:
            doc=App.getDocument(self.document_name) if self.document_name else None
            if doc is None:
                raise RuntimeError("The optimized document was closed before results could be applied")
            sheet=doc.getObject(self.running_sheet)
            if sheet is None:
                raise RuntimeError("The configured spreadsheet no longer exists")
            for name,value in p.items():
                unit=self.running_units.get(name,"")
                sheet.set(name,("%s %s"%(value,unit)) if unit else str(value))
            doc.recompute()
            result=doc.getObject("RobustOptResult")
            if result is None:
                result=doc.addObject("App::FeaturePython","RobustOptResult")
                result.addProperty("App::PropertyString","Summary")
            elif "Summary" not in result.PropertiesList:
                result.addProperty("App::PropertyString","Summary")
            result.Summary="objective=%g; %s"%(y,p)
            self.log.appendPlainText("DONE objective=%g %s"%(y,p));self.progress.setValue(100)
        except Exception as e:self.log.appendPlainText("Optimized, but model update failed: "+str(e))
        self.runBtn.setEnabled(True)
    def failure(self,s): self.log.appendPlainText(s);self.runBtn.setEnabled(True)
    def cancel(self):
        if self.worker and self.worker.isRunning(): self.worker.cancel();self.log.appendPlainText("Cancellation requested")
        else:self.reject()

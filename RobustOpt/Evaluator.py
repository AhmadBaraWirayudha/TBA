import json, os, shutil, subprocess, tempfile

class EvaluationError(RuntimeError): pass

class SubprocessEvaluator:
    def __init__(self, document, spreadsheet, analysis, metric_object="", metric_property="", freecadcmd="", timeout=3600, penalty=1e30, units=None):
        self.document=os.path.abspath(document); self.spreadsheet=spreadsheet; self.analysis=analysis
        self.metric_object=metric_object; self.metric_property=metric_property; self.units=dict(units or {})
        self.freecadcmd=self._resolve(freecadcmd); self.timeout=int(timeout); self.penalty=float(penalty)
        self.script=os.path.join(os.path.dirname(__file__), "eval_script.py")
    def _resolve(self, configured):
        candidates=[configured, shutil.which("freecadcmd.exe"), shutil.which("FreeCADCmd.exe")]
        # Native Windows installers may register either a machine-wide or per-user path.
        try:
            import winreg
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for key_name in (r"SOFTWARE\FreeCAD\FreeCAD", r"SOFTWARE\WOW6432Node\FreeCAD\FreeCAD"):
                    try:
                        with winreg.OpenKey(hive, key_name) as key:
                            root=winreg.QueryValueEx(key,"InstallPath")[0]
                            candidates += [os.path.join(root,"bin",x) for x in ("freecadcmd.exe","FreeCADCmd.exe")]
                    except OSError:
                        pass
        except (ImportError, OSError):
            pass
        try:
            import FreeCAD as App
            candidates += [os.path.join(App.getHomePath(), "bin", x) for x in ("freecadcmd.exe","FreeCADCmd.exe")]
        except Exception: pass
        for p in candidates:
            if p and os.path.isfile(p): return os.path.abspath(p)
        raise EvaluationError("freecadcmd.exe not found; set its full path")
    def evaluate(self, parameters, noise=None):
        payload={"document":self.document,"spreadsheet":self.spreadsheet,"analysis":self.analysis,
                 "parameters":parameters,"noise":noise or {},"units":self.units,
                 "metric_object":self.metric_object,"metric_property":self.metric_property}
        path=None
        try:
            fd,path=tempfile.mkstemp(suffix=".json",prefix="robustopt_"); os.close(fd)
            with open(path,"w",encoding="utf-8") as f: json.dump(payload,f)
            cp=subprocess.run([self.freecadcmd,self.script,path],capture_output=True,text=True,
                              timeout=self.timeout,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            # FreeCAD may print banners: use the final JSON-looking line.
            lines=[x.strip() for x in cp.stdout.splitlines() if x.strip().startswith("{")]
            if not lines: raise EvaluationError((cp.stderr or cp.stdout or "No evaluator output")[-2000:])
            out=json.loads(lines[-1])
            if not out.get("ok"): raise EvaluationError(out.get("error","evaluation failed"))
            return float(out["objective"]), out
        except Exception as e:
            return self.penalty,{"ok":False,"error":str(e),"objective":self.penalty}
        finally:
            if path:
                try: os.remove(path)
                except OSError: pass

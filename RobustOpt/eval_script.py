"""Executed only by FreeCADCmd: freecadcmd.exe eval_script.py request.json"""
import json, os, sys, traceback

def emit(x): print(json.dumps(x,separators=(",",":")))
def format_value(value,unit=""):
    unit=(unit or "").strip()
    return ("%s %s"%(value,unit)) if unit else str(value)
def number(v):
    if hasattr(v,"Value"): return float(v.Value)
    return float(v)
def main(req):
    import FreeCAD as App
    doc=App.openDocument(req["document"]); sheet=doc.getObject(req["spreadsheet"])
    if sheet is None: raise RuntimeError("Spreadsheet not found")
    merged=dict(req.get("parameters",{}))
    for k,v in req.get("noise",{}).items(): merged[k]=merged.get(k,0)+v
    units=req.get("units",{})
    for alias,value in merged.items():
        sheet.set(alias,format_value(value,units.get(alias,"")))
    doc.recompute()
    analysis=doc.getObject(req.get("analysis",""))
    if analysis is None: raise RuntimeError("FEM analysis object not found")
    # FreeCAD FEM's supported solver runner. Existing analysis must contain solver + mesh.
    try:
        from femtools import ccxtools
        solver=next((o for o in analysis.Group if "Solver" in o.TypeId or "Solver" in o.Name),None)
        if solver is None: raise RuntimeError("No CalculiX solver in analysis Group")
        runner=ccxtools.FemToolsCcx(analysis=analysis,solver=solver,test_mode=False)
        runner.setup_working_dir(); runner.setup_ccx()
        prerequisites=runner.check_prerequisites()
        if prerequisites:
            raise RuntimeError("FEM prerequisites failed: %s" % prerequisites)
        runner.purge_results(); runner.write_inp_file(); runner.ccx_run(); runner.load_results()
    except Exception as e: raise RuntimeError("FEM solve failed: "+str(e))
    doc.recompute(); obj=doc.getObject(req.get("metric_object","")); prop=req.get("metric_property","")
    if obj is not None and prop and hasattr(obj,prop): objective=number(getattr(obj,prop))
    else:
        # Generic fallback: maximum magnitude from common result properties.
        results=[o for o in doc.Objects if "Fem::FemResult" in o.TypeId or "Result" in o.Name]
        vals=[]
        for o in results:
            for name in ("MaxVonMises","MaxDisplacement","vonMises","DisplacementLengths"):
                if hasattr(o,name):
                    value=getattr(o,name); vals.extend([number(x) for x in value] if isinstance(value,(list,tuple)) else [number(value)])
        if not vals: raise RuntimeError("Metric property unavailable; specify result object/property")
        objective=max(vals)
    emit({"ok":True,"objective":objective,"parameters":merged})
if __name__=="__main__":
    try:
        with open(sys.argv[-1],encoding="utf-8") as f: main(json.load(f))
    except Exception as e: emit({"ok":False,"error":str(e),"traceback":traceback.format_exc()})

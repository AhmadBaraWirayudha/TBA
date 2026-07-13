"""Launch one real evaluator request and fail unless the final protocol record is ok.

Usage:
  python run_evaluator_smoke_test.py FREECADCMD REQUEST_JSON
This helper does not create or validate a FEM model; the request must reference a
saved model that has already solved successfully in the same FreeCAD build.
"""
import json, os, subprocess, sys

def main(argv):
    if len(argv)!=3:
        print("Usage: python run_evaluator_smoke_test.py FREECADCMD REQUEST_JSON",file=sys.stderr)
        return 2
    command,request=map(os.path.abspath,argv[1:])
    script=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","eval_script.py"))
    for label,path in (("freecadcmd",command),("request",request),("evaluator",script)):
        if not os.path.isfile(path):
            print("ERROR: %s file not found: %s"%(label,path),file=sys.stderr); return 2
    cp=subprocess.run([command,script,request],capture_output=True,text=True)
    lines=[line.strip() for line in cp.stdout.splitlines() if line.strip().startswith("{")]
    if not lines:
        print(cp.stdout); print(cp.stderr,file=sys.stderr)
        print("ERROR: evaluator produced no JSON record",file=sys.stderr); return 1
    try: result=json.loads(lines[-1])
    except Exception as exc:
        print("ERROR: invalid final JSON record: %s"%exc,file=sys.stderr); return 1
    print(json.dumps(result,indent=2,sort_keys=True))
    if cp.returncode!=0:
        print("ERROR: freecadcmd exited with %d"%cp.returncode,file=sys.stderr); return 1
    if not result.get("ok"):
        print("ERROR: evaluator reported failure",file=sys.stderr); return 1
    return 0

if __name__=="__main__": raise SystemExit(main(sys.argv))

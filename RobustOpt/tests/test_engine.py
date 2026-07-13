"""Pure-Python checks; run with: python -m unittest discover tests"""
import builtins, math, os, sys, types, unittest
from unittest import mock
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from OptimizationEngine import orthogonal_array, sn_ratio, Pipeline
from eval_script import format_value
class FakeEvaluator:
    def evaluate(self,p,noise=None):
        noise=noise or {}; y=sum((v-2.0)**2 for v in p.values())+sum(abs(v) for v in noise.values())
        return y,{"ok":True,"objective":y}
class EngineTests(unittest.TestCase):
    def test_arrays(self):
        self.assertEqual(len(orthogonal_array("L9",4)),9)
        self.assertEqual(len(orthogonal_array("L27",8)),27)
        for c in range(4): self.assertEqual(sorted(r[c] for r in orthogonal_array("L9",4)),[0,0,0,1,1,1,2,2,2])
        l27=orthogonal_array("L27",8)
        for a in range(8):
            for b in range(a+1,8):
                counts={(x,y):0 for x in range(3) for y in range(3)}
                for row in l27: counts[(row[a],row[b])]+=1
                self.assertEqual(set(counts.values()),{3})
    def test_sn(self):
        self.assertGreater(sn_ratio([1,1],"smaller"),sn_ratio([2,2],"smaller"))
        self.assertTrue(math.isfinite(sn_ratio([9,10,11],"nominal")))
    def test_unit_formatting(self):
        self.assertEqual(format_value(12.5,"mm"),"12.5 mm")
        self.assertEqual(format_value(12.5,""),"12.5")
    def test_failure_detail_is_logged(self):
        class Failed:
            def evaluate(self,p,noise=None): return 1e30,{"ok":False,"error":"solver failed"}
        messages=[]
        Pipeline(Failed(),log=messages.append)._eval({"x":1})
        self.assertIn("solver failed",messages[0])
    def test_taguchi(self):
        factors=[{"name":"x","min":0,"max":4,"noise":0}]
        p,y=Pipeline(FakeEvaluator()).taguchi(factors,{"array":"L9","noise_levels":1})
        self.assertEqual(p["x"],2)
    def test_pid_reaches_linear_target(self):
        class Linear:
            def evaluate(self,p,noise=None): return p["x"],{"ok":True,"objective":p["x"]}
        factors=[{"name":"x","min":0,"max":4}]
        p,y=Pipeline(Linear()).pid({"x":0},factors,{"parameter":"x","target":2,"kp":1,"ki":0,"kd":0,"iterations":3,"tolerance":1e-9})
        self.assertEqual(p["x"],2); self.assertEqual(y,2)
    def test_random_fallback_when_skopt_missing(self):
        real_import=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name=="skopt" or name.startswith("skopt."): raise ImportError("test")
            return real_import(name,*args,**kwargs)
        factors=[{"name":"x","min":0,"max":4}]
        with mock.patch("builtins.__import__",side_effect=guarded):
            p,y=Pipeline(FakeEvaluator()).bayes(factors,{"x":0},{"iterations":2,"seed":1})
        self.assertGreaterEqual(p["x"],0); self.assertLessEqual(p["x"],4)
    def test_standard_gp_branch_contract(self):
        class Real:
            def __init__(self,lo,hi,name=None): self.low=lo; self.high=hi; self.name=name
        class Optimizer:
            def __init__(self,*a,**k): self.seen=[]
            def ask(self): return [2.0]
            def tell(self,x,y): self.seen.append((x,y))
        skopt=types.ModuleType("skopt"); skopt.Optimizer=Optimizer
        space=types.ModuleType("skopt.space"); space.Real=Real
        factors=[{"name":"x","min":0,"max":4}]
        with mock.patch.dict(sys.modules,{"skopt":skopt,"skopt.space":space}):
            p,y=Pipeline(FakeEvaluator()).bayes(factors,{"x":0},{"iterations":1,"acq":"EI"})
        self.assertEqual(p["x"],2.0); self.assertEqual(y,0.0)
    def test_mcmc_branch_contract(self):
        class Optimizer:
            def __init__(self,*a,**k): self.X=[]; self.y=[]
            def add(self,x,y): self.X.append(x); self.y.append(y)
            def suggest(self): return [2.0]
        module=types.ModuleType("MCMCBayesianOptimizer"); module.MCMCBayesianOptimizer=Optimizer
        factors=[{"name":"x","min":0,"max":4}]
        with mock.patch.dict(sys.modules,{"MCMCBayesianOptimizer":module}):
            p,y=Pipeline(FakeEvaluator()).bayes(factors,{"x":0},{"iterations":1,"mcmc":True})
        self.assertEqual(p["x"],2.0); self.assertEqual(y,0.0)
if __name__=="__main__": unittest.main()

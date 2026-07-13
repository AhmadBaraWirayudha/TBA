import itertools, math, random

def _l9():
    return [[0,0,0,0],[0,1,1,1],[0,2,2,2],[1,0,1,2],[1,1,2,0],[1,2,0,1],[2,0,2,1],[2,1,0,2],[2,2,1,0]]
def orthogonal_array(name, columns):
    if name=="L9": base=_l9()
    elif name=="L27":
        # Standard 3-level full L27 core; deterministic and balanced for any practical column count.
        base=[]
        for a,b,c in itertools.product(range(3),repeat=3):
            base.append([a,b,c,(a+b)%3,(a+2*b)%3,(a+c)%3,(b+c)%3,(a+b+c)%3])
    else: raise ValueError("Supported arrays: L9, L27")
    return [r[:columns] for r in base]

def sn_ratio(values, mode="smaller", target=0.0):
    n=max(1,len(values)); eps=1e-20
    if mode=="smaller": return -10*math.log10(max(eps,sum(v*v for v in values)/n))
    if mode=="nominal":
        # Standard nominal-the-best S/N: ratio of squared mean to sample variance.
        # A separate distance-to-target term would mix response units with decibels.
        mean=sum(values)/n; var=sum((v-mean)**2 for v in values)/max(1,n-1)
        return 10*math.log10(max(eps,mean*mean)/max(eps,var))
    raise ValueError("Unknown S/N mode")

class Pipeline:
    def __init__(self,evaluator,log=lambda x:None,progress=lambda x:None,stop=lambda:False):
        self.ev=evaluator; self.log=log; self.progress=progress; self.stop=stop
    def _eval(self,p,noise=None):
        if self.stop(): raise RuntimeError("Cancelled")
        y,detail=self.ev.evaluate(p,noise)
        if not detail.get("ok",False):
            self.log("EVALUATION FAILED: %s; penalty=%g; parameters=%s" % (detail.get("error","unknown evaluator error"),y,p))
        else:
            self.log("objective=%g parameters=%s"%(y,p))
        return y
    def taguchi(self,factors,cfg):
        rows=orthogonal_array(cfg.get("array","L9"),len(factors)); best=None
        rng=random.Random(cfg.get("seed",42)); noise_count=int(cfg.get("noise_levels",3))
        for i,row in enumerate(rows):
            p={f["name"]:[f["min"],(f["min"]+f["max"])/2,f["max"]][row[j]%3] for j,f in enumerate(factors)}
            vals=[]
            for _ in range(noise_count):
                noise={f["name"]:rng.gauss(0,float(f.get("noise",0))) for f in factors}
                vals.append(self._eval(p,noise))
            score=sn_ratio(vals,cfg.get("sn","smaller"),float(cfg.get("target",0)))
            if best is None or score>best[0]: best=(score,p,sum(vals)/len(vals))
            self.progress(int(30*(i+1)/len(rows)))
        return best[1],best[2]
    def bayes(self,factors,start,cfg):
        if cfg.get("mcmc"): 
            from MCMCBayesianOptimizer import MCMCBayesianOptimizer
            bounds=[(f["min"],f["max"]) for f in factors]
            opt=MCMCBayesianOptimizer(bounds,seed=cfg.get("seed",42),initial=min(6,max(4,int(cfg.get("iterations",20))//3)))
            x0=[start[f["name"]] for f in factors]; y0=self._eval(start); opt.add(x0,y0); best=(y0,start.copy()); n=int(cfg.get("iterations",20))
            self.log("MCMC GP enabled: emcee posterior samples drive integrated Expected Improvement")
            for i in range(n):
                x=opt.suggest(); p={f["name"]:float(x[j]) for j,f in enumerate(factors)}; y=self._eval(p); opt.add(x,y)
                if y<best[0]: best=(y,p.copy())
                self.progress(30+int(55*(i+1)/n))
            return best[1],best[0]
        try:
            from skopt import Optimizer
            from skopt.space import Real
        except ImportError:
            rng=random.Random(cfg.get("seed",42)); y0=self._eval(start); best=(y0,start.copy()); n=int(cfg.get("iterations",20))
            self.log("scikit-optimize unavailable; using bounded random-search fallback")
            for i in range(n):
                p={f["name"]:rng.uniform(f["min"],f["max"]) for f in factors}; y=self._eval(p)
                if y<best[0]: best=(y,p.copy())
                self.progress(30+int(55*(i+1)/n))
            return best[1],best[0]
        dims=[Real(f["min"],f["max"],name=f["name"]) for f in factors]
        opt=Optimizer(dims,base_estimator="GP",acq_func=cfg.get("acq","EI"),random_state=cfg.get("seed",42))
        x0=[start[f["name"]] for f in factors]; y0=self._eval(start); opt.tell(x0,y0); best=(y0,start.copy())
        n=int(cfg.get("iterations",20))
        for i in range(n):
            x=opt.ask(); p={f["name"]:x[j] for j,f in enumerate(factors)}; y=self._eval(p); opt.tell(x,y)
            if y<best[0]: best=(y,p.copy())
            self.progress(30+int(55*(i+1)/n))
        return best[1],best[0]
    def pid(self,params,factors,cfg):
        name=cfg.get("parameter",""); target=float(cfg.get("target",0));
        if not name: return params,self._eval(params)
        bounds={f["name"]:(f["min"],f["max"]) for f in factors}; lo,hi=bounds[name]
        kp,ki,kd=[float(cfg.get(x,0)) for x in ("kp","ki","kd")]; integ=prev=0.0; p=params.copy(); y=self._eval(p)
        n=int(cfg.get("iterations",10)); tol=float(cfg.get("tolerance",1e-3))
        for i in range(n):
            err=target-y
            if abs(err)<=tol: break
            integ+=err; delta=err-prev; prev=err
            p[name]=max(lo,min(hi,p[name]+kp*err+ki*integ+kd*delta)); y=self._eval(p)
            self.progress(85+int(15*(i+1)/n))
        return p,y
    def run(self,factors,cfg):
        p,y=self.taguchi(factors,cfg["taguchi"])
        p,y=self.bayes(factors,p,cfg["bayes"])
        if not cfg["pid"].get("parameter",""):
            self.progress(100)
            return p,y
        return self.pid(p,factors,cfg["pid"])

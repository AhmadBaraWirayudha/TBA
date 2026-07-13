"""Lightweight fully Bayesian GP acquisition using emcee hyperparameter samples."""
import math
import numpy as np

class MCMCBayesianOptimizer:
    def __init__(self, bounds, seed=42, initial=6, walkers=12, steps=120, candidates=256):
        self.bounds=np.asarray(bounds,dtype=float); self.dim=len(bounds); self.rng=np.random.RandomState(seed)
        self.initial=max(initial,4); self.walkers=max(walkers,8); self.steps=max(steps,40); self.candidates=max(candidates,64)
        self.X=[]; self.y=[]
    def _norm(self,X):
        lo=self.bounds[:,0]; span=np.maximum(self.bounds[:,1]-lo,1e-15); return (np.asarray(X)-lo)/span
    def add(self,x,y): self.X.append(np.asarray(x,dtype=float)); self.y.append(float(y))
    def _log_prob(self,theta,X,y):
        # Bounded weak log priors prevent singular/extreme kernels.
        if np.any(theta < [-5,-8,-14]) or np.any(theta > [4,8,1]): return -np.inf
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
        kernel=ConstantKernel(math.exp(theta[1]),constant_value_bounds="fixed")*RBF(math.exp(theta[0]),length_scale_bounds="fixed")+WhiteKernel(math.exp(theta[2]),noise_level_bounds="fixed")
        try:
            gp=GaussianProcessRegressor(kernel=kernel,optimizer=None,normalize_y=True).fit(X,y)
            return float(gp.log_marginal_likelihood())
        except Exception: return -np.inf
    def _samples(self):
        import emcee
        X=self._norm(self.X); y=np.asarray(self.y); ndim=3
        center=np.array([-0.7,0.0,-7.0]); pos=center+0.08*self.rng.randn(self.walkers,ndim)
        sampler=emcee.EnsembleSampler(self.walkers,ndim,self._log_prob,args=(X,y))
        sampler.run_mcmc(pos,self.steps,progress=False)
        discard=min(self.steps//2,self.steps-2); chain=sampler.get_chain(discard=discard,thin=max(1,(self.steps-discard)//20),flat=True)
        return chain[-40:] if len(chain)>40 else chain
    def suggest(self):
        if len(self.X)<self.initial:
            return self.rng.uniform(self.bounds[:,0],self.bounds[:,1])
        from scipy.stats import norm
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
        samples=self._samples(); candidates=self.rng.uniform(self.bounds[:,0],self.bounds[:,1],(self.candidates,self.dim)); C=self._norm(candidates); X=self._norm(self.X); y=np.asarray(self.y); best=np.min(y); total=np.zeros(len(C))
        for theta in samples:
            kernel=ConstantKernel(math.exp(theta[1]),constant_value_bounds="fixed")*RBF(math.exp(theta[0]),length_scale_bounds="fixed")+WhiteKernel(math.exp(theta[2]),noise_level_bounds="fixed")
            gp=GaussianProcessRegressor(kernel=kernel,optimizer=None,normalize_y=True).fit(X,y)
            mu,sigma=gp.predict(C,return_std=True); sigma=np.maximum(sigma,1e-12); z=(best-mu)/sigma
            total += (best-mu)*norm.cdf(z)+sigma*norm.pdf(z)
        return candidates[int(np.argmax(total/max(1,len(samples))))]

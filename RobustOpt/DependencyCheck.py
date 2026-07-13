"""Dependency diagnostics. Installation is explicit; never mutates FreeCAD silently."""
import importlib.util, os, subprocess, sys
PACKAGES = {"numpy":"numpy", "skopt":"scikit-optimize", "emcee":"emcee", "sklearn":"scikit-learn", "scipy":"scipy"}
def missing_packages(include_optional=False):
    names = ["numpy", "skopt"] + (["emcee","sklearn","scipy"] if include_optional else [])
    return [PACKAGES[n] for n in names if importlib.util.find_spec(n) is None]
def install(packages):
    if not packages: return
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + list(packages), creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))

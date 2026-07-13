import os
import FreeCAD as App
import FreeCADGui as Gui

class RunCommand:
    def GetResources(self):
        return {"Pixmap": os.path.join(os.path.dirname(__file__), "Resources", "icons", "RobustOpt.svg"),
                "MenuText": "Run robust optimization", "ToolTip": "Configure and run RobustOpt"}
    def IsActive(self):
        return App.ActiveDocument is not None
    def Activated(self):
        from DependencyCheck import missing_packages
        from TaskPanel import RobustOptDialog
        missing = missing_packages()
        if missing:
            App.Console.PrintWarning("RobustOpt standard-mode dependencies missing: %s. The GP stage may use its documented fallback.\n" % ", ".join(missing))
        RobustOptDialog().exec_()

Gui.addCommand("RobustOpt_Run", RunCommand())

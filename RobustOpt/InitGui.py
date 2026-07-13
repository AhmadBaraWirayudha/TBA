import os
import FreeCADGui as Gui

class RobustOptWorkbench(Gui.Workbench):
    MenuText = "RobustOpt"
    ToolTip = "Robust parametric FEM optimization"
    Icon = os.path.join(os.path.dirname(__file__), "Resources", "icons", "RobustOpt.svg")
    def Initialize(self):
        import Commands
        self.appendToolbar("RobustOpt", ["RobustOpt_Run"])
        self.appendMenu("RobustOpt", ["RobustOpt_Run"])
    def GetClassName(self):
        return "Gui::PythonWorkbench"

Gui.addWorkbench(RobustOptWorkbench())

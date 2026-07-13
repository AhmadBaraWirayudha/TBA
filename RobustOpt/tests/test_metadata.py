"""Repository-level checks that do not require FreeCAD."""
import pathlib, re, unittest, xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parents[1]

class MetadataTests(unittest.TestCase):
    def test_package_xml_is_well_formed(self):
        root=ET.parse(ROOT/"package.xml").getroot()
        ns={"p":"https://wiki.freecad.org/Package_Metadata"}
        self.assertEqual(root.tag,"{%s}package"%ns["p"])
        self.assertEqual(root.findtext("p:name",namespaces=ns),"RobustOpt")
        self.assertEqual(root.findtext("p:content/p:workbench/p:classname",namespaces=ns),"RobustOptWorkbench")
        self.assertEqual(root.findtext("p:content/p:workbench/p:subdirectory",namespaces=ns),"./")
    def test_local_markdown_links_exist(self):
        missing=[]
        for file in ROOT.glob("*.md"):
            text=file.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)",text):
                clean=target.split("#",1)[0]
                if clean and "://" not in clean and not (file.parent/clean).exists():
                    missing.append((file.name,target))
        self.assertEqual(missing,[])
    def test_documented_files_exist(self):
        for name in ("README.md","TUTORIAL.md","ADDENDUM.md","HANDOVER.md","TESTED_ENVIRONMENTS.md","requirements.txt","requirements-mcmc.txt","eval_script.py","LICENSE","tools/validate_with_freecad_python.bat","tools/run_evaluator_smoke_test.py"):
            self.assertTrue((ROOT/name).is_file(),name)
    def test_windows_validation_helper_scope(self):
        text=(ROOT/"tools"/"validate_with_freecad_python.bat").read_text(encoding="utf-8").lower()
        self.assertIn("-m compileall",text)
        self.assertIn("-m unittest discover -s tests -v",text)
    def test_mcmc_direct_dependencies_are_declared(self):
        text=(ROOT/"requirements-mcmc.txt").read_text(encoding="utf-8").lower()
        for package in ("emcee","scikit-learn","scipy"):
            self.assertRegex(text,r"(?m)^%s\s*$"%re.escape(package))
    def test_declared_mit_license_is_complete(self):
        text=(ROOT/"LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License",text)
        self.assertIn("copyright notice and this permission notice shall be included",text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"',text)

if __name__=="__main__": unittest.main()

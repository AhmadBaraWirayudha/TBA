import contextlib, importlib.util, io, pathlib, types, unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("smoke",ROOT/"tools"/"run_evaluator_smoke_test.py")
smoke=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(smoke)

class ToolTests(unittest.TestCase):
    @mock.patch.object(smoke.os.path,"isfile",return_value=True)
    @mock.patch.object(smoke.subprocess,"run")
    def test_smoke_helper_accepts_ok_protocol(self,run,isfile):
        run.return_value=types.SimpleNamespace(stdout='banner\n{"ok":true,"objective":1.2}\n',stderr="",returncode=0)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code=smoke.main(["tool","freecadcmd.exe","request.json"])
        self.assertEqual(code,0)
    @mock.patch.object(smoke.os.path,"isfile",return_value=True)
    @mock.patch.object(smoke.subprocess,"run")
    def test_smoke_helper_rejects_error_protocol(self,run,isfile):
        run.return_value=types.SimpleNamespace(stdout='{"ok":false,"error":"FEM failed"}\n',stderr="",returncode=0)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code=smoke.main(["tool","freecadcmd.exe","request.json"])
        self.assertEqual(code,1)
if __name__=="__main__": unittest.main()

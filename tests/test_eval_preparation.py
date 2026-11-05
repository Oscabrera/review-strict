"""Blind input preparation must preserve raw cases and exclude expected labels."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

EVAL = Path(__file__).resolve().parent / 'evals'

class EvalPreparationTests(unittest.TestCase):
    def test_blind_inputs_preserve_source_without_expected_labels(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)/'blind'
            r = subprocess.run([sys.executable, str(EVAL/'prepare-spec-verification.py'), '--out', str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            corpus = json.loads((EVAL/'spec-verification-cases.json').read_text())['cases']
            manifest = json.loads((out/'manifest.json').read_text())
            self.assertEqual(len(manifest), len(corpus))
            for case in corpus:
                d=out/case['id']
                self.assertEqual(sorted(p.name for p in d.iterdir()), ['source.py','spec.md'])
                self.assertEqual((d/'spec.md').read_text(), case['spec']+'\n')
                self.assertEqual((d/'source.py').read_text(), case['source'])
                digest=hashlib.sha256(((d/'spec.md').read_text()+(d/'source.py').read_text()).encode()).hexdigest()
                self.assertIn({'id':case['id'],'sha256':digest}, manifest)

    def test_review_inputs_preserve_requests_without_expected_labels(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'review'
            r=subprocess.run([sys.executable,str(EVAL/'prepare-spec-verification.py'),'--kind','review','--out',str(out)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            cases=json.loads((EVAL/'review-lessons-cases.json').read_text())['cases']
            for case in cases:
                folder=out/case['id']
                self.assertEqual(sorted(p.name for p in folder.iterdir()),['request.md','source.py'])
                self.assertEqual((folder/'request.md').read_text(),case['request'])
                self.assertEqual((folder/'source.py').read_text(),case['source'])

    def test_rerun_refuses_to_overwrite_evaluator_inputs(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'blind';out.mkdir()
            marker=out/'source.py';marker.write_text('preserve me\n')
            r=subprocess.run([sys.executable,str(EVAL/'prepare-spec-verification.py'),'--out',str(out)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(marker.read_text(),'preserve me\n')
            self.assertEqual(list(out.iterdir()),[marker])

if __name__=='__main__':unittest.main()

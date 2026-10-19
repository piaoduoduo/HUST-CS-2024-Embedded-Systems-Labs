from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('materialize',ROOT/'tools/materialize.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class MaterializeTests(unittest.TestCase):
    def test_utf8_crlf_reconstruction(self):
        before='第一行\r\nkeep\r\nold\r\n'.encode()
        after='第一行\r\nkeep\r\nnew\n'.encode()
        item={'path':'common/a.c','baseSHA256':m.digest(before),'sha256':m.digest(after),'edits':[{'start':2,'end':3,'lines':['new\n']}]}
        self.assertEqual(m.rebuild(before,item),after)
        with self.assertRaises(ValueError):m.rebuild(b'changed',item)
    def test_path_rejection(self):
        for value in ('../file','/absolute','C:/file','a\\b','a/../b','a//b',''):
            with self.subTest(value=value),self.assertRaises(ValueError):m.safe_path(ROOT,value)
    def test_new_file_and_tampered_payload(self):
        item={'path':'main.c','baseSHA256':None,'sha256':m.digest(b'hello\n'),'edits':[{'start':0,'end':0,'lines':['hello\n']}]}
        self.assertEqual(m.rebuild(b'',item),b'hello\n')
        item['edits'][0]['lines']=['changed\n']
        with self.assertRaises(ValueError):m.rebuild(b'',item)
    def test_original_and_existing_output_preserved(self):
        work=ROOT/'.work';work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as td:
            course=Path(td)/'course';course.mkdir()
            original=course/'keep';original.write_bytes(b'original')
            out=Path(td)/'exists';out.mkdir();(out/'keep').write_bytes(b'output')
            with self.assertRaises(ValueError):m.materialize('lab2',course,out)
            self.assertEqual(original.read_bytes(),b'original')
            self.assertEqual((out/'keep').read_bytes(),b'output')
            with self.assertRaises(ValueError):m.materialize('lab2',course,course/'new')
    def test_profile_catalog(self):
        catalog=json.loads((ROOT/'profiles.json').read_text(encoding='utf-8'))
        self.assertEqual(set(catalog),{'lab2','lab3','lab4','v9','v10','lab5','lab6'})
        for name,record in catalog.items():
            data=json.loads(m.safe_path(ROOT,record['path']).read_text(encoding='utf-8'))
            self.assertEqual(name,data['name'])
            self.assertEqual(record['files'],len(data['files']))

if __name__=='__main__':unittest.main()

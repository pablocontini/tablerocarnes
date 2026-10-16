import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from ejecutar_tablero import ejecutar_notebook
from checkpoints import restaurar


class CheckpointsTest(unittest.TestCase):
    def test_exportar_excel_y_archivo_y_reanudar(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'exportar.ipynb'
            excel = root / 'datos.xlsx'
            output = root / 'datos.json'
            cells = [
                {'cell_type': 'code', 'source': [
                    "import pandas as pd\nimport json\ndf = pd.DataFrame({'valor': [7, 8]})\n"
                    f"with pd.ExcelWriter({str(excel)!r}, engine='openpyxl') as writer:\n"
                    "    df.to_excel(writer, index=False)\n"
                    "    _ws = writer.sheets['Sheet1']\n"
                    "    for _row in _ws.iter_rows():\n"
                    "        for _cell in _row:\n"
                    "            _cell.number_format = '0'\n"]},
                {'cell_type': 'code', 'source': ["raise ValueError('pausa de prueba')\n"]},
                {'cell_type': 'code', 'source': [
                    f"with open({str(output)!r}, 'w') as f:\n"
                    "    json.dump(df.to_dict('list'), f)\n"]},
            ]
            path.write_text(json.dumps({'cells': cells}), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(ejecutar_notebook(path, context={}, checkpoint_dir=root), 1)
                stamp = excel.stat().st_mtime_ns
                start, namespace = restaurar(root / 'exportar.pkl', cells, {})
                self.assertEqual(start, 1)
                self.assertNotIn('writer', namespace)
                self.assertNotIn('_ws', namespace)
                pd.testing.assert_frame_equal(namespace['df'], pd.DataFrame({'valor': [7, 8]}))
                cells[1]['source'] = ['assert df.valor.sum() == 15\n']
                path.write_text(json.dumps({'cells': cells}), encoding='utf-8')
                self.assertEqual(ejecutar_notebook(path, reanudar=True, context={}, checkpoint_dir=root), 0)
                _, namespace = restaurar(root / 'exportar.pkl', cells, {})
                self.assertNotIn('f', namespace)
            self.assertEqual(excel.stat().st_mtime_ns, stamp)
            self.assertEqual(json.loads(output.read_text()), {'valor': [7, 8]})

    def test_fallo_correccion_y_reanudacion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'test.ipynb'
            marker = root / 'carga.txt'
            output = root / 'resultado.txt'
            cells = [
                {'cell_type': 'code', 'source': [f"from pathlib import Path\nPath({str(marker)!r}).write_text('cargado')\nx = 7\n"]},
                {'cell_type': 'code', 'source': ['def valor():\n    return x\n']},
                {'cell_type': 'code', 'source': ["x = 999\nraise ValueError('fallo de prueba')\n"]},
                {'cell_type': 'code', 'source': [f"Path({str(output)!r}).write_text(str(valor()))\n"]},
            ]
            path.write_text(json.dumps({'cells': cells}), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(ejecutar_notebook(path, context={'input': 1}, checkpoint_dir=root), 1)
                timestamp = marker.stat().st_mtime_ns
                cells[1]['source'] = ['def valor():\n    return x * 2\n']
                cells[2]['source'] = ['assert x == 7\nx = 8\n']
                path.write_text(json.dumps({'cells': cells}), encoding='utf-8')
                self.assertEqual(ejecutar_notebook(path, reanudar=True, context={'input': 1}, checkpoint_dir=root), 0)
            self.assertEqual(marker.stat().st_mtime_ns, timestamp)
            self.assertEqual(output.read_text(), '16')
            with self.assertRaises(ValueError):
                restaurar(root / 'test.pkl', cells, {'input': 2})
            cells[0]['source'] = ['x = 20\n']
            with self.assertRaises(ValueError):
                restaurar(root / 'test.pkl', cells, {'input': 1})


if __name__ == '__main__':
    unittest.main()

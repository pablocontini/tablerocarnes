"""Regresión del indicador mensual: días con faena sin existencias."""
import ast
import json
from pathlib import Path
import unittest

import pandas as pd


class Indicador16Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'Tablero_Carnes_local.ipynb'
        notebook = json.loads(path.read_text(encoding='utf-8'))
        functions = []
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                functions.extend(node for node in ast.parse(''.join(cell['source'])).body
                                 if isinstance(node, ast.FunctionDef)
                                 and node.name in ('_base_nd', 'calc_ind16'))
        cls.namespace = {'pd': pd}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), cls.namespace)

    def test_planta_con_existencias_sin_faena(self):
        faena = pd.DataFrame({'establecimiento_ruca': [1, 1, 1, 2],
                              'fecha_faena': pd.to_datetime(['2026-01-01', '2026-01-01', '2026-01-02', '2026-01-03'])})
        existencias = pd.DataFrame({'establecimiento_ruca': [1, 3],
                                   'fecha_existencia': pd.to_datetime(['2026-01-01', '2026-01-01'])})
        result = self.namespace['calc_ind16'](faena, existencias, pd.Index([1, 2, 3, 4]))
        self.assertEqual(result.to_dict(), {1: 50.0, 2: 100.0, 3: 'nd', 4: 'nd'})

    def test_sin_faena_y_mas_existencias_que_dias_faenados(self):
        faena = pd.DataFrame({'establecimiento_ruca': [1], 'fecha_faena': pd.to_datetime(['2026-01-01'])})
        existencias = pd.DataFrame({'establecimiento_ruca': [1, 1],
                                   'fecha_existencia': pd.to_datetime(['2026-01-01', '2026-01-02'])})
        result = self.namespace['calc_ind16'](faena, existencias, pd.Index([1]))
        self.assertEqual(result.loc[1], 0.0)
        result = self.namespace['calc_ind16'](faena.iloc[:0], existencias, pd.Index([1]))
        self.assertEqual(result.loc[1], 'nd')


if __name__ == '__main__':
    unittest.main()

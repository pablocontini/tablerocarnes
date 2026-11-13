import tempfile
from pathlib import Path
import unittest

import pandas as pd

from archivos_entrada import detectar_bases, leer_base


class ArchivosEntradaTest(unittest.TestCase):
    def test_detectar_y_concatenar_en_orden_numerico(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for part in [10, 2, 1]:
                pd.DataFrame({'id': [part], 'valor': [7]}).to_csv(root / f'Faena_parte_{part}.csv', sep=';', index=False)
            (root / 'config_parametros_tablero.xlsx').touch()
            (root / '~$Faena.xlsx').touch()
            (root / 'faena_carpeta.csv').mkdir()
            (root / 'desconocido.csv').touch()
            bases, sin_match = detectar_bases(root, {'faena': ['faena']}, ['faena'])
            self.assertEqual(len(bases['faena']), 3)
            self.assertEqual(sin_match, ['desconocido.csv'])
            result = leer_base(bases['faena'])
            self.assertEqual(result.id.tolist(), [1, 2, 10])
            self.assertEqual(result.index.tolist(), [0, 1, 2])

    def test_excel_y_csv_columnas_reordenadas_y_duplicados(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            one, two = root / 'ingresos_1.csv', root / 'ingresos_2.xlsx'
            pd.DataFrame({'id': [1], 'valor': [7]}).to_csv(one, index=False)
            pd.DataFrame({'valor': [7], 'id': [1]}).to_excel(two, index=False, sheet_name='Datos')
            result = leer_base([two, one], sheet_name='Datos')
            self.assertEqual(result.to_dict('list'), {'id': [1, 1], 'valor': [7, 7]})
            self.assertEqual(len(leer_base(one)), 1)
            pd.DataFrame({'id': [2], 'otra': [9]}).to_excel(two, index=False)
            with self.assertRaisesRegex(ValueError, 'Columnas incompatibles'):
                leer_base([one, two])

    def test_opciones_de_excel_y_encabezados_por_parte(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / f'scoring_parte_{i}.xlsx' for i in [1, 2]]
            for i, path in enumerate(paths):
                pd.DataFrame({'id': ['001'], 'valor': [i], 'extra': [0]}).to_excel(
                    path, sheet_name='PADRON CARNES', startrow=4, index=False)
            result = leer_base(paths, sheet_name='PADRON CARNES', skiprows=4,
                               usecols=['id', 'valor'], dtype={'id': str})
            self.assertEqual(result.id.tolist(), ['001', '001'])
            self.assertEqual(result.valor.tolist(), [0, 1])
            result = leer_base(paths, sheet_name='PADRON CARNES', skiprows=5, header=None)
            self.assertEqual(result.shape, (2, 3))


if __name__ == '__main__':
    unittest.main()

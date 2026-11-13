import contextlib
import io
import unittest
from unittest.mock import patch

from ejecutar_tablero import main


class EjecucionTest(unittest.TestCase):
    def test_flujo_completo_reanuda_datos_y_regenera_html(self):
        with patch('sys.argv', ['ejecutar_tablero.py', '--reanudar']), \
                patch('ejecutar_tablero.contexto_ejecucion', return_value={}), \
                patch('ejecutar_tablero.ejecutar_notebook', return_value=0) as ejecutar, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)
        self.assertEqual([call.args[0].name for call in ejecutar.call_args_list],
                         ['Tablero_Carnes_local.ipynb', 'Tablero_Carnes_HTML_local.ipynb'])
        self.assertEqual([call.kwargs['reanudar'] for call in ejecutar.call_args_list], [True, False])

    def test_etapa_html_admite_reanudacion_explicita(self):
        with patch('sys.argv', ['ejecutar_tablero.py', '--etapa', 'html', '--reanudar']), \
                patch('ejecutar_tablero.contexto_ejecucion', return_value={}), \
                patch('ejecutar_tablero.ejecutar_notebook', return_value=0) as ejecutar, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)
        ejecutar.assert_called_once()
        self.assertTrue(ejecutar.call_args.kwargs['reanudar'])


if __name__ == '__main__':
    unittest.main()

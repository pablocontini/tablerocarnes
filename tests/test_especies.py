"""Especies observadas por planta y respaldo del padrón SIOCAL."""
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from especies import asignar_especies_desde_faena


class EspeciesTest(unittest.TestCase):
    def faena(self, registros):
        filas = []
        for registro in registros:
            fila = {
                'establecimiento_ruca': 1,
                'especie': 'Bovinos',
                'fecha_faena': pd.Timestamp('2026-01-01'),
                'cantidad_detalle_corte': 2,
                'eliminada': 0,
            }
            fila.update(registro)
            filas.append(fila)
        return pd.DataFrame(filas)

    def test_faena_reemplaza_declaracion_y_no_muta_padron(self):
        padron = pd.DataFrame({
            'establecimiento_ruca': [1, 2],
            'especies': ['Bovino, Caprino', 'Ovino'],
            'razon_social': ['Planta A', 'Planta B'],
        }, index=[10, 20])
        original = padron.copy(deep=True)
        reporte = self.faena([{'especie': 'Porcinos'}])
        original_faena = reporte.copy(deep=True)

        resultado = asignar_especies_desde_faena(padron, reporte)

        self.assertEqual(resultado['especies'].tolist(), ['Porcino', 'Ovino'])
        self.assertEqual(resultado['fuente_especies'].tolist(), ['Faena', 'Padrón SIOCAL'])
        self.assertEqual(resultado.index.tolist(), [10, 20])
        self.assertEqual(resultado['razon_social'].tolist(), ['Planta A', 'Planta B'])
        assert_frame_equal(padron, original)
        assert_frame_equal(reporte, original_faena)

    def test_multiespecie_normaliza_deduplica_y_ordena(self):
        padron = pd.DataFrame({'establecimiento_ruca': [1], 'especies': ['']})
        reporte = self.faena([
            {'especie': ' Caprinos '},
            {'especie': 'bovinos'},
            {'especie': 'Bovino'},
            {'especie': 'Porcinos'},
            {'especie': 'Ovinos'},
            {'especie': 'Équidos'},
            {'especie': 'AVES'},
            {'especie': 'Bubalinos'},
            {'especie': 'Camélidos'},
            {'especie': 'Conejos y Piliferos'},
            {'especie': None},
            {'especie': '  '},
        ])

        resultado = asignar_especies_desde_faena(padron, reporte)

        self.assertEqual(resultado.loc[0, 'especies'],
                         'Bovino, Ovino, Porcino, Equino, Caprino, Avicola, '
                         'Bubalino, Camelido, Conejos y Piliferos')
        self.assertEqual(resultado.loc[0, 'fuente_especies'], 'Faena')
        # El orden de las filas del reporte no altera el resultado.
        assert_frame_equal(resultado, asignar_especies_desde_faena(padron, reporte.iloc[::-1]))

    def test_excluye_faena_invalida_y_no_agrega_establecimientos(self):
        padron = pd.DataFrame({'establecimiento_ruca': [1, 2, 3],
                               'especies': ['Caprina, Equina', '', None]})
        reporte = self.faena([
            {'eliminada': 1},
            {'eliminada': None},
            {'cantidad_detalle_corte': 0},
            {'cantidad_detalle_corte': -2},
            {'cantidad_detalle_corte': 'no numérico'},
            {'fecha_faena': pd.NaT},
            {'fecha_faena': ''},
            {'fecha_faena': 'fecha inválida'},
            {'establecimiento_ruca': None},
            {'establecimiento_ruca': 'desconocido'},
            {'establecimiento_ruca': 0},
            {'establecimiento_ruca': -1},
            {'establecimiento_ruca': 1.5},
            {'establecimiento_ruca': 2, 'especie': None},
            {'establecimiento_ruca': 3, 'especie': '  '},
            {'establecimiento_ruca': 999, 'especie': 'Porcinos'},
        ])

        resultado = asignar_especies_desde_faena(padron, reporte)

        self.assertEqual(resultado['establecimiento_ruca'].tolist(), [1, 2, 3])
        self.assertEqual(resultado['especies'].tolist(), ['Equino, Caprino', '', ''])
        self.assertEqual(resultado['fuente_especies'].tolist(),
                         ['Padrón SIOCAL', 'Sin datos', 'Sin datos'])

    def test_respaldo_con_reporte_vacio_y_ruca_nullable(self):
        padron = pd.DataFrame({'establecimiento_ruca': pd.Series([1, 2, None], dtype='Int64'),
                               'especies': [' Avícola, Aves ', 'Bovino', '']})
        vacio = self.faena([{}]).iloc[:0]

        resultado = asignar_especies_desde_faena(padron, vacio)

        self.assertEqual(resultado['especies'].tolist(), ['Avicola', 'Bovino', ''])
        self.assertEqual(resultado['fuente_especies'].tolist(),
                         ['Padrón SIOCAL', 'Padrón SIOCAL', 'Sin datos'])
        assert_frame_equal(resultado[padron.columns], padron.assign(
            especies=['Avicola', 'Bovino', '']))

    def test_no_eliminada_admite_los_tipos_del_reporte(self):
        padron = pd.DataFrame({'establecimiento_ruca': list(range(1, 7)),
                               'especies': [''] * 6})
        reporte = self.faena([
            {'establecimiento_ruca': ruca, 'eliminada': valor}
            for ruca, valor in enumerate([0, 0.0, False, ' NO ', 'false', '0'], start=1)
        ])

        resultado = asignar_especies_desde_faena(padron, reporte)

        self.assertEqual(resultado['especies'].tolist(), ['Bovino'] * 6)
        self.assertEqual(resultado['fuente_especies'].tolist(), ['Faena'] * 6)


if __name__ == '__main__':
    unittest.main()

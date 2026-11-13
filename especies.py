"""Especies observadas en faena, con el padrón como respaldo por planta."""
import unicodedata

import pandas as pd


_NOMBRES = {
    'bovino': 'Bovino', 'bovinos': 'Bovino',
    'porcino': 'Porcino', 'porcinos': 'Porcino',
    'ovino': 'Ovino', 'ovinos': 'Ovino',
    'caprino': 'Caprino', 'caprinos': 'Caprino', 'caprina': 'Caprino',
    'equino': 'Equino', 'equinos': 'Equino', 'equina': 'Equino',
    'equido': 'Equino', 'equidos': 'Equino',
    'avicola': 'Avicola', 'ave': 'Avicola', 'aves': 'Avicola',
    'bubalino': 'Bubalino', 'bubalinos': 'Bubalino',
    'camelido': 'Camelido', 'camelidos': 'Camelido',
    'conejo': 'Conejo', 'conejos': 'Conejo',
    'pilifero': 'Pilifero', 'piliferos': 'Pilifero',
}
_ORDEN = ['Bovino', 'Ovino', 'Porcino', 'Equino', 'Caprino', 'Avicola',
          'Bubalino', 'Camelido', 'Conejo', 'Pilifero']


def normalizar_especie(value):
    if pd.isna(value):
        return ''
    label = ' '.join(str(value).split())
    key = ''.join(c for c in unicodedata.normalize('NFKD', label.casefold())
                  if not unicodedata.combining(c))
    # Conservar denominaciones adicionales del reporte sin adivinar su especie.
    return _NOMBRES.get(key, label)


def _unir_especies(values):
    especies = {normalizar_especie(value) for value in values} - {''}
    return ', '.join(sorted(especies, key=lambda value: (
        _ORDEN.index(value) if value in _ORDEN else len(_ORDEN), value)))


def asignar_especies_desde_faena(padron, faena):
    """Devuelve el padrón con especies y fuente, sin agregar establecimientos.

    Usa todo el histórico cargado, sin recortar a los meses del tablero. Solo
    considera faena no eliminada, con fecha y RUCA válidos y cantidad de cortes
    positiva. No exige un divisor de cortes conocido para identificar la especie.
    Si una planta no tiene especies observadas, conserva las del padrón.
    """
    result = padron.copy()
    cantidad = pd.to_numeric(faena['cantidad_detalle_corte'], errors='coerce')
    ruca = pd.to_numeric(faena['establecimiento_ruca'], errors='coerce')
    fecha_valida = pd.to_datetime(faena['fecha_faena'], errors='coerce').notna()
    no_eliminada = (faena['eliminada'].astype('string').str.strip().str.casefold()
                    .isin(['0', '0.0', 'false', 'no']))
    validas = (no_eliminada & cantidad.gt(0) & ruca.gt(0) & ruca.mod(1).eq(0)
               & fecha_valida)
    observadas = faena.loc[validas, ['especie']].copy()
    observadas['establecimiento_ruca'] = ruca.loc[validas]
    nombres = {value: normalizar_especie(value)
               for value in observadas['especie'].dropna().unique()}
    observadas['especie'] = observadas['especie'].map(nombres).fillna('')
    observadas = observadas.loc[observadas['especie'].ne('')].drop_duplicates()
    por_planta = observadas.groupby('establecimiento_ruca')['especie'].agg(_unir_especies)

    respaldo = result['especies'].fillna('').map(lambda value: _unir_especies(str(value).split(',')))
    especies_faena = result['establecimiento_ruca'].map(por_planta)
    result['especies'] = especies_faena.fillna(respaldo)
    result['fuente_especies'] = 'Sin datos'
    result.loc[respaldo.ne(''), 'fuente_especies'] = 'Padrón SIOCAL'
    result.loc[especies_faena.notna(), 'fuente_especies'] = 'Faena'
    return result

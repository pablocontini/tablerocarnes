"""Detección y concatenación de bases divididas en archivos independientes."""
import os
from pathlib import Path
import re
import unicodedata

import pandas as pd


def _slug(value):
    text = unicodedata.normalize('NFKD', str(value).lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in text if not unicodedata.combining(c)))


def _orden_natural(value):
    return tuple((0, int(part)) if part.isdigit() else (1, part.lower())
                 for part in re.split(r'(\d+)', str(value)))


def lista_archivos(paths):
    if isinstance(paths, (str, os.PathLike)):
        return [os.fspath(paths)]
    return [os.fspath(path) for path in paths]


def nombres_archivos(paths):
    return ', '.join(Path(path).name for path in lista_archivos(paths))


def detectar_bases(input_dir, keywords, orden):
    archivos = sorted((p for p in Path(input_dir).iterdir()
                       if p.is_file() and p.suffix.lower() in ('.csv', '.xls', '.xlsx')
                       and not p.name.startswith('~$')
                       and p.name.lower() != 'config_parametros_tablero.xlsx'),
                      key=lambda p: _orden_natural(p.name))
    asignacion, sin_match = {}, []
    prioridad = {base: i for i, base in enumerate(orden)}
    for path in archivos:
        slug = _slug(path.stem)
        scores = {base: max((len(_slug(kw)) for kw in kws if _slug(kw) in slug), default=0)
                  for base, kws in keywords.items()}
        maximum = max(scores.values(), default=0)
        if not maximum:
            sin_match.append(path.name)
            continue
        candidatos = [base for base, score in scores.items() if score == maximum]
        base = min(candidatos, key=lambda name: (prioridad.get(name, len(prioridad)), name))
        asignacion.setdefault(base, []).append(str(path))
    return asignacion, sin_match


def _leer_archivo(path, sheet_name=0, header=0, skiprows=None, dtype=None, usecols=None):
    if Path(path).suffix.lower() == '.csv':
        for sep in (';', ',', '\t'):
            try:
                df = pd.read_csv(path, encoding='latin-1', sep=sep, header=header,
                                 skiprows=skiprows, dtype=dtype, usecols=usecols, low_memory=False)
                if df.shape[1] > 1:
                    return df
            except Exception:
                pass
        return pd.read_csv(path, encoding='latin-1', sep=None, engine='python',
                           header=header, skiprows=skiprows, dtype=dtype, usecols=usecols)
    for engine in ('calamine', None):
        try:
            return pd.read_excel(path, sheet_name=sheet_name, header=header,
                                 skiprows=skiprows, dtype=dtype, usecols=usecols, engine=engine)
        except Exception:
            if engine is None:
                raise


def leer_base(paths, sheet_name=0, header=0, skiprows=None, dtype=None, usecols=None):
    archivos = sorted(lista_archivos(paths), key=_orden_natural)
    if not archivos:
        raise ValueError('La base no tiene archivos asignados.')
    partes = []
    for path in archivos:
        try:
            df = _leer_archivo(path, sheet_name, header, skiprows, dtype, usecols)
        except Exception as exc:
            raise ValueError(f'No se pudo leer la parte {path}: {exc}') from exc
        if partes and set(df.columns) != set(partes[0].columns):
            faltan = list(partes[0].columns.difference(df.columns))
            sobran = list(df.columns.difference(partes[0].columns))
            raise ValueError(f'Columnas incompatibles en {path} respecto de {archivos[0]}. '
                             f'Faltan: {faltan}. Sobran: {sobran}.')
        partes.append(df)
    if len(partes) == 1:
        return partes[0]
    combined = pd.concat(partes, ignore_index=True)
    print(f'Base concatenada: {len(partes)} archivos, {len(combined):,} filas ({nombres_archivos(archivos)})')
    return combined

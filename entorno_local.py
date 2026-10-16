"""Rutas y validaciones compartidas por el notebook y el ejecutor local."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent


def archivo_config():
    path = Path(os.environ.get('TABLERO_CONFIG', PROJECT_DIR / 'input' / 'config_parametros_tablero.xlsx')).expanduser()
    if not path.is_absolute():
        path = PROJECT_DIR / path
    if not path.is_file():
        raise FileNotFoundError(
            f'Falta el Excel de parámetros: {path}\n'
            'Copiá config_parametros_tablero.xlsx a input/ o usá --config en el ejecutor.'
        )
    return str(path)


def ruta_local(valor, parametro):
    override = os.environ.get(f'TABLERO_{parametro}')
    raw = str(override or valor).strip()
    if not override and raw.startswith('/content/'):
        raw = 'input' if parametro == 'INPUT_DIR' else 'output'
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = PROJECT_DIR / path
    if parametro == 'INPUT_DIR' and not path.is_dir():
        raise FileNotFoundError(f'No existe la carpeta de datos: {path}')
    return str(path.resolve())

"""Ejecuta los notebooks locales de datos y HTML, sin servidor Jupyter."""
import argparse
import json
import os
from pathlib import Path
import sys
from checkpoints import guardar, restaurar
from entorno_local import PROJECT_DIR, archivo_config, ruta_local


def contexto_ejecucion():
    import pandas as pd
    config = Path(archivo_config())
    rutas_df = pd.read_excel(config, sheet_name='Rutas')
    rutas = dict(zip(rutas_df['Parametro'], rutas_df['Valor']))
    input_dir = Path(ruta_local(rutas['INPUT_DIR'], 'INPUT_DIR'))
    output_dir = ruta_local(rutas['OUTPUT_DIR'], 'OUTPUT_DIR')
    def firma(path):
        stat = path.stat()
        return (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    return {'config': firma(config), 'input': sorted(firma(p) for p in input_dir.iterdir()
            if p.is_file() and not p.name.startswith('~$')), 'output': output_dir,
            'python': sys.version, 'pandas': pd.__version__}


def main():
    # Algunas consolas Windows no pueden representar los emojis del notebook.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(errors='replace')
    parser = argparse.ArgumentParser(description='Generar Excel, JSON y HTML del Tablero de Carnes.')
    parser.add_argument('--config', help='Ruta al Excel de parámetros.')
    parser.add_argument('--input-dir', help='Carpeta de bases de datos; reemplaza la ruta del Excel.')
    parser.add_argument('--output-dir', help='Carpeta de resultados; reemplaza la ruta del Excel.')
    parser.add_argument('--etapa', choices=['todo', 'datos', 'html'], default='todo',
                        help='todo: datos y HTML; datos: solo Notebook 1; html: solo Notebook 2.')
    parser.add_argument('--reanudar', action='store_true', help='Continuar desde el último checkpoint disponible.')
    args = parser.parse_args()
    for key, value in [('CONFIG', args.config), ('INPUT_DIR', args.input_dir), ('OUTPUT_DIR', args.output_dir)]:
        if value:
            os.environ[f'TABLERO_{key}'] = str(Path(value).expanduser().resolve())
    notebooks = {
        'datos': ['Tablero_Carnes_local.ipynb'],
        'html': ['Tablero_Carnes_HTML_local.ipynb'],
        'todo': ['Tablero_Carnes_local.ipynb', 'Tablero_Carnes_HTML_local.ipynb'],
    }
    try:
        context = contexto_ejecucion()
    except Exception as exc:
        print(f'Error de configuración: {exc}', file=sys.stderr)
        return 1
    for filename in notebooks[args.etapa]:
        result = ejecutar_notebook(Path(__file__).with_name(filename), reanudar=args.reanudar, context=context)
        if result:
            return result
    print('\nProceso finalizado.')
    return 0


def ejecutar_notebook(notebook_path, reanudar=False, context=None, checkpoint_dir=None):
    print(f'\nNotebook: {notebook_path.name}', flush=True)
    notebook = json.loads(notebook_path.read_text(encoding='utf-8'))
    namespace = {'__name__': '__main__'}
    checkpoint = Path(checkpoint_dir or PROJECT_DIR / '.checkpoints') / (notebook_path.stem + '.pkl')
    start = 0
    if reanudar and checkpoint.exists():
        try:
            start, namespace = restaurar(checkpoint, notebook['cells'], context)
        except Exception as exc:
            print(f'No se pudo reanudar: {exc}', file=sys.stderr)
            return 1
        if start >= len(notebook['cells']):
            print('Este notebook ya terminó; se conserva su resultado.', flush=True)
            return 0
        print(f'Estado recuperado. Próxima celda: {start + 1}.', flush=True)
    else:
        # Invalidar un estado anterior al iniciar una ejecución nueva.
        checkpoint.unlink(missing_ok=True)
        if reanudar:
            print('Sin checkpoint para este notebook; se ejecutará desde el inicio.', flush=True)
    for index, cell in enumerate(notebook['cells']):
        if index < start:
            continue
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        if not source.strip():
            continue
        print(f'\nEjecutando celda {index + 1}...', flush=True)
        try:
            exec(compile(source, f'{notebook_path.name}:celda_{index + 1}', 'exec'), namespace)
        except Exception as exc:
            print(f'\nError en celda {index + 1}: {exc}', file=sys.stderr)
            if checkpoint.exists():
                print('Para continuar: repetí el comando agregando --reanudar.', file=sys.stderr)
            return 1
        try:
            sources = {i: ''.join(c['source']) for i, c in enumerate(notebook['cells'][:index + 1])
                       if c['cell_type'] == 'code'}
            guardar(checkpoint, {'next_cell': index + 1, 'namespace': namespace,
                                  'sources': sources, 'context': context})
        except Exception as exc:
            print(f'No se pudo guardar el checkpoint después de celda {index + 1}: {exc}', file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

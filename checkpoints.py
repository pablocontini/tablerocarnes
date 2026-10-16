"""Persistencia atómica del estado de ejecución de un notebook local."""
import ast
import io
import os
import types
from pathlib import Path

import cloudpickle
import pandas as pd
from openpyxl.cell.cell import Cell, MergedCell
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet


def _recurso_exportacion(value):
    if isinstance(value, (io.IOBase, pd.ExcelWriter, Workbook, Worksheet, Cell, MergedCell)):
        return True
    if isinstance(value, (tuple, list)):
        return any(isinstance(item, (Cell, MergedCell)) for item in value)
    return False


def guardar(path, state):
    # Los bloques with dejan writer/f y los objetos auxiliares de openpyxl
    # en el namespace. Los archivos ya exportados se mantienen en disco.
    state = dict(state)
    state['namespace'] = {name: value for name, value in state['namespace'].items()
                          if not _recurso_exportacion(value)}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    try:
        with temporary.open('wb') as stream:
            cloudpickle.dump(state, stream, protocol=5)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def restaurar(path, cells, context):
    with Path(path).open('rb') as stream:
        state = cloudpickle.load(stream)
    if state['context'] != context:
        raise ValueError('Cambiaron la configuración, las rutas o los archivos de input. Ejecutá sin --reanudar.')
    namespace = state['namespace']
    # cloudpickle puede reconstruir un diccionario global separado por función.
    # Reunificarlos para que las próximas celdas actualicen las mismas variables.
    for name, value in list(namespace.items()):
        if isinstance(value, types.FunctionType) and value.__module__ == namespace.get('__name__'):
            function = types.FunctionType(value.__code__, namespace, value.__name__, value.__defaults__, value.__closure__)
            function.__kwdefaults__ = value.__kwdefaults__
            function.__annotations__ = value.__annotations__
            function.__dict__.update(value.__dict__)
            namespace[name] = function
    for index, previous in state['sources'].items():
        current = ''.join(cells[index]['source']) if index < len(cells) and cells[index]['cell_type'] == 'code' else ''
        if current == previous:
            continue
        old_tree, new_tree = ast.parse(previous), ast.parse(current)
        def outside_functions(tree):
            return [ast.dump(node) for node in tree.body if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        old_names = {node.name for node in old_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        new_functions = [node for node in new_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if outside_functions(old_tree) != outside_functions(new_tree) or old_names != {node.name for node in new_functions}:
            raise ValueError(f'Cambió la celda ya ejecutada {index + 1}. Ejecutá sin --reanudar para recalcular sus datos.')
        # Actualizar funciones corregidas sin volver a cargar las bases.
        exec(compile(ast.Module(body=new_functions, type_ignores=[]), f'celda_{index + 1}', 'exec'), namespace)
    return state['next_cell'], namespace

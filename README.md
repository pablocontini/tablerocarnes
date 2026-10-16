# Tablero de Carnes local

Adaptación de `Notebook_1 (1).ipynb` y `notebook_2_1.ipynb` para Windows con Python 3.12. El primero genera el Excel y el JSON; el segundo genera el HTML con las pestañas Control, Macro y Planta. Conserva los cálculos originales, elimina Google Drive y las instalaciones dentro de las celdas, y limpia las salidas guardadas.

## Instalación

Abrí PowerShell en esta carpeta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Archivos necesarios

Copiá a `input/` el Excel original `config_parametros_tablero.xlsx` y las bases CSV, XLS o XLSX. El Excel debe conservar las hojas `Indicadores_Semaforo`, `Grupos`, `Parametros_Generales`, `Rutas` y `Meses_Procesar`. Los valores de negocio no se inventan: este repositorio no incluye una plantilla con umbrales de ejemplo.

Las bases esperadas son autorizaciones, capacidad de cámaras/corrales, existencias, faena, ingresos, tipificación, tipificadores habilitados, SIGSA, padrón SIOCAL, padrón SIGICA, scoring/inspecciones y habilitación de faena. Se detectan por nombre; si hace falta, ajustá `ASIGNACION_MANUAL` en el primer notebook. Se mantienen las hojas y columnas exigidas por el original, incluida `PADRON CARNES` del archivo de scoring. Los archivos actualmente cargados en `input/` se detectan sin asignaciones manuales.

En la hoja `Rutas`, usá `input` y `output` para `INPUT_DIR` y `OUTPUT_DIR`, o rutas absolutas de Windows. Las rutas antiguas que empiezan con `/content/` se convierten automáticamente a esas carpetas locales. Las rutas relativas del Excel se resuelven desde la carpeta del proyecto. Se conservan `NOMBRE_EXCEL_SALIDA`, `NOMBRE_JSON_SALIDA` y `NOMBRE_HTML_SALIDA`. El segundo notebook usa la misma carpeta de salida para leer sus entradas y guardar el HTML.

## Ejecutar por consola

```powershell
.\.venv\Scripts\python.exe ejecutar_tablero.py
```

Ejecuta ambos notebooks en orden y se detiene si alguna etapa falla. Con la configuración actual genera `output/tablero_fiscalizacion_indicadores.xlsx`, `output/datos_tablero.json` y `output/Tablero_Carnes_Unificado.html`. Abrí el HTML en tu navegador al terminar.

Para ejecutar solo una etapa:

```powershell
# Generar Excel y JSON desde las bases:
.\.venv\Scripts\python.exe ejecutar_tablero.py --etapa datos
# Regenerar HTML desde el Excel y JSON existentes:
.\.venv\Scripts\python.exe ejecutar_tablero.py --etapa html
```

El HTML incluye los datos y el logo. Conserva las referencias del original a Chart.js, SheetJS y Google Fonts por internet; los gráficos y la descarga de Excel requieren que esas bibliotecas se carguen. No requiere Google Drive ni un servidor de Colab.

## Continuar después de un error

El ejecutor guarda automáticamente un checkpoint después de cada celda de código exitosa en `.checkpoints/`. Si una celda falla o cerrás la consola, podés continuar con:

```powershell
.\.venv\Scripts\python.exe ejecutar_tablero.py --reanudar
```

Se recuperan las variables, funciones y tablas de la última celda guardada, y se repite la siguiente celda. Los cambios parciales de la celda fallida se descartan. Si el primer notebook ya terminó, se continúa con el segundo. Conservá los mismos argumentos `--config`, `--input-dir`, `--output-dir` y `--etapa` que usaste al iniciar.

Podés corregir la celda pendiente y también los cuerpos de funciones de celdas ya ejecutadas: el ejecutor actualiza esas funciones al recuperar el estado. Cambiar otros cálculos anteriores, el Excel de configuración o los archivos de entrada requiere comenzar nuevamente sin `--reanudar`. La detección de cambios en archivos usa sus nombres, tamaños y fechas de modificación. Si borrás o modificás los resultados, volvé a ejecutar la etapa correspondiente sin `--reanudar`.

Los checkpoints incluyen los datos en memoria, por lo que pueden ocupar varios GB y agregar tiempo de escritura. La actualización es atómica y mantiene una sola versión por notebook; durante el guardado se necesita espacio para la versión anterior y la nueva. No se incluyen en Git.

La ejecución que falló antes de agregar esta función no tiene checkpoint: necesitás ejecutar una vez desde el inicio para empezar a guardar estados. Esta función se aplica al ejecutor por consola; Jupyter sigue usando su propio kernel.

También podés indicar otras ubicaciones (las rutas relativas de estos argumentos se resuelven desde la consola):

```powershell
.\.venv\Scripts\python.exe ejecutar_tablero.py --config "D:\datos\config_parametros_tablero.xlsx" --input-dir "D:\datos\bases" --output-dir "D:\datos\resultados"
```

## Usar Jupyter

```powershell
.\.venv\Scripts\python.exe -m jupyterlab
```

Abrí `Tablero_Carnes_local.ipynb` y ejecutá todas las celdas en orden. Después abrí `Tablero_Carnes_HTML_local.ipynb` y ejecutá todas sus celdas. Si editás parámetros o datos, reiniciá los kernels y ejecutá todo nuevamente. Podés configurar otras rutas mediante las variables `TABLERO_CONFIG`, `TABLERO_INPUT_DIR` y `TABLERO_OUTPUT_DIR` antes de cargar los parámetros en cada notebook.

## Límites del notebook original

El loop mensual deja los indicadores 12 (entropía) y 14 (cupo) como pendientes: el JSON no calcula sus valores mensuales. El original también pide validar los indicadores 04, 05 y 15. La adaptación conserva estos comportamientos; los cálculos del Excel y del JSON usan ventanas distintas.

Se verificaron la lectura del Excel de configuración, la detección de las 12 bases y la generación del HTML con un Excel y un JSON mínimos de prueba en una carpeta temporal. Esa prueba comprueba la integración, pero no valida los cálculos ni el funcionamiento de los gráficos en el navegador con los datos reales.

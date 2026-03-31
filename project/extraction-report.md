# Fases 2/3/6 — Extracción de contenido, imágenes y validación

Esta fase quedó automatizada en `project/scripts/clone_imaginaits.py`.

## Extracción por URL
Por cada página detectada, el script extrae:
- título (`<title>`)
- headings (`h1..h4`)
- CTAs (`<button>`)
- enlaces (`<a href>`)
- imágenes desde:
  - `<img src>`
  - `srcset`
  - `<picture><source>`
  - lazy loading (`data-src`, `data-lazy-src`, `data-original`, `data-srcset`)
  - `background-image` en estilos inline

## Asignación y descarga
- Convierte rutas relativas a absolutas.
- Intenta descargar cada imagen a `project/assets/images`.
- Si falla, registra: `IMAGEN NO DISPONIBLE – REVISIÓN MANUAL`.

## Reportes de salida
- `project/data/pages.json` (contenido estructurado por página)
- `project/data/image-validation.csv`

Formato CSV de validación:

`Página | Sección | Imagen original | Estado`

Estados esperados:
- `correcta`
- `faltante`
- `error`

# ImaginaITS Clone (pipeline de clonación)

Este repositorio contiene una base frontend + un pipeline automatizado para clonar de forma estructural y visual la web origen:

- Web principal: https://imaginaits.com/
- Sitemap objetivo: https://www.imaginaits.com/sitemap.xml

## Estructura

- `pages/`: páginas manuales y volcado espejo (`pages/mirror`)
- `components/`: header/footer reutilizables
- `assets/images/`: imágenes descargadas de origen + fallback
- `styles/`: estilos globales de la maqueta
- `scripts/`: automatización de descubrimiento/extracción
- `data/`: reportes generados (arquitectura, páginas, validación)

## Clonación completa (Fases 1–6)

```bash
python project/scripts/clone_imaginaits.py --root project
```

Qué hace el script:
1. Intenta leer sitemap (`www`, raíz y `wp-sitemap`).
2. Si sitemap falla, usa fallback de enlaces detectados en home.
3. Para cada URL:
   - vuelca HTML original en `pages/mirror/<slug>.html`
   - extrae título, headings, botones CTA, enlaces e imágenes
   - detecta imágenes en `img/src`, `srcset`, `picture/source`, lazy attrs y `background-image` inline
4. Descarga imágenes reales en `assets/images/`.
5. Genera reportes:
   - `data/architecture.json`
   - `data/pages.json`
   - `data/image-validation.csv` (`correcta`, `faltante`, `error`)

## Regla de fallback visual

Si una imagen no es accesible, se registra exactamente:

`IMAGEN NO DISPONIBLE – REVISIÓN MANUAL`

## Estado en este entorno

En esta sesión, las descargas HTTP directas contra el origen fallaron por túnel/proxy (`403`). El pipeline queda listo para ejecutarse en CI/local con salida de red estándar para obtener clon 1:1 con binarios reales.

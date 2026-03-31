# Fase 1 — Descubrimiento de arquitectura

Esta fase quedó automatizada en `project/scripts/clone_imaginaits.py`.

## Fuente de descubrimiento
El script intenta, por orden:
1. `https://www.imaginaits.com/sitemap.xml`
2. `https://imaginaits.com/sitemap.xml`
3. `https://imaginaits.com/wp-sitemap.xml`
4. Fallback a enlaces detectados en home (`https://imaginaits.com/`)

## Salida jerárquica
La jerarquía final se serializa en:
- `project/data/architecture.json`

Con claves:
- `home`
- `paginas_principales`
- `categorias`
- `landings`

> Nota: en este entorno no se pudo resolver el sitemap por restricciones de red del túnel. El pipeline queda preparado para ejecutarse fuera de este bloqueo.

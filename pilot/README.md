# Pilot

Este directorio contiene un piloto estatico del observatorio.

## Archivos

- `index.html`
- `styles.css`
- `app.js`
- `data/*.json`

## Como regenerar datos

Ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\scripts\build_pilot_data.ps1"
```

## Como abrirlo en Chrome

No conviene abrir `index.html` por `file://` porque Chrome suele bloquear los `fetch()` a JSON locales.

Levanta un servidor local con:

```cmd
C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\start-pilot.cmd
```

Y luego abre:

```text
http://127.0.0.1:4173
```

## Que muestra hoy

- resumen general de la base canónica
- explorador de entidades con filtros
- ficha de entidad
- top inversores
- top startups
- cola de revisión

## Limites actuales

- no tiene todavía clustering visual
- no tiene mapa geográfico
- no tiene capa de demanda ni ESOs
- funciona sobre JSON estático generado desde la base canónica actual

# Merge Review Notes

## Como Leer Esto

Los merges en [merge_suggestions.csv](C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\merge_suggestions.csv) son sugerencias, no verdad canonica.

Regla sugerida:

- `0.97+`: merge casi seguro
- `0.93-0.96`: merge probable, revisar branding o naming historico
- `<0.93`: no merge automatico

## Casos Claros Para Merge

- `Stämm` y `StÃ¤mm`
- `DraperCygnus` y `Draper Cygnus`
- `WerkénVac`, `Werken Vac` y `WerkenVac`
- `Onco Precision` y `OncoPrecision`
- `Novo Space` y `NovoSpace`
- `BreakPET` y `Break Pet`
- `Feed Vax` y `Feedvax`

## Casos De Calidad Que Conviene Marcar

- `Kigui` tiene mismatch de codificacion entre fuentes: `Kigui` vs `KigÃ¼i`
- `Sillicon Catalyst` parece typo y deberia revisarse contra `Silicon Catalyst`

## Casos Relacionados Pero No Equivalentes

Estos no deberian mergearse automaticamente:

- `SOSV` vs `SOSV_IndieBio`
  pueden estar relacionados, pero uno parece fondo/plataforma y el otro marca o programa especifico

- `Dragones` vs `DragonesVP`
  pueden ser la misma organizacion con naming abreviado, pero tambien podria haber diferencia entre firma y vehiculo

- `IndieBio` vs `SOSV_IndieBio`
  probablemente convenga modelarlo como relacion organizacional o alias controlado, no como merge directo sin revisar

- `The Ganesha Lab`
  hoy aparece solo en una fuente, asi que no hay merge pero si faltan aliases o enriquecimiento

## Nota Importante

Aunque el archivo de merges ya esta filtrado, sigue siendo una lista de sugerencias.

No conviene ejecutar merges en bloque sin una pasada minima de validacion, sobre todo en:

- inversores con naming abreviado
- programas vs fondos
- marcas vs entidades legales

# appmemoria

Aplicación PyShiny para observar, analizar, experimentar, operar y visualizar
el sistema de memoria investigativa.

## Principios

- Modularidad.
- Agnosticismo respecto de proveedores.
- Trazabilidad.
- Separación entre UI, servicios, dominio e infraestructura.
- Integración futura con `memory_core` mediante contratos.

## Estado

Fase 5.1 — shell inicial con Visión general, Memoria episódica y Diagnóstico.
Todavía no se conectan proveedores externos ni `memory_core`.

## Ejecución

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
shiny run --reload --port 8010 app.py
```

Abrir <http://127.0.0.1:8010>.

## Configuración

La aplicación lee directamente estas variables de entorno opcionales:

- `APPMEMORIA_ENV`, con valor predeterminado `local`.
- `APPMEMORIA_DEBUG`, con valor predeterminado `true`.

`.env.example` documenta los valores, pero la aplicación todavía no carga
archivos `.env` automáticamente.

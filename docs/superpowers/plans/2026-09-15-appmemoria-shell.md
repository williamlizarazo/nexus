# appmemoria Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un shell PyShiny modular, ejecutable y desacoplado de proveedores.

**Architecture:** `app.py` compone configuración, dependencias y servidor. Cada módulo PyShiny consume un servicio aislado y recibe el mismo contenedor `AppDependencies` mediante inyección explícita.

**Tech Stack:** Python 3.11, Shiny for Python 1.8.0, `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-15-appmemoria-shell-design.md`

## Global Constraints

- Usar exactamente `shiny==1.8.0`.
- No conectar Supabase, Qdrant, OpenAI ni `memory_core`.
- No inicializar Git ni crear commits.
- Mantener UI, servicios y composición en capas separadas.

---

### Task 1: Núcleo y servicios

**Files:**
- Create: `tests/test_core_services.py`
- Create: `core/config.py`, `core/dependencies.py`, `core/memory_registry.py`
- Create: `services/overview_service.py`, `services/episodic_service.py`, `services/diagnostics_service.py`

**Interfaces:**
- Produces: `load_config() -> AppConfig`, `build_dependencies(AppConfig) -> AppDependencies`, `list_memory_modules()`, y los tres servicios.

- [ ] Escribir pruebas que exijan valores predeterminados/configurables, cinco dependencias inicialmente nulas, estado episódico y diagnóstico.
- [ ] Ejecutar `python -m unittest tests.test_core_services -v` y confirmar fallo por módulos ausentes.
- [ ] Implementar el código mínimo descrito en la especificación.
- [ ] Repetir la prueba y confirmar que pasa.

### Task 2: Módulos y composición

**Files:**
- Create: `tests/test_app_composition.py`
- Create: `modules/{overview,episodic,diagnostics}/{ui.py,server.py}`
- Create: `ui.py`, `server.py`, `app.py`

**Interfaces:**
- Consumes: `AppDependencies` y los tres servicios de Task 1.
- Produces: `overview_ui`, `episodic_ui`, `diagnostics_ui`, `create_server`, `app_ui`, `app`.

- [ ] Escribir pruebas que exijan IDs namespaced distintos, shell con las tres vistas y una aplicación importable.
- [ ] Ejecutar `python -m unittest tests.test_app_composition -v` y confirmar fallo por módulos ausentes.
- [ ] Implementar módulos, shell y composition root mínimos.
- [ ] Repetir la prueba y confirmar que pasa.

### Task 3: Empaquetado y operación

**Files:**
- Create: `www/css/app.css`, `.env.example`, `.gitignore`, `requirements.txt`, `README.md`
- Create: archivos `__init__.py` y directorios reservados indicados en la especificación.

**Interfaces:**
- Produces: instalación reproducible y comando `shiny run --port 8010 app.py`.

- [ ] Añadir los archivos operativos y CSS mínimo.
- [ ] Crear `.venv` con Python 3.11 e instalar `requirements.txt`.
- [ ] Ejecutar toda la suite con `.venv\\Scripts\\python -m unittest discover -s tests -v`.
- [ ] Ejecutar `compileall` e importar `app`.
- [ ] Arrancar la app, solicitar `http://127.0.0.1:8010` y comprobar respuesta HTTP.
- [ ] Confirmar que el código no importa proveedores externos.

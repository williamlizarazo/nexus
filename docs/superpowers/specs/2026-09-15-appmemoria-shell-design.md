# Diseño del shell inicial de appmemoria

## Objetivo

Crear un checkpoint mínimo y ejecutable de `appmemoria` con PyShiny 1.8.0,
sin conectar `memory_core` ni proveedores externos.

## Arquitectura

`app.py` será el composition root: carga `AppConfig`, construye un único
`AppDependencies` vacío, crea el servidor y expone `shiny.App`. La UI se divide
en tres módulos namespaced (`overview`, `episodic` y `diagnostics`). Cada
servidor de módulo recibe las dependencias por parámetro y consume únicamente
su servicio; ningún módulo conoce adaptadores concretos.

El registro de memorias contiene inicialmente solo la memoria episódica. Los
campos de infraestructura permanecen en `None`, y Diagnóstico los representa
como no disponibles.

## Interfaz

La aplicación usa `ui.page_navbar()` con sidebar global, navegación a Visión
general, Memoria episódica y Diagnóstico, y CSS externo. El sidebar muestra
selectores inertes de proyecto y actor para establecer el futuro contexto
global sin realizar consultas.

## Validación

Las pruebas unitarias cubren carga de configuración, dependencias desconectadas,
estados de servicios y registro. Pruebas de integración comprueban namespaces
independientes, ensamblaje con una misma instancia de dependencias e importación
de la aplicación. La validación final incluye tests, `compileall`, importación,
arranque HTTP local y búsqueda de referencias prohibidas a proveedores.

## Fuera de alcance

No se conectan Supabase, Qdrant, OpenAI ni `memory_core`. Tampoco se inicializa
Git ni se crea un commit, por decisión expresa del usuario.

# Directorio organizacional administrativo

## Objetivo

Incorporar en `appmemoria` un directorio organizacional de solo lectura que
permita a los administradores consultar usuarios, roles funcionales y
pertenencias organizacionales. La interfaz debe consumir un contrato de
`memory_core`; no debe conocer tablas, vistas ni detalles de Supabase.

## Alcance

La implementación atraviesa dos repositorios locales:

- `memory_core`: modelo canónico, contrato del repositorio y adaptador de
  lectura para Supabase.
- `appmemoria`: service, presenter, módulo PyShiny, integración con el shell y
  autorización administrativa.

No se creará ni modificará SQL. Las tablas, relaciones, vista y políticas RLS
ya existen en Supabase. Tampoco se añadirán operaciones de escritura al nuevo
directorio.

## Autorización

El directorio es exclusivo para actores cuyo `AppActor.is_admin` sea
verdadero. La restricción se aplica en dos límites:

1. `app_shell_ui` no construye la pestaña para un actor `viewer`.
2. `organizational_directory_server` comprueba `is_admin()` antes de invocar
   el service o renderizar datos.

Ocultar la pestaña no se considera un control suficiente. Un cambio posterior
en la navegación no debe permitir que una sesión `viewer` consulte el
repositorio.

Para transportar la autorización, `app_root_ui` y `app_shell_ui` recibirán un
indicador `is_admin` con valor predeterminado `False`.
`root_ui_for_auth_state` derivará el valor exclusivamente del actor almacenado
en `AuthSessionState`.

## Modelo canónico de `memory_core`

Se creará
`src/memory_core/domain/organization_directory_entry.py` con el siguiente
modelo inmutable:

```python
@dataclass(frozen=True, slots=True)
class OrganizationDirectoryEntry:
    user_id: str
    email: str
    full_name: str | None
    functional_role: str | None
    user_status: str
    unit_id: str | None = None
    unit_name: str | None = None
    unit_type: str | None = None
    is_primary: bool = False
```

Cada instancia representa una fila de la vista. Por eso un mismo usuario puede
tener cero, una o varias pertenencias sin introducir estructuras anidadas en
el contrato de persistencia.

## Contrato y adaptador Supabase

`OrganizationDirectoryRepository` conservará todos sus métodos actuales y
añadirá:

```python
def list_directory_entries(self) -> list[OrganizationDirectoryEntry]:
    ...
```

`SupabaseOrganizationDirectoryRepository` implementará el método consultando
únicamente `memory_organizational_directory_v`. Seleccionará explícitamente
`user_id`, `email`, `full_name`, `functional_role`, `user_status`, `unit_id`,
`unit_name`, `unit_type` e `is_primary`, y ordenará por `full_name`.

El adaptador convertirá identificadores presentes a `str`, preservará como
`None` los campos opcionales, usará `active` cuando `user_status` esté vacío y
usará `False` cuando `is_primary` no esté presente. Una respuesta sin datos
producirá una lista vacía. Las excepciones del cliente Supabase no se
convertirán en una lista vacía, porque eso ocultaría una falla operativa.

## Service de `appmemoria`

`OrganizationalDirectoryService` dependerá solamente de `AppDependencies` y
del contrato expuesto como `organization_directory_repository`.

```python
def list_entries(self) -> tuple[OrganizationDirectoryEntry, ...]:
    ...
```

Cuando no exista repositorio configurado devolverá `()`. Cuando exista,
devolverá una tupla con el resultado de `list_directory_entries()`. No conocerá
Supabase ni nombres de vistas.

## Presentación y agrupación

`OrganizationalDirectoryPresenter` agrupará las entradas por `user_id` y
devolverá una fila de tabla por usuario con estas columnas exactas:

- `Nombre`
- `Correo`
- `Rol funcional`
- `Magistratura / Dirección`
- `Principal`
- `Estado`

Las reglas serán:

- `Nombre` usa `full_name`; si está vacío, usa el correo.
- `Rol funcional` queda vacío cuando no existe.
- Una entrada sin unidad no genera texto de pertenencia.
- Las pertenencias se deduplican y se ordenan de forma estable por tipo y
  nombre.
- Los tipos `magistratura` y `direccion`, sin distinguir mayúsculas, se
  presentan como `Magistratura` y `Dirección`. Otros tipos se muestran como un
  título legible en vez de descartarse.
- Varias pertenencias se unen con ` · `; por ejemplo,
  `Magistratura: Magistratura A · Dirección: Dirección B`.
- `Principal` contiene el nombre de la primera unidad marcada como principal
  en el orden estable; queda vacío si ninguna lo está.
- `active` se presenta como `Activo` e `inactive` como `Inactivo`. Un estado
  distinto se conserva como texto legible para no ocultar datos inesperados.
- Si varias filas del mismo usuario discrepan en nombre, rol o estado, se usa
  el primer valor no vacío en el orden recibido.

## Módulo PyShiny

Se creará `modules/organizational_directory/` con `__init__.py`, `ui.py` y
`server.py`.

La UI mostrará el título `Directorio organizacional`, el subtítulo
`Usuarios, roles funcionales y pertenencias organizacionales.` y un
`DataGrid` filtrable con las seis columnas del presenter.

El servidor recibirá `dependencies`, `is_authenticated` e `is_admin` como
callbacks. No consultará datos salvo que ambos devuelvan `True`. La carga se
realizará una vez por estado reactivo válido de la sesión. Si el repositorio no
está configurado, se mostrará una tabla vacía. Si Supabase produce una
excepción, el servidor la registrará y mostrará el mensaje seguro
`Directorio organizacional no disponible.` sin exponer detalles internos.

La pestaña aparecerá entre `Memoria episódica` y `Diagnóstico` con el valor de
navegación `organizational_directory`.

## Flujo de datos

```text
Supabase: memory_organizational_directory_v
    -> SupabaseOrganizationDirectoryRepository
    -> OrganizationDirectoryEntry[]
    -> OrganizationalDirectoryService
    -> OrganizationalDirectoryPresenter
    -> DataGrid de PyShiny
```

La autorización se deriva en paralelo de `AuthSessionState.actor` y se valida
antes de entrar en el flujo.

## Pruebas

`memory_core` tendrá pruebas unitarias para:

- usuario sin unidad;
- usuario con unidad, `unit_type` y marca principal;
- consulta de la vista y selección de columnas;
- mapeo de varias filas y valores opcionales;
- respuesta sin datos.

`appmemoria` tendrá pruebas para:

- service con y sin repositorio;
- agrupación de varias pertenencias en una sola fila;
- deduplicación, orden, principal, estado y usuario sin unidad;
- pestaña visible para `admin` y ausente para `viewer`;
- guardia del servidor que impide consultar como `viewer`;
- integración del módulo en el shell y el servidor.

Todas las pruebas nuevas seguirán ciclos RED/GREEN. Al finalizar se ejecutarán
las suites completas de ambos repositorios, `compileall` sobre los archivos
nuevos y modificados, y `git diff --check` en ambos repositorios.

Si las variables locales permiten construir el runtime, se hará además una
lectura real y de solo lectura con `list_directory_entries()`. La ausencia de
credenciales no hará fallar la suite automatizada.

## Validación visual

Se iniciará `shiny run app.py` para comprobar que un administrador ve la
pestaña, que la tabla respeta las columnas y que la navegación existente no se
degrada. También se verificará mediante pruebas que un visor no recibe esa
pestaña.

## Recuperación

Los puntos previos a la implementación son:

- `appmemoria`: `checkpoint/antes-implementacion-sustancial-2026-09-22`
  (`5716ef2`).
- `memory_core`:
  `checkpoint/antes-directorio-organizacional-admin-2026-09-22` (`cd500de`).

Para inspeccionar o recuperar cualquiera de los estados se debe crear una rama
nueva desde el tag correspondiente, evitando sobrescribir trabajo posterior.

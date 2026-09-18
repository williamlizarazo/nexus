# Authentication and Authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build provider-agnostic authentication, ephemeral Supabase Auth login, and deny-by-default admin/viewer authorization without adding login UI.

**Architecture:** Domain contracts live under `auth` and `authorization`; only the Supabase adapter imports the provider SDK. Authentication, authorization, and memory capabilities are built independently in `AppDependencies`.

**Tech Stack:** Python 3.11, PyShiny 1.8, Supabase Python 2.x, python-dotenv, pytest 8+

**Spec:** `docs/superpowers/specs/2026-09-17-authentication-authorization-design.md`

## Global Constraints

- No login UI, navigation guards, MFA, recovery, or administrative tab.
- Do not change `memory_core`, persistence services, or database adapters.
- Prefer `SUPABASE_PUBLISHABLE_KEY`; allow `SUPABASE_ANON_KEY` only as a legacy fallback.
- Never use service-role or secret keys for login.
- Create a new Supabase client for every authentication attempt.
- Authorization is deny-by-default and admin takes priority over viewer.
- Never print or commit values from `.env`.
- Preserve unrelated working-tree changes and stage only task-owned paths.

---

### Task 1: Authentication Domain and Service

**Files:**
- Create: `auth/__init__.py`
- Create: `auth/models.py`
- Create: `auth/ports.py`
- Create: `auth/service.py`
- Create: `tests/test_auth_service.py`

**Interfaces:**
- Produces: `AuthIdentity`, `AppActor`, `AccessRole`, `AuthProvider.authenticate()`, `AuthService.login()`, and `AuthenticationError`.
- Consumes: no provider-specific code.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from auth.models import AuthIdentity
from auth.service import AuthenticationError, AuthService

class FakeAuthProvider:
    def __init__(self):
        self.received = None
    def authenticate(self, email, password):
        self.received = (email, password)
        return AuthIdentity("user-001", email)

class FailingAuthProvider:
    def authenticate(self, email, password):
        raise RuntimeError("provider failure")

def test_login_normalizes_email():
    provider = FakeAuthProvider()
    identity = AuthService(provider).login("  USER@EXAMPLE.ORG ", "secret")
    assert identity == AuthIdentity("user-001", "user@example.org")
    assert provider.received == ("user@example.org", "secret")

@pytest.mark.parametrize("email,password", [("", "secret"), ("a@b.co", "")])
def test_login_rejects_empty_credentials(email, password):
    with pytest.raises(AuthenticationError):
        AuthService(FakeAuthProvider()).login(email, password)

def test_login_hides_provider_error():
    with pytest.raises(AuthenticationError, match="No fue posible autenticar"):
        AuthService(FailingAuthProvider()).login("user@example.org", "secret")
```

- [ ] **Step 2: Verify RED**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_auth_service.py -v`

Expected: import failure because the `auth` modules do not exist.

- [ ] **Step 3: Implement the minimal domain and service**

```python
# auth/models.py
from dataclasses import dataclass
from typing import Literal

AccessRole = Literal["admin", "viewer"]

@dataclass(frozen=True, slots=True)
class AuthIdentity:
    user_id: str
    email: str
    def __post_init__(self):
        object.__setattr__(self, "user_id", self.user_id.strip())
        object.__setattr__(self, "email", self.email.strip().lower())

@dataclass(frozen=True, slots=True)
class AppActor:
    user_id: str
    email: str
    role: AccessRole
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
```

```python
# auth/ports.py
from typing import Protocol
from auth.models import AuthIdentity

class AuthProvider(Protocol):
    def authenticate(self, email: str, password: str) -> AuthIdentity: ...
```

```python
# auth/service.py
from auth.models import AuthIdentity
from auth.ports import AuthProvider

class AuthenticationError(RuntimeError):
    pass

class AuthService:
    def __init__(self, provider: AuthProvider) -> None:
        self._provider = provider

    def login(self, email: str, password: str) -> AuthIdentity:
        normalized_email = email.strip().lower()
        if not normalized_email or not password:
            raise AuthenticationError("Correo y contraseÃ±a son obligatorios.")
        try:
            identity = self._provider.authenticate(normalized_email, password)
        except Exception as exc:
            raise AuthenticationError(
                "No fue posible autenticar las credenciales."
            ) from exc
        return AuthIdentity(identity.user_id, identity.email)
```

- [ ] **Step 4: Verify GREEN**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_auth_service.py -v`

- [ ] **Step 5: Commit only Task 1 files**

```powershell
git add -- auth/__init__.py auth/models.py auth/ports.py auth/service.py tests/test_auth_service.py
git commit -m "feat: add authentication domain service"
```

### Task 2: Deny-by-Default Authorization

**Files:**
- Create: `authorization/__init__.py`
- Create: `authorization/service.py`
- Create: `tests/test_authorization_service.py`

**Interfaces:**
- Consumes: `AuthIdentity` and `AppActor`.
- Produces: `AuthorizationService.authorize(identity) -> AppActor | None`.

- [ ] **Step 1: Write failing admin, viewer, and denial tests**

```python
from auth.models import AuthIdentity
from authorization.service import AuthorizationService

def test_admin_role_has_priority():
    service = AuthorizationService(
        admin_emails=("ADMIN@EXAMPLE.ORG",),
        viewer_emails=("admin@example.org",),
    )
    actor = service.authorize(AuthIdentity("user-001", "admin@example.org"))
    assert actor is not None and actor.role == "admin" and actor.is_admin

def test_viewer_is_authorized():
    service = AuthorizationService(viewer_emails=("viewer@example.org",))
    actor = service.authorize(AuthIdentity("user-002", "VIEWER@example.org"))
    assert actor is not None and actor.role == "viewer" and not actor.is_admin

def test_unknown_email_is_denied():
    service = AuthorizationService(admin_emails=("admin@example.org",))
    assert service.authorize(AuthIdentity("user-003", "other@example.org")) is None
```

- [ ] **Step 2: Verify RED**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_authorization_service.py -v`

- [ ] **Step 3: Implement normalized role lookup**

```python
from auth.models import AppActor, AuthIdentity

def _normalize_emails(values: tuple[str, ...]) -> frozenset[str]:
    return frozenset(value.strip().lower() for value in values if value.strip())

class AuthorizationService:
    def __init__(self, *, admin_emails=(), viewer_emails=()) -> None:
        self._admins = _normalize_emails(admin_emails)
        self._viewers = _normalize_emails(viewer_emails)

    def authorize(self, identity: AuthIdentity) -> AppActor | None:
        email = identity.email.strip().lower()
        if email in self._admins:
            return AppActor(identity.user_id, email, "admin")
        if email in self._viewers:
            return AppActor(identity.user_id, email, "viewer")
        return None
```

- [ ] **Step 4: Verify GREEN**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_authorization_service.py -v`

- [ ] **Step 5: Commit only Task 2 files**

```powershell
git add -- authorization/__init__.py authorization/service.py tests/test_authorization_service.py
git commit -m "feat: add role authorization service"
```

### Task 3: Supabase Authentication Adapter

**Files:**
- Create: `auth/adapters/__init__.py`
- Create: `auth/adapters/supabase.py`
- Create: `tests/test_supabase_auth_adapter.py`

**Interfaces:**
- Consumes: `AuthIdentity`, Supabase `create_client`, `SUPABASE_URL`, and a public API key.
- Produces: `SupabaseAuthProvider`, `AuthProviderConfigurationError`, and `build_supabase_auth_provider_from_env()`.

- [ ] **Step 1: Write failing tests for key precedence, missing configuration, secret rejection, response validation, and a fresh client for each attempt**

```python
from types import SimpleNamespace
import pytest
import supabase
from auth.adapters.supabase import (
    AuthProviderConfigurationError,
    SupabaseAuthProvider,
    build_supabase_auth_provider_from_env,
)

def test_builder_prefers_publishable_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "legacy-key")
    assert build_supabase_auth_provider_from_env()._api_key == "publishable-key"

def test_builder_rejects_missing_public_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    with pytest.raises(AuthProviderConfigurationError):
        build_supabase_auth_provider_from_env()

def test_builder_uses_legacy_anon_key_as_fallback(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_ANON_KEY", "legacy-key")
    assert build_supabase_auth_provider_from_env()._api_key == "legacy-key"

def test_builder_rejects_secret_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_secret_forbidden")
    with pytest.raises(AuthProviderConfigurationError, match="clave pública"):
        build_supabase_auth_provider_from_env()

def test_authenticate_creates_a_fresh_client_per_attempt(monkeypatch):
    clients = []
    def create_client(url, key):
        client = SimpleNamespace(
            auth=SimpleNamespace(
                sign_in_with_password=lambda credentials: SimpleNamespace(
                    user=SimpleNamespace(
                        id=f"user-{len(clients)}", email=credentials["email"]
                    )
                )
            )
        )
        clients.append(client)
        return client
    monkeypatch.setattr(supabase, "create_client", create_client)
    provider = SupabaseAuthProvider(
        url="https://example.supabase.co", api_key="publishable-key"
    )
    provider.authenticate("one@example.org", "secret")
    provider.authenticate("two@example.org", "secret")
    assert len(clients) == 2 and clients[0] is not clients[1]

def test_authenticate_rejects_response_without_user(monkeypatch):
    client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_in_with_password=lambda credentials: SimpleNamespace(user=None)
        )
    )
    monkeypatch.setattr(supabase, "create_client", lambda url, key: client)
    provider = SupabaseAuthProvider(
        url="https://example.supabase.co", api_key="publishable-key"
    )
    with pytest.raises(RuntimeError, match="no devolvió usuario"):
        provider.authenticate("user@example.org", "secret")
```

- [ ] **Step 2: Verify RED**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_supabase_auth_adapter.py -v`

- [ ] **Step 3: Implement the adapter**

```python
import os
from auth.models import AuthIdentity

class AuthProviderConfigurationError(RuntimeError):
    pass

class SupabaseAuthProvider:
    def __init__(self, *, url: str, api_key: str) -> None:
        self._url = url
        self._api_key = api_key

    def authenticate(self, email: str, password: str) -> AuthIdentity:
        from supabase import create_client
        client = create_client(self._url, self._api_key)
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user = getattr(response, "user", None)
        if user is None:
            raise RuntimeError("Supabase no devolviÃ³ usuario.")
        user_id = str(getattr(user, "id", "")).strip()
        if not user_id:
            raise RuntimeError("Supabase no devolviÃ³ user_id.")
        user_email = str(getattr(user, "email", "") or email)
        return AuthIdentity(user_id, user_email)

def build_supabase_auth_provider_from_env() -> SupabaseAuthProvider:
    url = os.getenv("SUPABASE_URL", "").strip()
    api_key = (
        os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    if not url:
        raise AuthProviderConfigurationError("Falta SUPABASE_URL.")
    if not api_key:
        raise AuthProviderConfigurationError(
            "Falta SUPABASE_PUBLISHABLE_KEY o SUPABASE_ANON_KEY."
        )
    if api_key.startswith("sb_secret_"):
        raise AuthProviderConfigurationError(
            "La autenticaciÃ³n requiere una clave pÃºblica de Supabase."
        )
    return SupabaseAuthProvider(url=url, api_key=api_key)
```

- [ ] **Step 4: Verify GREEN**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_supabase_auth_adapter.py -v`

- [ ] **Step 5: Commit only Task 3 files**

```powershell
git add -- auth/adapters/__init__.py auth/adapters/supabase.py tests/test_supabase_auth_adapter.py
git commit -m "feat: add isolated Supabase auth adapter"
```

### Task 4: Environment Configuration

**Files:**
- Modify: `core/config.py`
- Modify: `tests/test_config_env.py`
- Modify: `.env.example`

**Interfaces:**
- Produces: `AppConfig.admin_emails`, `AppConfig.viewer_emails`, and `_env_csv(name)`.
- Consumes: `APPMEMORIA_ADMIN_EMAILS` and `APPMEMORIA_VIEWER_EMAILS`.

- [ ] **Step 1: Add a failing normalized-list test**

```python
def test_load_config_reads_normalized_authorized_emails(monkeypatch):
    monkeypatch.setattr(config_module, "load_local_env", lambda: True)
    monkeypatch.setenv(
        "APPMEMORIA_ADMIN_EMAILS",
        " ADMIN@example.org, second@example.org ",
    )
    monkeypatch.setenv("APPMEMORIA_VIEWER_EMAILS", " viewer@example.org, ")
    config = config_module.load_config()
    assert config.admin_emails == ("admin@example.org", "second@example.org")
    assert config.viewer_emails == ("viewer@example.org",)
```

- [ ] **Step 2: Verify RED**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_config_env.py::test_load_config_reads_normalized_authorized_emails -v`

- [ ] **Step 3: Extend `AppConfig`, add `_env_csv`, and add blank names to `.env.example`**

```dotenv
SUPABASE_PUBLISHABLE_KEY=
APPMEMORIA_ADMIN_EMAILS=
APPMEMORIA_VIEWER_EMAILS=
```

- [ ] **Step 4: Verify GREEN**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_config_env.py -v`

- [ ] **Step 5: Commit only Task 4 files**

```powershell
git add -- core/config.py tests/test_config_env.py .env.example
git commit -m "feat: configure authorized application emails"
```

### Task 5: Independent Dependency Construction

**Files:**
- Modify: `core/dependencies.py`
- Modify: `tests/test_dependencies.py`

**Interfaces:**
- Consumes: configuration lists, `build_supabase_auth_provider_from_env()`, and `build_memory_runtime_from_env()`.
- Produces: `AppDependencies.auth_provider`, `authorization_service`, and `auth_runtime_error` while preserving all successful memory fields.

- [ ] **Step 1: Write failing independence tests**

```python
def test_auth_survives_memory_runtime_failure(monkeypatch):
    auth_provider = object()
    monkeypatch.setattr(
        dependencies_module,
        "build_supabase_auth_provider_from_env",
        lambda: auth_provider,
    )
    monkeypatch.setattr(
        dependencies_module,
        "build_memory_runtime_from_env",
        lambda: (_ for _ in ()).throw(
            MemoryRuntimeConfigurationError("memory unavailable")
        ),
    )
    dependencies = dependencies_module.build_dependencies(
        AppConfig("appmemoria", "test", True)
    )
    assert dependencies.auth_provider is auth_provider
    assert dependencies.authorization_service is not None
    assert dependencies.memory_runtime_error == "memory unavailable"

def test_memory_survives_auth_provider_failure(monkeypatch):
    runtime = SimpleNamespace(
        episode_repository=object(),
        research_activity_source=object(),
    )
    monkeypatch.setattr(
        dependencies_module,
        "build_supabase_auth_provider_from_env",
        lambda: (_ for _ in ()).throw(
            AuthProviderConfigurationError("auth unavailable")
        ),
    )
    monkeypatch.setattr(
        dependencies_module,
        "build_memory_runtime_from_env",
        lambda: runtime,
    )
    dependencies = dependencies_module.build_dependencies(
        AppConfig("appmemoria", "test", True)
    )
    assert dependencies.episode_repository is runtime.episode_repository
    assert dependencies.auth_provider is None
    assert dependencies.auth_runtime_error == "auth unavailable"
```

- [ ] **Step 2: Verify RED**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_dependencies.py -v`

- [ ] **Step 3: Extend and decouple `build_dependencies()`**

Add these fields to `AppDependencies`:

```python
auth_provider: Any | None = None
authorization_service: Any | None = None
auth_runtime_error: str | None = None
```

Implement independent construction:

```python
def build_dependencies(config: AppConfig) -> AppDependencies:
    authorization_service = AuthorizationService(
        admin_emails=config.admin_emails,
        viewer_emails=config.viewer_emails,
    )

    auth_provider = None
    auth_runtime_error = None
    try:
        auth_provider = build_supabase_auth_provider_from_env()
    except AuthProviderConfigurationError as exc:
        auth_runtime_error = str(exc)

    runtime = None
    memory_runtime_error = None
    try:
        runtime = build_memory_runtime_from_env()
    except MemoryRuntimeConfigurationError as exc:
        memory_runtime_error = str(exc)

    return AppDependencies(
        episode_repository=(
            getattr(runtime, "episode_repository", None) if runtime else None
        ),
        research_activity_source=(
            getattr(runtime, "research_activity_source", None) if runtime else None
        ),
        research_project_source=(
            getattr(runtime, "research_project_source", None) if runtime else None
        ),
        organization_directory_repository=(
            getattr(runtime, "organization_directory_repository", None)
            if runtime
            else None
        ),
        auth_provider=auth_provider,
        authorization_service=authorization_service,
        auth_runtime_error=auth_runtime_error,
        memory_runtime_error=memory_runtime_error,
    )
```

- [ ] **Step 4: Verify GREEN**

Run: `.venv\\Scripts\\python.exe -m pytest tests\\test_dependencies.py -v`

- [ ] **Step 5: Commit only Task 5 files**

```powershell
git add -- core/dependencies.py tests/test_dependencies.py
git commit -m "feat: decouple auth and memory dependencies"
```

### Task 6: Dependency Declaration and Final Verification

**Files:**
- Modify: `requirements.txt`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: the Supabase adapter.
- Produces: reproducible `supabase>=2.0,<3.0` runtime dependency.

- [ ] **Step 1: Add the direct dependency to both manifests**

```text
supabase>=2.0,<3.0
```

- [ ] **Step 2: Verify the installed version**

Run: `.venv\\Scripts\\python.exe -c "import importlib.metadata as m; print(m.version('supabase'))"`

Expected: version >=2.0 and <3.0.

- [ ] **Step 3: Run focused and complete verification**

```powershell
.venv\\Scripts\\python.exe -m pytest tests\\test_auth_service.py tests\\test_authorization_service.py tests\\test_supabase_auth_adapter.py tests\\test_config_env.py tests\\test_dependencies.py -v
.venv\\Scripts\\python.exe -m pytest tests -q
.venv\\Scripts\\python.exe -m compileall auth authorization core
git diff --check
git status --short
```

- [ ] **Step 4: Inspect manifest changes and commit only their intended hunks**

```powershell
git diff -- requirements.txt pyproject.toml
git add -- requirements.txt pyproject.toml
git commit -m "build: declare Supabase auth dependency"
```



# Authentication and Authorization Design

## Objective

Add authentication and authorization infrastructure to `appmemoria` without
adding a login screen or administrative tab yet. Each PyShiny session will be
able to authenticate a user through Supabase Auth and convert the resulting
identity into an authorized application actor with either the `admin` or
`viewer` role.

The subsystem must remain independent from `memory_core`. A failure to build
the memory runtime must not prevent the authentication and authorization
capabilities from being constructed, and an authentication configuration
failure must not prevent the memory runtime from being constructed.

## Scope

This block includes:

- normalized authentication identities;
- an agnostic authentication provider contract;
- an authentication service that validates credentials and hides provider
  failures behind a stable application error;
- a Supabase Auth adapter;
- deny-by-default authorization with `admin` and `viewer` roles;
- environment-backed authorized-email lists;
- dependency construction for authentication and authorization;
- direct declaration of the Supabase Python dependency;
- automated tests for services, configuration, dependency isolation, and the
  ephemeral-client security requirement.

This block excludes:

- login/logout UI;
- persistence of identity in a PyShiny session;
- navigation guards;
- the administrative tab;
- password recovery, invitations, MFA, or account management;
- changes to `memory_core`, persistence services, or database adapters.

## Architecture

```text
Supabase Auth
     |
SupabaseAuthProvider  (adapter; new client per authentication attempt)
     |
AuthProvider          (agnostic protocol)
     |
AuthService
     |
AuthIdentity
     |
AuthorizationService
     |
AppActor (admin | viewer)
```

Application code depends on `AuthProvider`, `AuthIdentity`, `AppActor`, and the
two services. Only `auth/adapters/supabase.py` imports the Supabase SDK.

## Domain Models

`AuthIdentity` contains a non-provider-specific `user_id` and normalized email.
It trims both fields and lowercases the email.

`AppActor` contains `user_id`, normalized email, and an `AccessRole` restricted
to `admin` or `viewer`. Its `is_admin` property derives from the role rather
than storing a second authorization flag.

## Authentication Contract and Service

`AuthProvider` is a `Protocol` with this operation:

```python
def authenticate(self, email: str, password: str) -> AuthIdentity: ...
```

`AuthService.login()` normalizes the email before calling the provider,
rejects missing email or password, and returns a normalized `AuthIdentity`.
Provider exceptions are chained internally but exposed to callers as a stable
`AuthenticationError` that does not leak provider details.

## Supabase Adapter and Session Isolation

`SupabaseAuthProvider.authenticate()` imports `create_client` locally and
creates a new Supabase client for every authentication attempt. No authenticated
client or session is stored in `AppDependencies`, shared globally, or reused
between PyShiny sessions.

The adapter reads the API key in this order:

1. `SUPABASE_PUBLISHABLE_KEY` (current recommended key);
2. `SUPABASE_ANON_KEY` (legacy compatibility only).

It never reads `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_SECRET_KEY`, or any
`sb_secret_...` value. Missing `SUPABASE_URL` or a supported public key produces
`AuthProviderConfigurationError`.

The adapter validates that Supabase returned a user and a non-empty user ID.

## Authorization Rules

`AuthorizationService` receives normalized sets of administrator and viewer
emails. Authorization is deny-by-default:

- an administrator email produces an `AppActor(role="admin")`;
- otherwise, a viewer email produces an `AppActor(role="viewer")`;
- every other authenticated identity returns `None`.

Administrator membership has priority when an email appears in both lists.
With the current local configuration, `william.lizarazo@jep.gov.co` is therefore
an administrator even though it is listed in both variables.

## Configuration

`AppConfig` gains `admin_emails` and `viewer_emails`, both tuples of normalized
emails. `load_config()` reads comma-separated values from:

- `APPMEMORIA_ADMIN_EMAILS`;
- `APPMEMORIA_VIEWER_EMAILS`.

The existing `.env` already contains `SUPABASE_PUBLISHABLE_KEY` and both access
lists. Tests must never read, print, or commit secret values.

## Dependency Construction

`AppDependencies` gains:

- `auth_provider`;
- `authorization_service`;
- `auth_runtime_error`.

`build_dependencies()` always builds `AuthorizationService` from `AppConfig`.
It attempts to build the authentication provider and memory runtime separately.
Each failure is captured in its own error field. The resulting dependency object
preserves every capability that was constructed successfully instead of
returning early and discarding unrelated capabilities.

The authentication provider in `AppDependencies` is an unauthenticated provider
factory object. It contains only project URL and public key; it does not contain
an authenticated Supabase client or user session.

## Dependency Declaration

Both `requirements.txt` and `pyproject.toml` declare:

```text
supabase>=2.0,<3.0
```

The installed environment currently satisfies this constraint with Supabase
Python 2.31.0.

## Error Handling

- Missing credentials: `AuthenticationError` with a user-safe required-fields
  message.
- Supabase authentication or transport failure: `AuthenticationError` with a
  generic authentication message and the original exception chained.
- Missing provider configuration: `AuthProviderConfigurationError`, captured as
  `auth_runtime_error` during dependency construction.
- Unknown authenticated email: authorization returns `None`.
- Memory runtime misconfiguration: captured independently as
  `memory_runtime_error`.

## Testing Strategy

Tests will be written before production code and will cover:

1. authentication email normalization;
2. rejection of empty credentials;
3. provider-error concealment;
4. administrator priority over viewer;
5. viewer authorization;
6. deny-by-default behavior;
7. publishable-key configuration and legacy anon-key fallback;
8. rejection when no public key is configured;
9. a fresh Supabase client for each authentication attempt;
10. email-list parsing in `AppConfig`;
11. authentication surviving memory-runtime failure;
12. memory dependencies surviving authentication-provider failure.

The complete existing test suite, compilation of `auth`, `authorization`, and
`core`, and `git diff --check` must pass before completion.

## Security Properties

- No privileged Supabase key is used for user login.
- No authenticated Supabase client is shared between sessions.
- Authentication does not imply authorization.
- Authorization denies access unless the normalized email is explicitly listed.
- Provider errors and sensitive configuration values are not exposed to users or
  test output.

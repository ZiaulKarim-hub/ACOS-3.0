#!/usr/bin/env python3
"""hca-secrets.py — env/secret-store credential loader (SLICE-HCA-10).

Centralizes what hca-live.py and hca-adapter.LiveBackend read from the
environment. Credentials are injected at runtime by Doppler:

    doppler run --project hypercore-ask --config dev_personal -- <command>

INVARIANTS (hard — slice-10 acceptance):
  1. This module NEVER logs, prints, or echoes the secret value itself.
  2. Absent / blank credentials yield a clear, named error — NOT a crash
     that might leak partial data, NOT a fabricated answer.
  3. The __repr__ / __str__ of the returned Credentials object is REDACTED
     so that e.g. `print(creds)`, f-string interpolation, or logging the
     object can never leak the secret.
  4. Only the ENV VAR NAMES live in code; the VALUES come from the environment.

USAGE:
    from hca_secrets import load_credentials, MissingCredentialsError

    try:
        creds = load_credentials()
    except MissingCredentialsError as e:
        # Degrade to NO_LIVE_DATA — never crash, never fabricate.
        print(e)          # clear human-readable message naming the missing var
        ...

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib only. No third-party deps. No network. No model calls.
  - Subscription-only Claude: never reads the Anthropic API key env var.
  - This module is the ONLY place credentials are read from env. All other
    modules that previously read CLIENT_ID / HYPERCORE_CLIENT_SECRET directly must
    delegate here (or pass the env dict to LiveBackend which calls is_live()
    using the same env var names).
"""

from __future__ import annotations

import os
from typing import Optional


# ---------------------------------------------------------------------------
# Canonical env var names (names only; values are NEVER stored in code)
# ---------------------------------------------------------------------------

CLIENT_ID_ENV = "CLIENT_ID"
API_KEY_ENV = "HYPERCORE_CLIENT_SECRET"      # OAuth client SECRET (Doppler name)
BASE_URL_ENV = "HYPERCORE_BASE_URL"    # optional override for the GraphQL URL


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

class MissingCredentialsError(RuntimeError):
    """Raised when a required credential env var is absent or blank.

    The message names the MISSING VAR NAME only — not the value of any var.
    The caller MUST degrade to the NO_LIVE_DATA path on this error; it MUST
    NOT crash, log sensitive context, or fabricate an answer.
    """


# ---------------------------------------------------------------------------
# Credentials holder — value is NEVER exposed by repr/str
# ---------------------------------------------------------------------------

class Credentials:
    """Immutable holder for the Hypercore credential pair.

    The secret is accessible via `.api_key` (for use in auth calls) but is
    NEVER surfaced by str(), repr(), or format(). Any log statement that
    accidentally logs this object will emit the redacted placeholder instead.

    Usage:
        creds = load_credentials()
        # Pass to the auth call:
        token_manager = TokenManager(client_id=creds.client_id,
                                     client_secret=creds.api_key, ...)
    """

    __slots__ = ("client_id", "api_key", "_client_id_env", "_api_key_env")

    def __init__(self, *, client_id: str, api_key: str,
                 client_id_env: str = CLIENT_ID_ENV,
                 api_key_env: str = API_KEY_ENV):
        object.__setattr__(self, "client_id", client_id)
        object.__setattr__(self, "api_key", api_key)
        object.__setattr__(self, "_client_id_env", client_id_env)
        object.__setattr__(self, "_api_key_env", api_key_env)

    def __setattr__(self, name, value):
        raise AttributeError("Credentials is immutable")

    def __repr__(self) -> str:
        # NEVER include the secret or client_id value.
        return (
            f"Credentials("
            f"client_id_env={self._client_id_env!r}, "
            f"api_key_env={self._api_key_env!r}, "
            f"client_id=[REDACTED], "
            f"api_key=[REDACTED]"
            f")"
        )

    def __str__(self) -> str:
        return self.__repr__()

    def __format__(self, format_spec: str) -> str:
        return self.__repr__()

    def redacted_summary(self) -> dict:
        """Return a loggable dict summary — values are ALWAYS redacted."""
        return {
            "client_id_env": self._client_id_env,
            "api_key_env": self._api_key_env,
            "client_id": "[REDACTED]",
            "api_key": "[REDACTED]",
            "client_id_present": bool(self.client_id),
            "api_key_present": bool(self.api_key),
        }


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_credentials(
    *,
    client_id_env: str = CLIENT_ID_ENV,
    api_key_env: str = API_KEY_ENV,
    env: Optional[dict] = None,
) -> Credentials:
    """Load CLIENT_ID + HYPERCORE_CLIENT_SECRET from the environment.

    Parameters
    ----------
    client_id_env, api_key_env : str
        Names of the env vars to read (defaults: CLIENT_ID, HYPERCORE_CLIENT_SECRET).
    env : dict | None
        Explicit env mapping for testing (defaults to os.environ).

    Returns
    -------
    Credentials
        Immutable holder. repr/str never expose the secret.

    Raises
    ------
    MissingCredentialsError
        If either var is absent or blank. Message names the missing var.
        Caller must degrade to NO_LIVE_DATA; must NOT crash or fabricate.
    """
    _env = env if env is not None else os.environ
    client_id = (_env.get(client_id_env) or "").strip()
    api_key = (_env.get(api_key_env) or "").strip()

    missing = []
    if not client_id:
        missing.append(client_id_env)
    if not api_key:
        missing.append(api_key_env)

    if missing:
        raise MissingCredentialsError(
            f"Missing required credential(s): {missing}. "
            f"Inject via Doppler: "
            f"`doppler run --project hypercore-ask --config dev_personal -- <cmd>`. "
            f"Degrading to NO_LIVE_DATA path. "
            f"(Never fabricate; never crash with partial data.)"
        )

    return Credentials(
        client_id=client_id,
        api_key=api_key,
        client_id_env=client_id_env,
        api_key_env=api_key_env,
    )


def is_provisioned(
    *,
    client_id_env: str = CLIENT_ID_ENV,
    api_key_env: str = API_KEY_ENV,
    env: Optional[dict] = None,
) -> bool:
    """Return True when both credentials are present and non-blank.

    Non-raising equivalent of load_credentials() — suitable for is_live() checks.
    NEVER returns the credential values.
    """
    _env = env if env is not None else os.environ
    client_id = (_env.get(client_id_env) or "").strip()
    api_key = (_env.get(api_key_env) or "").strip()
    return bool(client_id) and bool(api_key)


# ---------------------------------------------------------------------------
# Module-level self-test (demonstrates NO-SECRET-LOGGED invariant)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    env_under_test = {CLIENT_ID_ENV: "test-id", API_KEY_ENV: "super-secret-value"}

    # 1. Show that repr never leaks the secret.
    creds = load_credentials(env=env_under_test)
    print("repr:", repr(creds))
    print("str :", str(creds))
    print("f   :", f"{creds}")
    assert "super-secret-value" not in repr(creds), "SECRET IN REPR — FAIL"
    assert "super-secret-value" not in str(creds), "SECRET IN STR — FAIL"
    print("redacted_summary:", json.dumps(creds.redacted_summary(), indent=2))

    # 2. Show that absent vars raise a named clear error with the env var names.
    try:
        load_credentials(env={})
    except MissingCredentialsError as exc:
        print(f"\nMissingCredentialsError (expected): {exc}")
        assert CLIENT_ID_ENV in str(exc), "Error message should name the missing CLIENT_ID var"
        assert API_KEY_ENV in str(exc), "Error message should name the missing API_KEY var"
        print("PASS: clear error, missing vars named, no crash, no secret echoed.")
        sys.exit(0)

    print("FAIL: expected MissingCredentialsError but did not get one")
    sys.exit(1)

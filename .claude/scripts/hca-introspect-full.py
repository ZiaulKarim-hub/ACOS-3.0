#!/usr/bin/env python3
"""hca-introspect-full.py — run the STANDARD full GraphQL IntrospectionQuery (read-only).

Step 0 of SLICE-HCA-02 (LiveBackend upgrade): the original `_introspection.json`
(produced by hca-discover.py) carried only field NAMES + a shallow return-type chain.
It lacked field ARGS, INPUT_OBJECT inputFields, and enumValues — which the LiveBackend
needs to build exact query arguments (the pagination/filter input shapes for `loans`,
`clients`, etc.) and to validate requested fields before sending.

This script runs the canonical GraphQL introspection query (same shape graphql-core /
graphiql emit), unwrapping the type-ref chain to depth 7 and including:
    - every field's `args { name, type, defaultValue }`
    - every INPUT_OBJECT's `inputFields { name, type, defaultValue }`
    - every ENUM's `enumValues { name }`
    - interfaces / possibleTypes / enumValues / etc.

Flow (READ-ONLY — an auth POST + a single GraphQL `query` introspection; NO mutations):
  1. POST {clientId, secret} to the token service -> JWT accessToken.
  2. POST the introspection query to the GraphQL endpoint with Bearer <accessToken>.
  3. Overwrite `_introspection.json`; print ONLY summary stats (never the token/secret).

Credentials (CLIENT_ID + HYPERCORE_CLIENT_SECRET, the OAuth client *secret*) are read from
the environment, which Doppler injects at runtime:
    doppler run --project hypercore-ask --config dev_personal -- python3 .claude/scripts/hca-introspect-full.py

SECURITY: never prints the secret or the JWT. stdlib only. TLS >= 1.2 enforced.
"""
import os
import sys
import ssl
import json
import urllib.request
import urllib.error
import importlib.util


def _load_hca_secrets():
    """Load the sibling hca-secrets.py (hyphenated filename) — the SINGLE SOURCE OF TRUTH
    for credential env var NAMES. No secret VALUE is read at import time."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "hca-secrets.py")
    spec = importlib.util.spec_from_file_location("hca_secrets", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_secrets = _load_hca_secrets()

AUTH_URL = os.environ.get(
    "HYPERCORE_AUTH_URL",
    "https://auth.hypercore.ai/identity/resources/auth/v1/api-token",
)
GQL_URL = os.environ.get(_secrets.BASE_URL_ENV, "https://api.hypercore.ai/graphql")
CLIENT_ID = os.environ.get(_secrets.CLIENT_ID_ENV)
SECRET = os.environ.get(_secrets.API_KEY_ENV)  # OAuth client secret (Doppler name)
OUT = os.environ.get(
    "HCA_INTROSPECTION_OUT",
    "planning/preeng/001-hypercore-ask/_introspection.json",
)

# --- Standard full GraphQL IntrospectionQuery (type ref chain unwound to depth 7) ----
# Mirrors the canonical query graphql-js ships. Adds args + inputFields + enumValues.
_TYPE_REF = """
fragment TypeRef on __Type {
  kind name
  ofType { kind name
    ofType { kind name
      ofType { kind name
        ofType { kind name
          ofType { kind name
            ofType { kind name
              ofType { kind name }
            }
          }
        }
      }
    }
  }
}
"""

INTROSPECTION = (
    """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args { ...InputValue }
        type { ...TypeRef }
        isDeprecated
        deprecationReason
      }
      inputFields { ...InputValue }
      interfaces { ...TypeRef }
      enumValues(includeDeprecated: true) {
        name
        description
        isDeprecated
        deprecationReason
      }
      possibleTypes { ...TypeRef }
    }
    directives {
      name
      description
      locations
      args { ...InputValue }
    }
  }
}

fragment InputValue on __InputValue {
  name
  description
  type { ...TypeRef }
  defaultValue
}
"""
    + _TYPE_REF
)


def _ssl_context():
    """TLS >= 1.2 enforced (matches LiveBackend transport posture)."""
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def post_json(url, payload, headers=None):
    data = json.dumps(payload).encode()
    h = {"accept": "application/json", "content-type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=60, context=_ssl_context()) as r:
        return r.status, json.loads(r.read().decode())


def main():
    if not CLIENT_ID or not SECRET:
        print("FAIL: CLIENT_ID / HYPERCORE_CLIENT_SECRET not in env. "
              "Run via `doppler run --project hypercore-ask --config dev_personal -- python3 ...`.")
        return 2
    print(f"auth_url = {AUTH_URL}")
    print(f"gql_url  = {GQL_URL}")

    # --- Step 1: token exchange ---
    try:
        _, tok = post_json(AUTH_URL, {"clientId": CLIENT_ID, "secret": SECRET})
    except urllib.error.HTTPError as e:
        print(f"FAIL token exchange: HTTP {e.code} {e.reason}")
        try:
            print("body:", e.read().decode()[:400])
        except Exception:
            pass
        return 3
    except Exception as e:
        print("FAIL token exchange:", type(e).__name__, str(e)[:250])
        return 3

    access = tok.get("accessToken")
    if not access:
        print("FAIL: no accessToken in token response. keys:", list(tok.keys()))
        return 3
    print(f"OK  token exchange — expiresIn={tok.get('expiresIn')}s, "
          f"has_refresh={bool(tok.get('refreshToken'))}, jwt_len={len(access)}")

    # --- Step 2: full introspection ---
    try:
        _, res = post_json(GQL_URL, {"query": INTROSPECTION},
                           headers={"Authorization": f"Bearer {access}"})
    except urllib.error.HTTPError as e:
        print(f"FAIL introspection: HTTP {e.code} {e.reason}")
        try:
            print("body:", e.read().decode()[:400])
        except Exception:
            pass
        return 4
    except Exception as e:
        print("FAIL introspection:", type(e).__name__, str(e)[:250])
        return 4

    if res.get("errors") and not res.get("data"):
        print("FAIL introspection returned errors:", json.dumps(res["errors"])[:400])
        return 4

    schema = (res.get("data") or {}).get("__schema")
    if not schema:
        print("FAIL: no __schema in response. top-level keys:", list(res.keys()))
        return 4

    types = schema.get("types", [])
    qtype = (schema.get("queryType") or {}).get("name")
    mtype = (schema.get("mutationType") or {}).get("name")
    with open(OUT, "w") as f:
        json.dump(res, f, indent=2)

    # --- summary stats (no values from the data) ---
    qfields = []
    qfields_with_args = 0
    for t in types:
        if t.get("name") == qtype:
            for fl in (t.get("fields") or []):
                qfields.append(fl.get("name"))
                if fl.get("args"):
                    qfields_with_args += 1
    input_objects = [t for t in types if t.get("kind") == "INPUT_OBJECT"]
    enums = [t for t in types if t.get("kind") == "ENUM"]
    n_input_fields = sum(len(t.get("inputFields") or []) for t in input_objects)

    print(f"OK  full introspection — total_types={len(types)}, "
          f"query_fields={len(qfields)}, query_fields_with_args={qfields_with_args}")
    print(f"queryType={qtype}  mutationType={mtype}")
    print(f"input_objects={len(input_objects)} (total inputFields={n_input_fields}), "
          f"enums={len(enums)}")
    # Confirm the critical paginated queries now carry args.
    for probe in ("loans", "clients", "equities", "fundingEntities", "loanFundings"):
        for t in types:
            if t.get("name") == qtype:
                for fl in (t.get("fields") or []):
                    if fl.get("name") == probe:
                        argnames = [a.get("name") for a in (fl.get("args") or [])]
                        print(f"  {probe}(...) args: {argnames}")
    print("full schema (with args/inputFields/enumValues) written to", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

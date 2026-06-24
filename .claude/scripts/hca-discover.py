#!/usr/bin/env python3
"""One-time LIVE discovery for the Hypercore GraphQL API.

Reads CLIENT_ID + HYPERCORE_CLIENT_SECRET (the OAuth client *secret*) from the
environment, which Doppler injects at runtime:  `doppler run -- python3 ...`.

Flow (all READ-ONLY — an auth POST + a GraphQL introspection query; no mutations):
  1. POST {clientId, secret} to the token service -> JWT accessToken.
  2. POST a GraphQL introspection query to the API with Bearer <accessToken>.
  3. Write the full introspection result to disk; print ONLY summary stats.

SECURITY: never prints the secret or the JWT. stdlib only.
"""
import os, sys, json, urllib.request, urllib.error
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
OUT = "planning/preeng/001-hypercore-ask/_introspection.json"

INTROSPECTION = (
    "query IntrospectionQuery { __schema { "
    "queryType { name } mutationType { name } "
    "types { kind name "
    "fields { name type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } "
    "} } }"
)


def post_json(url, payload, headers=None):
    data = json.dumps(payload).encode()
    h = {"accept": "application/json", "content-type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.status, json.loads(r.read().decode())


def main():
    if not CLIENT_ID or not SECRET:
        print("FAIL: CLIENT_ID / HYPERCORE_CLIENT_SECRET not in env. Run via `doppler run -- python3 ...`.")
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

    # --- Step 2: introspection ---
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
        print("FAIL introspection returned errors (introspection may be disabled):",
              json.dumps(res["errors"])[:400])
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

    qfields = []
    for t in types:
        if t.get("name") == qtype:
            qfields = [fl.get("name") for fl in (t.get("fields") or [])]
    obj_types = [t.get("name") for t in types
                 if t.get("kind") == "OBJECT" and not (t.get("name") or "").startswith("__")]

    print(f"OK  introspection — total_types={len(types)}, "
          f"query_fields={len(qfields)}, object_types={len(obj_types)}")
    print(f"queryType={qtype}  mutationType={mtype}")
    peek = [n for n in qfields if any(k in (n or "").lower()
            for k in ("loan", "client", "borrow", "payment", "statement", "document",
                      "equit", "funding", "deal", "notif"))][:30]
    print("sample read-relevant query fields:", peek)
    print("full schema written to", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

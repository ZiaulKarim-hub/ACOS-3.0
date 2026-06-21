#!/usr/bin/env python3
"""test_hca_secrets.py — stdlib unittest for the credential loader (SLICE-HCA-10).

Hard gates:
  1. Missing vars yield a CLEAR, NAMED error (MissingCredentialsError) — no crash,
     no fabrication, no leaked partial data.
  2. The Credentials repr/str/format NEVER contains the secret value.
  3. is_provisioned() returns True only when BOTH vars are present and non-blank.
  4. No ANTHROPIC_API_KEY or credential value is present in the module source.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import io
import logging
import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))


def _load(modname, filename):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


secrets = _load("hca_secrets", "hca-secrets.py")

_FAKE_ENV = {
    secrets.CLIENT_ID_ENV: "test-client-id-xyz",
    secrets.API_KEY_ENV: "super-secret-api-key-never-log-me",
}
_SECRET_VALUE = "super-secret-api-key-never-log-me"
_CLIENT_ID_VALUE = "test-client-id-xyz"


# ===========================================================================
# 1. Happy path — both vars present
# ===========================================================================

class LoadCredentialsHappyPathTest(unittest.TestCase):

    def setUp(self):
        self.creds = secrets.load_credentials(env=_FAKE_ENV)

    def test_returns_credentials_object(self):
        self.assertIsInstance(self.creds, secrets.Credentials)

    def test_client_id_accessible(self):
        self.assertEqual(self.creds.client_id, _CLIENT_ID_VALUE)

    def test_api_key_accessible(self):
        """api_key must be readable for use in auth calls."""
        self.assertEqual(self.creds.api_key, _SECRET_VALUE)

    def test_credentials_is_immutable(self):
        with self.assertRaises(AttributeError):
            self.creds.api_key = "overwrite-attempt"


# ===========================================================================
# 2. Secret NEVER in repr / str / format / logging (HARD GATE)
# ===========================================================================

class SecretNeverLoggedTest(unittest.TestCase):
    """The Credentials repr/str/format must NEVER expose the secret value.

    Any code path that logs the object (print, f-string, logging) must be safe.
    """

    def setUp(self):
        self.creds = secrets.load_credentials(env=_FAKE_ENV)

    def test_repr_does_not_contain_secret(self):
        rep = repr(self.creds)
        self.assertNotIn(_SECRET_VALUE, rep,
                         f"SECRET found in repr: {rep!r} — HARD GATE FAIL")

    def test_str_does_not_contain_secret(self):
        s = str(self.creds)
        self.assertNotIn(_SECRET_VALUE, s,
                         f"SECRET found in str: {s!r} — HARD GATE FAIL")

    def test_fstring_does_not_contain_secret(self):
        s = f"{self.creds}"
        self.assertNotIn(_SECRET_VALUE, s,
                         f"SECRET found in f-string: {s!r} — HARD GATE FAIL")

    def test_repr_does_not_contain_client_id_value(self):
        rep = repr(self.creds)
        self.assertNotIn(_CLIENT_ID_VALUE, rep,
                         f"CLIENT_ID value found in repr: {rep!r} — must be redacted")

    def test_repr_contains_redacted_marker(self):
        rep = repr(self.creds)
        self.assertIn("[REDACTED]", rep,
                      "repr must show [REDACTED] placeholder, not the secret")

    def test_logging_does_not_leak_secret(self):
        """Simulate logging the Credentials object; check captured log output."""
        logger = logging.getLogger("test_hca_secrets")
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.debug("Credentials: %s", self.creds)
            logger.info("Creds repr: %r", self.creds)
            output = log_stream.getvalue()
            self.assertNotIn(_SECRET_VALUE, output,
                             f"SECRET in log output: {output!r} — HARD GATE FAIL")
        finally:
            logger.removeHandler(handler)

    def test_redacted_summary_never_has_secret(self):
        summary = self.creds.redacted_summary()
        import json
        text = json.dumps(summary)
        self.assertNotIn(_SECRET_VALUE, text)
        self.assertIn("[REDACTED]", text)

    def test_redacted_summary_shows_presence_flags(self):
        summary = self.creds.redacted_summary()
        self.assertTrue(summary["client_id_present"])
        self.assertTrue(summary["api_key_present"])


# ===========================================================================
# 3. Missing-var clear error (HARD GATE)
# ===========================================================================

class MissingCredentialsTest(unittest.TestCase):
    """Absent / blank vars must raise MissingCredentialsError naming the missing var.

    The error MUST NOT:
      - crash with an unhandled exception that might leak env context
      - fabricate a value (return empty Credentials)
      - log or embed the value of any var that IS present
    """

    def test_both_missing_raises(self):
        with self.assertRaises(secrets.MissingCredentialsError) as cm:
            secrets.load_credentials(env={})
        msg = str(cm.exception)
        self.assertIn(secrets.CLIENT_ID_ENV, msg,
                      "Error message must name the missing CLIENT_ID var")
        self.assertIn(secrets.API_KEY_ENV, msg,
                      "Error message must name the missing API_KEY var")

    def test_client_id_missing_raises(self):
        env = {secrets.API_KEY_ENV: _SECRET_VALUE}
        with self.assertRaises(secrets.MissingCredentialsError) as cm:
            secrets.load_credentials(env=env)
        self.assertIn(secrets.CLIENT_ID_ENV, str(cm.exception))
        # The present key's VALUE must not appear in the error message
        self.assertNotIn(_SECRET_VALUE, str(cm.exception))

    def test_api_key_missing_raises(self):
        env = {secrets.CLIENT_ID_ENV: _CLIENT_ID_VALUE}
        with self.assertRaises(secrets.MissingCredentialsError) as cm:
            secrets.load_credentials(env=env)
        self.assertIn(secrets.API_KEY_ENV, str(cm.exception))
        self.assertNotIn(_CLIENT_ID_VALUE, str(cm.exception))

    def test_blank_client_id_raises(self):
        env = {secrets.CLIENT_ID_ENV: "  ", secrets.API_KEY_ENV: _SECRET_VALUE}
        with self.assertRaises(secrets.MissingCredentialsError):
            secrets.load_credentials(env=env)

    def test_blank_api_key_raises(self):
        env = {secrets.CLIENT_ID_ENV: _CLIENT_ID_VALUE, secrets.API_KEY_ENV: ""}
        with self.assertRaises(secrets.MissingCredentialsError):
            secrets.load_credentials(env=env)

    def test_error_is_subclass_of_runtime_error(self):
        """Caller can catch as RuntimeError for broad degradation handling."""
        with self.assertRaises(RuntimeError):
            secrets.load_credentials(env={})


# ===========================================================================
# 4. is_provisioned()
# ===========================================================================

class IsProvisionedTest(unittest.TestCase):

    def test_true_when_both_present(self):
        self.assertTrue(secrets.is_provisioned(env=_FAKE_ENV))

    def test_false_when_both_absent(self):
        self.assertFalse(secrets.is_provisioned(env={}))

    def test_false_when_client_id_absent(self):
        env = {secrets.API_KEY_ENV: _SECRET_VALUE}
        self.assertFalse(secrets.is_provisioned(env=env))

    def test_false_when_api_key_absent(self):
        env = {secrets.CLIENT_ID_ENV: _CLIENT_ID_VALUE}
        self.assertFalse(secrets.is_provisioned(env=env))

    def test_false_when_blank(self):
        env = {secrets.CLIENT_ID_ENV: "  ", secrets.API_KEY_ENV: ""}
        self.assertFalse(secrets.is_provisioned(env=env))


# ===========================================================================
# 5. Repo grep gate — no credential string in the module source
# ===========================================================================

class RepoCredGrepTest(unittest.TestCase):
    """The module source file itself must contain no real credential value.

    Note: ANTHROPIC_API_KEY must also be absent (subscription-only invariant).
    """

    def setUp(self):
        src_path = os.path.join(_SCRIPTS_DIR, "hca-secrets.py")
        with open(src_path, "r", encoding="utf-8") as fh:
            self.source = fh.read()

    def test_no_anthropic_api_key_in_source(self):
        self.assertNotIn("ANTHROPIC_API_KEY", self.source,
                         "ANTHROPIC_API_KEY must not appear in hca-secrets.py source")

    def test_no_hardcoded_credential_value(self):
        # These would only appear if someone hardcoded a value.
        bad_strings = [
            "sk-ant-",         # Anthropic API key prefix
            "doppler-token",   # doppler personal token
        ]
        for bad in bad_strings:
            with self.subTest(bad=bad):
                self.assertNotIn(bad, self.source)

    def test_module_contains_only_var_names_not_values(self):
        """The env var NAME strings are present; no hard-coded credential values."""
        self.assertIn("CLIENT_ID", self.source)
        self.assertIn("HYPERCORE_CLIENT_SECRET", self.source)
        # No real value — we can only prove absence of known formats, but that's enough.


# ===========================================================================
# 6. Custom env var names
# ===========================================================================

class CustomEnvVarNamesTest(unittest.TestCase):
    """load_credentials() and is_provisioned() must support custom var name overrides."""

    def test_custom_var_names_happy_path(self):
        env = {"MY_CLIENT": "cid-abc", "MY_SECRET": "key-xyz"}
        creds = secrets.load_credentials(
            client_id_env="MY_CLIENT", api_key_env="MY_SECRET", env=env
        )
        self.assertEqual(creds.client_id, "cid-abc")
        self.assertEqual(creds.api_key, "key-xyz")

    def test_custom_var_names_missing_raises(self):
        with self.assertRaises(secrets.MissingCredentialsError) as cm:
            secrets.load_credentials(
                client_id_env="MY_CLIENT", api_key_env="MY_SECRET", env={}
            )
        self.assertIn("MY_CLIENT", str(cm.exception))
        self.assertIn("MY_SECRET", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

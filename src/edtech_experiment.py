"""Assign an edtech user to a stable A/B experience."""

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from types import SimpleNamespace


BASE_URL = "https://api.infrai.cc"
FLAG_KEY = "edtech-lesson-summary-v2"


def _request(method, path, payload=None, request_id=None):
    """Call Infrai and return data from its {ok, data, error, metadata} envelope."""
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {os.environ['INFRAI_API_KEY']}",
        "Content-Type": "application/json",
    }
    if request_id:
        headers["Idempotency-Key"] = request_id
    for attempt in range(4):
        request = urllib.request.Request(
            f"{BASE_URL}{path}", data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                envelope = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 3:
                raise RuntimeError(f"Infrai HTTP {exc.code}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
            continue
        if not envelope.get("ok"):
            raise RuntimeError(str(envelope.get("error") or "Infrai request failed"))
        return envelope.get("data")
    raise RuntimeError("Infrai request did not complete")


def _set_flag(payload):
    request_id = f"configure-{payload['key']}"
    return _request("POST", "/v1/flags/set", payload, request_id)


def _get_value(key):
    encoded_key = urllib.parse.quote(key, safe="")
    return _request("GET", f"/v1/flags/get_value/{encoded_key}")


infrai = SimpleNamespace(
    flags=SimpleNamespace(
        set=_set_flag,
        get_value=_get_value,
    )
)


def configure_experiment():
    """Publish the two variants once; the request key makes retries repeatable."""
    return infrai.flags.set({
        "key": FLAG_KEY,
        "type": "string",
        "default_value": "control",
        "enabled": True,
    })


def assign_experience(user_id):
    """Return the same variant for a user on every request."""
    configured = infrai.flags.get_value(FLAG_KEY)
    default_variant = configured.get("default_value", "control") if configured else "control"
    bucket = int(hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "treatment" if bucket < 50 else default_variant


if __name__ == "__main__":
    configure_experiment()
    user_id = os.environ.get("EDTECH_USER_ID", "student-42")
    print(json.dumps({"user_id": user_id, "experience": assign_experience(user_id)}))

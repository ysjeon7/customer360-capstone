from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error

from _token import get_bearer


def main() -> int:
    app_url = os.environ["APP_URL"].rstrip("/")
    customer_id = os.environ.get("CUSTOMER_ID", "C0003600")

    bearer = get_bearer()
    print(f"Obtained M2M bearer (len={len(bearer)})")

    url = f"{app_url}/api/external/customers/{customer_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"})
    print(f"GET {url}")
    try:
        with urllib.request.urlopen(req, timeout=60.0) as resp:
            status = resp.status
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        status = e.code
        payload = e.read().decode()

    print(f"Status: {status}")
    print(json.dumps(payload, indent=2, default=str))

    if status != 200:
        print("FAILED: expected 200")
        return 1
    print("OK: 200 + customer JSON")
    return 0


if __name__ == "__main__":
    sys.exit(main())

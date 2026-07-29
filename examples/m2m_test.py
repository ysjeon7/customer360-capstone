from __future__ import annotations

import json
import os
import sys

import httpx

from _token import get_bearer


def main() -> int:
    app_url = os.environ["APP_URL"].rstrip("/")
    customer_id = os.environ.get("CUSTOMER_ID", "C0003600")

    bearer = get_bearer()
    print(f"Obtained M2M bearer (len={len(bearer)})")

    url = f"{app_url}/api/external/customers/{customer_id}"
    resp = httpx.get(url, headers={"Authorization": f"Bearer {bearer}"}, timeout=60.0)

    print(f"GET {url}")
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2, default=str))

    if resp.status_code != 200:
        print("FAILED: expected 200")
        return 1
    print("OK: 200 + customer JSON")
    return 0


if __name__ == "__main__":
    sys.exit(main())

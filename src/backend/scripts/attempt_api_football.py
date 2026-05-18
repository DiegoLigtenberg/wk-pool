import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://v3.football.api-sports.io"
WORLD_CUP_LEAGUE_ID = 1
WORLD_CUP_SEASON = 2026
API_KEY_ENV_NAME = "API_FOOTBALL_KEY"


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
            continue

        key, value = clean_line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def call_api_football(path: str, params: dict[str, str | int]) -> dict[str, object]:
    load_env_file()
    api_key = os.environ.get(API_KEY_ENV_NAME)
    if not api_key:
        raise RuntimeError(f"Missing {API_KEY_ENV_NAME} environment variable.")

    url = f"{BASE_URL}{path}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "x-apisports-key": api_key,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    try:
        data = call_api_football(
            "/fixtures",
            {"league": WORLD_CUP_LEAGUE_ID, "season": WORLD_CUP_SEASON},
        )
    except RuntimeError as error:
        print(error)
        print(f"Set it in .env or PowerShell with: $env:{API_KEY_ENV_NAME} = 'your-key'")
        return 2
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.reason}")
        print(error.read().decode("utf-8"))
        return 1
    except URLError as error:
        print(f"Request failed: {error.reason}")
        return 1

    response = data.get("response", [])
    errors = data.get("errors")
    print(f"Errors: {errors}")
    print(f"Fixture count: {len(response) if isinstance(response, list) else 0}")

    if isinstance(response, list):
        for fixture in response[:5]:
            print(json.dumps(fixture, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

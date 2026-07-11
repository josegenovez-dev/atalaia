import time
import requests

from config import APP_ID, APP_SECRET, BASE_URL

_token_cache = {
    "token": None,
    "expires_at": 0,
}


def get_access_token():
    agora = time.time()

    if (
        _token_cache["token"]
        and agora < _token_cache["expires_at"]
    ):
        return _token_cache["token"]

    if not APP_ID or not APP_SECRET:
        print(
            "ERRO: APP_ID ou APP_SECRET não configurados.",
            flush=True,
        )
        return None

    try:
        response = requests.post(
            f"{BASE_URL}/auth/app_access_token",
            json={
                "app_id": APP_ID,
                "app_secret": APP_SECRET,
            },
            timeout=20,
        )

        print(
            "TOKEN RESPONSE:",
            response.status_code,
            flush=True,
        )

        print(
            "TOKEN BODY:",
            response.text,
            flush=True,
        )

        if not response.ok:
            return None

        data = response.json()

        token = (
            data.get("app_access_token")
            or data.get("access_token")
        )

        if not token:
            print(
                "ERRO: SeaTalk não retornou token.",
                flush=True,
            )
            return None

        expire = data.get("expire") or data.get(
            "expires_in"
        )

        try:
            expire = int(expire)
        except (TypeError, ValueError):
            expire = 7200

        if expire > agora:
            expires_at = expire - 120
        else:
            expires_at = agora + max(
                expire - 120,
                60,
            )

        _token_cache["token"] = token
        _token_cache["expires_at"] = expires_at

        return token

    except requests.RequestException as error:
        print(
            "ERRO AO GERAR TOKEN:",
            repr(error),
            flush=True,
        )
        return None

    except ValueError as error:
        print(
            "ERRO AO LER TOKEN:",
            repr(error),
            flush=True,
        )
        return None


def send_private_message(employee_code, text):
    try:
        token = get_access_token()

        if not token:
            print(
                "ERRO: token não gerado.",
                flush=True,
            )
            return False

        if not employee_code:
            print(
                "ERRO: employee_code vazio.",
                flush=True,
            )
            return False

        mensagem = str(text or "").strip()

        if not mensagem:
            print(
                "ERRO: mensagem vazia.",
                flush=True,
            )
            return False

        payload = {
            "employee_code": str(employee_code),
            "message": {
                "tag": "text",
                "text": {
                    "content": mensagem[:3900],
                },
            },
        }

        response = requests.post(
            f"{BASE_URL}/messaging/v2/single_chat",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )

        print(
            "SEND PRIVATE RESPONSE:",
            response.status_code,
            flush=True,
        )

        print(
            "SEND PRIVATE BODY:",
            response.text,
            flush=True,
        )

        return 200 <= response.status_code < 300

    except requests.RequestException as error:
        print(
            "ERRO HTTP AO ENVIAR:",
            repr(error),
            flush=True,
        )
        return False

    except Exception as error:
        print(
            "ERRO AO ENVIAR:",
            repr(error),
            flush=True,
        )
        return False

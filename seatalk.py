import requests
from config import APP_ID, APP_SECRET, BASE_URL


def get_access_token():
    response = requests.post(
        f"{BASE_URL}/auth/app_access_token",
        json={
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        },
        timeout=20
    )

    print("TOKEN RESPONSE:", response.status_code)
    print("TOKEN BODY:", response.text)

    data = response.json()
    return data.get("app_access_token")


def send_private_message(employee_code, text):
    try:
        token = get_access_token()

        if not token:
            print("ERRO: token não gerado")
            return

        payload = {
            "employee_code": str(employee_code),
            "message": {
                "tag": "text",
                "text": {
                    "content": text[:3900]
                }
            }
        }

        response = requests.post(
            f"{BASE_URL}/messaging/v2/single_chat",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20
        )

        print("SEND RESPONSE:", response.status_code)
        print("SEND BODY:", response.text)

    except Exception as e:
        print("ERRO AO ENVIAR:", repr(e))

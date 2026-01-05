# linkedin_api.py
import requests
from datetime import datetime, timedelta
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, LINKEDIN_API_VERSION, ORGANIZATION_ID

BASE_URL = "https://api.linkedin.com/v2/ugcPosts"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"


def build_auth_url(state: str) -> str:
    scope = "w_member_social openid profile email"
    return (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope={scope}&state={state}"
    )


def exchange_code_for_token(code: str) -> tuple[str, datetime]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=10)
    if not resp.ok:
        print("LinkedIn token error:", resp.status_code, resp.text)
        return "", datetime.utcnow()  # or handle gracefully
    payload = resp.json()
    access_token = payload["access_token"]
    expires_in = int(payload.get("expires_in", 0))
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    return access_token, expires_at



def get_linkedin_user_id(access_token: str) -> str:
    url = "https://api.linkedin.com/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.ok:
        return resp.json().get("sub", "")  # 'sub' is the person ID
    return ""


def post_text_to_linkedin_as_user(text: str, access_token: str) -> tuple[bool, str]:
    person_id = get_linkedin_user_id(access_token)
    if not person_id:
        return False, "Could not fetch user id"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Linkedin-Version": LINKEDIN_API_VERSION,  # e.g., "202502"
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",  # Important for v2 APIs
    }

    body = {
        "author": f"urn:li:person:{person_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    resp = requests.post(BASE_URL, headers=headers, json=body, timeout=10)
    if resp.status_code == 201:
        return True, "Post published"
    return False, f"{resp.status_code}: {resp.text}"

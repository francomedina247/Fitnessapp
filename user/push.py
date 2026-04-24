"""
Push notification helpers using the Expo Push Notification Service.

Expo acts as a proxy to FCM (Android) and APNs (iOS) so no platform
credentials are needed on the backend — only the Expo push token that
the mobile app registers after the user grants permission.

Docs: https://docs.expo.dev/push-notifications/sending-notifications/
"""

import logging
from typing import Optional
import urllib.request
import urllib.error
import json

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    sound: str = "default",
    badge: Optional[int] = None,
) -> bool:
    """
    Send a single push notification via the Expo Push API.
    Returns True on success, False on any failure.
    """
    if not token or not token.startswith("ExponentPushToken["):
        logger.warning("send_push_notification: invalid or missing token: %s", token)
        return False

    payload = {
        "to": token,
        "title": title,
        "body": body,
        "sound": sound,
        "data": data or {},
    }
    if badge is not None:
        payload["badge"] = badge

    try:
        req = urllib.request.Request(
            EXPO_PUSH_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            # Expo returns {"data": {"status": "ok"}} on success
            status = result.get("data", {}).get("status")
            if status == "ok":
                return True
            logger.warning("Expo push returned non-ok status: %s", result)
            return False
    except urllib.error.URLError as exc:
        logger.error("send_push_notification network error: %s", exc)
        return False
    except Exception as exc:
        logger.error("send_push_notification unexpected error: %s", exc)
        return False


def send_push_to_user(user, title: str, body: str, data: Optional[dict] = None) -> bool:
    """Convenience wrapper — looks up the user's stored push token."""
    token = getattr(user, "push_token", None)
    if not token:
        return False
    return send_push_notification(token, title, body, data)


def broadcast_push(users, title: str, body: str, data: Optional[dict] = None) -> int:
    """
    Send the same notification to a list of users.
    Returns the count of successful deliveries.
    """
    sent = 0
    for user in users:
        if send_push_to_user(user, title, body, data):
            sent += 1
    return sent

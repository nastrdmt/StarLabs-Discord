import string
from random import choice

from curl_cffi import requests
from loguru import logger
import time


def get_guild_ids(client: requests.Session, invite_code: str, account_index: int) -> tuple[str, str, bool]:
    try:
        resp = client.get(f"https://discord.com/api/v9/invites/{invite_code}")

        if "You need to verify your account" in resp.text:
            logger.error(f"{account_index} | Account needs verification (Email code etc).")
            return "verification_failed", "", False

        location_guild_id = resp.json()['guild_id']
        location_channel_id = resp.json()['channel']['id']

        return location_guild_id, location_channel_id, True

    except Exception as err:
        logger.error(f"{account_index} | Failed to get guild ids: {err}")
        return "", "", False


def calculate_nonce() -> str:
    unix_ts = time.time()
    return str((int(unix_ts) * 1000 - 1420070400000) * 4194304)


def generate_random_session_id() -> str:
    return "".join(choice(string.ascii_letters + string.digits) for _ in range(32))

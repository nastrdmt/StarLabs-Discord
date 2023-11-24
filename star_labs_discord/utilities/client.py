from curl_cffi import requests

from .. import utilities


def create_client(proxy: str, discord_token: str, user_agent: str) -> requests.Session:
    session = requests.Session(impersonate="chrome110", timeout=60)

    if proxy:
        session.proxies.update({
            "http": "http://" + proxy,
            "https": "http://" + proxy,
        })

    session.headers.update({
        "authorization": discord_token,
        "x-super-properties": utilities.create_x_super_properties(user_agent)
    })

    return session

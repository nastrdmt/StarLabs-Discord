from curl_cffi import requests
from loguru import logger


def init_cf(account_index: int, client: requests.Session, user_agent: str) -> bool:
    try:
        resp = client.get("https://discord.com/login",
                          headers={
                              'authority': 'discord.com',
                              'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                              'accept-language': 'en-US,en;q=0.9',
                              'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
                              'sec-ch-ua-mobile': '?0',
                              'sec-ch-ua-platform': '"Windows"',
                              'sec-fetch-dest': 'document',
                              'sec-fetch-mode': 'navigate',
                              'sec-fetch-site': 'none',
                              'sec-fetch-user': '?1',
                              'upgrade-insecure-requests': '1',
                              'user-agent': user_agent,
                          }
                          )

        if set_response_cookies(client, resp):
            logger.success(f"{account_index} | Initialized new cookies.")
            return True
        else:
            logger.error(f"{account_index} | Failed to initialize new cookies.")
            return False

    except Exception as err:
        logger.error(f"{account_index} | Failed to initialize new cookies: {err}")
        return False


def set_response_cookies(client: requests.Session, response: requests.Response) -> bool:
    try:
        cookies = response.headers.get_list("set-cookie")
        for cookie in cookies:
            try:
                key, value = cookie.split(';')[0].strip().split("=")
                client.cookies.set(name=key, value=value, domain="discord.com", path="/")

            except:
                pass

        return True

    except Exception as err:
        logger.error(f"Failed to set response cookies: {err}")
        return False

from curl_cffi import requests
from loguru import logger


def init_cf(account_index: int, client: requests.Session, user_agent: str) -> bool:
    try:
        resp = client.get("https://discord.com/login",
                          headers={
                              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                              'Connection': 'keep-alive',
                              'Sec-Fetch-Dest': 'document',
                              'Sec-Fetch-Mode': 'navigate',
                              'Sec-Fetch-Site': 'none',
                              'Sec-Fetch-User': '?1',
                              'Upgrade-Insecure-Requests': '1',
                              'User-Agent': user_agent,
                              'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
                              'sec-ch-ua-mobile': '?0',
                              'sec-ch-ua-platform': '"Windows"',
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

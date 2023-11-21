# quick api for the https://capmonster.cloud/ captcha service #
from typing import Any

from curl_cffi import requests
from loguru import logger
from time import sleep
import requests as default_requests


class Capmonstercloud:
    def __init__(self, account_index: int, api_key: str, client: requests.Session, proxy: str):
        self.account_index = account_index
        self.api_key = api_key
        self.client = client
        self.proxy = proxy

    # returns gRecaptchaResponse, resp_key and success status (False if something failed)
    def solve_hcaptcha(self, site_key: str, website_url: str, captcha_rqdata: str, user_agent: str) -> tuple[str, bool]:
        try:
            captcha_data = {
                "clientKey": self.api_key,
                "task":
                    {
                        "type": "HCaptchaTask",
                        "websiteURL": website_url,
                        "websiteKey": site_key,
                        "data": captcha_rqdata,
                        "userAgent": user_agent,
                        "fallbackToActualUA": True,
                        "proxyType": "http",
                        "proxyAddress": self.proxy.split("@")[1].split(":")[0],
                        "proxyPort": self.proxy.split("@")[1].split(":")[1],
                        "proxyLogin": self.proxy.split("@")[0].split(":")[0],
                        "proxyPassword": self.proxy.split("@")[0].split(":")[1]
                    }
            }

            resp = self.client.post("https://api.capmonster.cloud/createTask",
                                    json=captcha_data)

            if resp.json()["errorId"] == 0:
                logger.info(f"{self.account_index} | Starting to solve the captcha...")
                return self.get_captcha_result(resp.json()["taskId"])

            else:
                logger.error(f"{self.account_index} | Failed to send captcha request: {resp.json()['errorDescription']}")
                return "", False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to send captcha request to capmonster: {err}")
            return "", False

    # returns gRecaptchaResponse, resp_key and success status (False if something failed)
    def solve_turnstile(self, site_key: str, website_url: str) -> tuple[str, bool]:
        try:
            captcha_data = {
                "clientKey": self.api_key,
                "task":
                    {
                        "type": "TurnstileTaskProxyless",
                        "websiteURL": website_url,
                        "websiteKey": site_key,
                    }
            }

            resp = self.client.post("https://api.capmonster.cloud/createTask",
                                    json=captcha_data)

            if resp.json()["errorId"] == 0:
                logger.info(f"{self.account_index} | Starting to solve the CF captcha...")
                return self.get_captcha_result(resp.json()["taskId"], "cf")

            else:
                logger.error(f"{self.account_index} | Failed to send CF captcha request: {resp.json()['errorDescription']}")
                return "", False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to send CF captcha request to capmonster: {err}")
            return "", False

    def get_captcha_result(self, task_id: str, captcha_type: str = "hcaptcha") -> tuple[Any, bool] | tuple[str, str, bool]:
        for i in range(30):
            try:
                resp = self.client.post("https://api.capmonster.cloud/getTaskResult/",
                                        json={
                                            "clientKey": self.api_key,
                                            "taskId": int(task_id)
                                        })

                if resp.json()["errorId"] == 0:
                    if resp.json()["status"] == "ready":

                        logger.success(f"{self.account_index} | Captcha solved!")
                        if captcha_type == "cf":
                            g_recaptcha_response = resp.json()['solution']["token"]

                        elif captcha_type == "image_to_text":
                            g_recaptcha_response = resp.json()['solution']["text"]

                        else:
                            g_recaptcha_response = resp.json()['solution']["gRecaptchaResponse"]

                        return g_recaptcha_response, True

                else:
                    logger.error(f"{self.account_index} | Failed to get captcha solution: {resp.json()['errorDescription']}")

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to get captcha solution: {err}")
                return "", "", False
            # sleep between result requests
            sleep(6)

        return "", "", False


class TwoCaptcha:
    def __init__(self, account_index: int, api_key: str, client: requests.Session, proxy: str):
        self.account_index = account_index
        self.api_key = api_key
        self.client = client
        self.proxy = proxy

    # returns gRecaptchaResponse, resp_key and success status (False if something failed)
    def solve_image_to_text(self, image_base64: str, captcha_options: {}) -> tuple[str, bool]:
        try:
            captcha_data = {
                "key": self.api_key,
                "method": "base64",
                "body": str(image_base64),
                "json": 1
            }

            captcha_data.update(captcha_options)

            resp = default_requests.post("http://2captcha.com/in.php",
                                         data=captcha_data)

            if resp.json()["status"] == 1:
                logger.info(f"{self.account_index} | Starting to solve the captcha...")
                return self.get_captcha_result(resp.json()["request"])

            else:
                logger.error(f"{self.account_index} | Failed to send captcha request: {resp.json()['errorDescription']}")
                return "", False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to send captcha request to 2captcha: {err}")
            return "", False

    def get_captcha_result(self, task_id: str) -> tuple[Any, bool] | tuple[str, str, bool]:
        for i in range(30):
            try:
                resp = default_requests.post("http://2captcha.com/res.php",
                                             params={
                                                 "key": self.api_key,
                                                 "action": "get",
                                                 "id": int(task_id),
                                                 "json": 1
                                             })

                if resp.json()["status"] == 1:
                    logger.success(f"{self.account_index} | Captcha solved! Answer -> {resp.json()['request']}")

                    response = resp.json()['request']
                    return response, True

                elif "CAPCHA_NOT_READY" in resp.text:
                    pass

                else:
                    raise Exception(resp.text)

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to get captcha solution: {err}")
                return "", "", False
            # sleep between result requests
            sleep(5)

        return "", "", False

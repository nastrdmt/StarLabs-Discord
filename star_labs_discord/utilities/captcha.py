# quick api for the https://capmonster.cloud/ captcha service #
import requests as default_requests
from curl_cffi import requests
from loguru import logger
from time import sleep
from typing import Any


class Capmonstercloud:
    def __init__(self, account_index: int, api_key: str, client: requests.Session, proxy: str):
        self.account_index = account_index
        self.api_key = api_key
        self.client = client
        self.proxy = proxy

    # returns gRecaptchaResponse, resp_key and success status (False if something failed)
    def solve_hcaptcha(self, site_key: str, website_url: str, captcha_rqdata: str, user_agent: str) -> tuple[str, bool]:
        try:
            if self.client.proxies:
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

            else:
                captcha_data = {
                    "clientKey": self.api_key,
                    "task":
                        {
                            "type": "HCaptchaTaskProxyless",
                            "websiteURL": website_url,
                            "websiteKey": site_key,
                            "data": captcha_rqdata,
                            "userAgent": user_agent,
                            "fallbackToActualUA": True,
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
                    pass

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to get captcha solution: {err}")
                return "", False
            # sleep between result requests
            sleep(6)

        logger.error(f"{self.account_index} | Failed to get captcha solution")
        return "", False


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

    def solve_hcaptcha(self, site_key: str, website_url: str, captcha_rqdata: str, user_agent: str) -> tuple[str, bool]:
        try:
            captcha_data = {
                "key": self.api_key,
                "method": "hcaptcha",
                "sitekey": site_key,
                "pageurl": website_url,
                "data": captcha_rqdata,
                "userAgent": user_agent,
                "json": 1
            }

            if self.client.proxies:
                captcha_data['proxy'] = self.proxy
                captcha_data['proxyType'] = "http"

            resp = self.client.post("http://2captcha.com/in.php",
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

    def get_captcha_result(self, task_id: str) -> tuple[Any, bool] | tuple[str, bool]:
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
                    logger.success(f"{self.account_index} | Captcha solved!")

                    response = resp.json()['request']
                    return response, True

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to get captcha solution: {err}")
                return "", False
            # sleep between result requests
            sleep(5)

        logger.error(f"{self.account_index} | Failed to get captcha solution")
        return "", False


class HCoptcha:
    def __init__(self, account_index: int, api_key: str, client: requests.Session, proxy: str):
        self.account_index = account_index
        self.api_key = api_key
        self.client = client
        self.proxy = proxy

    # returns gRecaptchaResponse, resp_key and success status (False if something failed)
    def solve_hcaptcha(self, url: str, captcha_rqdata: str) -> tuple[str, bool]:
        try:
            if self.proxy != "":
                captcha_data = {
                    "task_type": "hcaptchaEnterprise",
                    "api_key": self.api_key,
                    "data": {
                        "sitekey": "a9b5fb07-92ff-493f-86fe-352a2803b3df",
                        "url": url,
                        "proxy": self.proxy,
                        "rqdata": captcha_rqdata
                    }
                }
            else:
                captcha_data = {
                    "task_type": "hcaptchaEnterprise",
                    "api_key": self.api_key,
                    "data": {
                        "sitekey": "a9b5fb07-92ff-493f-86fe-352a2803b3df",
                        "url": url,
                        "proxy": "",
                        "rqdata": captcha_rqdata
                    }
                }

            resp = default_requests.post("https://api.hcoptcha.online/api/createTask",
                                         json=captcha_data)

            if resp.status_code == 200:
                logger.info(f"{self.account_index} | Starting to solve hcoptcha...")
                return self.get_captcha_result(resp.json()["task_id"])

            else:
                logger.error(f"{self.account_index} | Failed to send hcoptcha request: {resp.json()['message']}")
                return "", False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to send hcoptcha request to 2captcha: {err}")
            return "", False

    def get_captcha_result(self, task_id: str) -> tuple[Any, bool] | tuple[str, bool]:
        for i in range(30):
            try:
                resp = default_requests.post("https://api.hcoptcha.online/api/getTaskData",
                                             json={
                                                 "api_key": self.api_key,
                                                 "task_id": task_id
                                             })

                if resp.status_code == 200:
                    if resp.json()['error']:
                        logger.error(f"{self.account_index} | Hcoptcha failed!")
                        return "", False

                    elif resp.json()['task']['state'] == "completed":
                        logger.success(f"{self.account_index} | Hcoptcha solved!")

                        response = resp.json()['task']['captcha_key']
                        return response, True

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to get hcoptcha solution: {err}")
                return "", False
            # sleep between result requests
            sleep(7)

        logger.error(f"{self.account_index} | Failed to get hcoptcha solution")
        return "", False


class Capsolver:
    def __init__(self, account_index: int, api_key: str, client: requests.Session, proxy: str):
        self.account_index = account_index
        self.api_key = api_key
        self.client = client
        self.proxy = proxy

    # returns gRecaptchaResponse, resp_key and success status (False if something failed)
    def solve_hcaptcha(self, url: str, captcha_rqdata: str, site_key: str, user_agent: str) -> tuple[str, bool]:
        try:
            if self.proxy != "":
                captcha_data = {
                    "clientKey": self.api_key,
                    "task": {
                        "type": "HCaptchaTurboTask",
                        "websiteURL": url,
                        "websiteKey": site_key,
                        "isInvisible": False,
                        "enterprisePayload": {
                            "rqdata": captcha_rqdata
                        },
                        # http:ip:port:user:pass
                        "proxy": f"http:{self.proxy.split('@')[1].split(':')[0]}:{self.proxy.split('@')[1].split(':')[1]}:{self.proxy.split('@')[0].split(':')[0]}:{self.proxy.split('@')[0].split(':')[1]}",
                        "userAgent": user_agent
                    }
                }
            else:
                logger.error(f"{self.account_index} | Capsolver requires proxy for solving HCaptcha.")
                return "", False

            resp = default_requests.post("https://api.capsolver.com/createTask",
                                         json=captcha_data)

            if resp.status_code == 200:
                logger.info(f"{self.account_index} | Starting to solve hcaptcha...")
                return self.get_captcha_result(resp.json()["taskId"])

            else:
                logger.error(f"{self.account_index} | Failed to send hcaptcha request: {resp.json()['errorDescription']}")
                return "", False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to send hcaptcha request to 2captcha: {err}")
            return "", False

    def get_captcha_result(self, task_id: str) -> tuple[Any, bool] | tuple[str, bool]:
        for i in range(30):
            try:
                resp = default_requests.post("https://api.capsolver.com/getTaskResult",
                                             json={
                                                 "clientKey": self.api_key,
                                                 "taskId": task_id
                                             })

                if resp.status_code == 200:
                    if resp.json()['errorId'] != 0:
                        logger.error(f"{self.account_index} | Hcaptcha failed!")
                        return "", False

                    elif resp.json()['status'] == "ready":
                        logger.success(f"{self.account_index} | Hcaptcha solved!")

                        response = resp.json()['solution']['gRecaptchaResponse']
                        return response, True

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to get hcaptcha solution: {err}")
                return "", False
            # sleep between result requests
            sleep(7)

        logger.error(f"{self.account_index} | Failed to get hcaptcha solution")
        return "", False


class AntiCaptcha:
    def __init__(self, account_index: int, api_key: str, client: requests.Session, proxy: str):
        self.account_index = account_index
        self.api_key = api_key
        self.client = client
        self.proxy = proxy

    # returns gRecaptchaResponse, resp_key and success status (False if something failed)
    def solve_hcaptcha(self, url: str, captcha_rqdata: str, site_key: str, user_agent: str) -> tuple[str, bool]:
        try:
            # if self.proxy != "":
            #     captcha_data = {
            #         "clientKey": self.api_key,
            #         "task":
            #             {
            #                 "type": "HCaptchaTask",
            #                 "websiteURL": url,
            #                 "websiteKey": site_key,
            #                 "proxyType": "http",
            #                 "proxyAddress": self.proxy.split('@')[1].split(':')[0],
            #                 "proxyPort": self.proxy.split('@')[1].split(':')[1],
            #                 "proxyLogin": self.proxy.split('@')[0].split(':')[0],
            #                 "proxyPassword": self.proxy.split('@')[0].split(':')[1],
            #                 "isInvisible": False,
            #                 "enterprisePayload": {
            #                     "rqdata": captcha_rqdata,
            #                     "sentry": True
            #                 }
            #             },
            #         "softId": 0
            #     }
            # else:
            captcha_data = {
                "clientKey": self.api_key,
                "task":
                    {
                        "type": "HCaptchaTaskProxyless",
                        "websiteURL": url,
                        "websiteKey": site_key,
                        "isInvisible": False,
                        "enterprisePayload": {
                            "rqdata": captcha_rqdata,
                            "sentry": True
                        }
                    },
                "softId": 0
            }

            resp = default_requests.post("https://api.anti-captcha.com/createTask",
                                         json=captcha_data)

            if resp.status_code == 200:
                logger.info(f"{self.account_index} | Starting to solve hcaptcha...")
                return self.get_captcha_result(resp.json()["taskId"])

            else:
                logger.error(f"{self.account_index} | Failed to send hcaptcha request: {resp.json()['errorDescription']}")
                return "", False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to send hcaptcha request to AntiCaptcha: {err}")
            return "", False

    def get_captcha_result(self, task_id: str) -> tuple[Any, bool] | tuple[str, bool]:
        for i in range(30):
            try:
                resp = default_requests.post("https://api.anti-captcha.com/getTaskResult",
                                             json={
                                                 "clientKey": self.api_key,
                                                 "taskId": task_id
                                             })

                if resp.status_code == 200:
                    if resp.json()['errorId'] != 0:
                        logger.error(f"{self.account_index} | Hcaptcha failed!")
                        return "", False

                    elif resp.json()['status'] == "ready":
                        logger.success(f"{self.account_index} | Hcaptcha solved!")

                        response = resp.json()['solution']['gRecaptchaResponse']
                        return response, True

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to get hcaptcha solution: {err}")
                return "", False
            # sleep between result requests
            sleep(7)

        logger.error(f"{self.account_index} | Failed to get hcaptcha solution")
        return "", False

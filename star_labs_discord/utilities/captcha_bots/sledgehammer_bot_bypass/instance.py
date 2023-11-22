from discum.utils.button import Buttoner
from curl_cffi import requests
from functools import partial
from loguru import logger
from time import sleep
import discum

from ... import calculate_nonce


class SledgehammerBot:
    def __init__(self, account_index: int, client: requests.Session, user_agent: str, proxy: str, discord_token: str, config: dict, capmonster_client,
                 guild_id: str, channel_id: str, message_id: str, two_captcha_client):

        self.account_index = account_index
        self.discord_token = discord_token
        self.user_agent = user_agent
        self.http_client = client
        self.config = config
        self.proxy = proxy

        self.two_captcha_client = two_captcha_client
        self.discum_client: None | discum.Client = None
        self.capmonster_client = capmonster_client
        self.channel_id: str = channel_id
        self.message_id: str = message_id
        self.guild_id: str = guild_id

        self.sledge_message_id: str = ""
        self.verified: bool = False
        self.captcha_in_process: bool = False

    def bypass_sledgehammer_bot(self) -> bool:
        self.start_websockets()

        if self.verified:
            return True

        return False

    def listen_events(self, response):
        if response.event.ready_supplemental:
            self.press_verify_button()
            for retry in range(180):
                sleep(1)

            logger.error(f"{self.account_index} | Unable to solve SledgehammerBot. Too much time has passed.")
            self.end_websockets()

        if response.event.message:
            if "You are already being verified" in str(response.raw):
                logger.success(f"{self.account_index} | You are already verified.")
                self.verified = True
                self.end_websockets()

        if response.event.message_updated:
            if "You are already verified" in str(response.raw):
                logger.success(f"{self.account_index} | You are already verified.")
                self.verified = True
                self.end_websockets()

            elif "You have been verified" in str(response.raw):
                logger.success(f"{self.account_index} | You are successfully verified!")
                self.verified = True
                self.end_websockets()

            elif "Verify yourself to gain access" in str(response.raw):
                self.captcha_in_process = True
                message = response.raw.get("d")

                self.sledge_message_id = message['id']
                captcha_answer = str(message).split("**")[1].strip().lower()

                if self.send_captcha_solution(captcha_answer):
                    self.verified = True

                self.end_websockets()

    def start_websockets(self):
        proxy_str = f"http://{self.proxy}"

        self.discum_client = discum.Client(token=self.discord_token, proxy=proxy_str, log={"console": False, "file": False})
        prepare = partial(self.listen_events)

        self.discum_client.gateway.command(prepare)
        self.discum_client.gateway.run(True)

    def end_websockets(self):
        self.discum_client.gateway.close()

    def press_verify_button(self) -> bool:
        try:
            msg = self.discum_client.getMessage(self.channel_id, self.message_id).json()

            try:
                if msg["message"] in ("Unknown Channel", "Missing Access"):
                    logger.success(f"{self.account_index} | Account has already been verified or not invited.")
                    self.discum_client.gateway.close()
                    return False
            except:
                pass

            message = msg[0]

            button_manager = Buttoner(message.get("components"))

            self.discum_client.click(
                message.get("author").get("id"),
                message.get("channel_id"),
                message.get("id"),
                message.get("flags"),
                self.guild_id,
                data=button_manager.getButton("Start Verification"),
            )
            logger.success(f"{self.account_index} | Verify button pressed.")
            return True

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to press verify button: {err}")
            return False

    def send_captcha_solution(self, captcha_answer: str) -> bool:
        for retry in range(3):
            try:

                data = {
                    'type': 3,
                    'nonce': calculate_nonce(),
                    'guild_id': self.guild_id,
                    'channel_id': self.channel_id,
                    'message_flags': 64,
                    'message_id': self.sledge_message_id,
                    'application_id': '863168632941969438',
                    'session_id': self.discum_client.gateway.session_id,
                    'data': {
                        'component_type': 3,
                        'custom_id': 'verificationRequest.en',
                        'type': 3,
                        'values': [
                            captcha_answer,
                        ],
                    },
                }

                resp = self.http_client.post("https://discord.com/api/v10/interactions",
                                             headers={
                                                 'authority': 'discord.com',
                                                 'accept': '*/*',
                                                 'content-type': 'application/json',
                                                 'origin': 'https://discord.com',
                                                 'sec-ch-ua-mobile': '?0',
                                                 'sec-ch-ua-platform': '"Windows"',
                                                 'sec-fetch-dest': 'empty',
                                                 'sec-fetch-mode': 'cors',
                                                 'sec-fetch-site': 'same-origin',
                                                 'x-debug-options': 'bugReporterEnabled',
                                                 'x-discord-locale': 'en-US',
                                             },
                                             json=data
                                             )

                if resp.status_code != 204:
                    logger.error(f"{self.account_index} | Failed to send a result to SledgehammerBot.")
                    sleep(1)
                    if retry == 2:
                        self.captcha_in_process = False
                        self.end_websockets()
                        return False

                    continue

                elif resp.status_code == 204:
                    logger.success(f"{self.account_index} | Successfully sent the captcha result to the SledgehammerBot.")
                    return True

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to send captcha solution to SledgehammerBot -> {err}")
                if retry == 2:
                    self.captcha_in_process = False
                    sleep(2)
                    return False

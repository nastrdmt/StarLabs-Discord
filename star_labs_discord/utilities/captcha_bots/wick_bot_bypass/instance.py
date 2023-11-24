from discum.utils.button import Buttoner
import requests as default_requests
from curl_cffi import requests
from functools import partial
from loguru import logger
from time import sleep
from io import BytesIO
from PIL import Image
import base64
import discum

from ... import calculate_nonce


class WickBot:
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

        self.wick_message_id: str = ""
        self.verified: bool = False
        self.captcha_in_process: bool = False

    def bypass_wick_bot(self) -> bool:
        self.start_websockets()

        if self.verified:
            return True

        return False

    def listen_events(self, response):
        if response.event.ready_supplemental:
            self.press_verify_button()
            for retry in range(180):
                sleep(1)

            logger.error(f"{self.account_index} | Unable to solve WickBot. Too much time has passed.")
            self.end_websockets()

        if response.event.message:
            if "You are already being verified" in str(response.raw):
                logger.success(f"{self.account_index} | You are already verified.")
                self.verified = True
                self.end_websockets()

            # press Continue button
            elif "Please type the captcha below" in str(response.raw):
                self.captcha_in_process = True
                message = response.raw.get("d")
                self.wick_message_id = message['id']
                if self.solve_captcha(message):
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

    def start_websockets(self):
        if self.proxy:
            proxy_str = f"http://{self.proxy}"
            self.discum_client = discum.Client(token=self.discord_token, proxy=proxy_str, log={"console": False, "file": False})
        else:
            self.discum_client = discum.Client(token=self.discord_token, log={"console": False, "file": False})

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
                data=button_manager.getButton("Verify"),
            )
            logger.success(f"{self.account_index} | Verify button pressed.")
            return True

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to press verify button: {err}")
            return False

    def solve_captcha(self, message):
        try:

            captcha_options = {
                "min_len": 6,
                "max_len": 6,
                "textinstructions": "The image contains 6 big GREEN SYMBOLS, not gray"
            }

            captcha_image_url = message["embeds"][0]['image']['url']
            custom_wick_id = message['components'][0]['components'][0]['custom_id'].split('_')[-1]
            simple_id = message.get("id")

            response = default_requests.get(captcha_image_url)

            img = Image.open(BytesIO(response.content))
            img = img.resize((int(img.size[0] * 0.9), int(img.size[1] * 0.9)), Image.LANCZOS)
            img = img.convert("RGB")

            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=70, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()

            result, ok = self.two_captcha_client.solve_image_to_text(img_str, captcha_options)

            if ok:
                return self.send_captcha_solution_numbers(result, custom_wick_id, simple_id)

            else:
                return False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to solve the captcha: {err}")
            return False

    def send_captcha_solution_numbers(self, result: str, custom_wick_id: str, simple_id: str) -> bool:
        for retry in range(3):
            try:
                nonce = calculate_nonce()

                data = {
                    'type': 5,
                    'application_id': '898193246088478790',
                    'channel_id': self.channel_id,
                    'guild_id': self.guild_id,
                    'data': {
                        'id': simple_id,
                        'custom_id': f'modalmmbrver_{custom_wick_id}',
                        'components': [
                            {
                                'type': 1,
                                'components': [
                                    {
                                        'type': 4,
                                        'custom_id': 'answer',
                                        'value': result.upper(),
                                    },
                                ],
                            },
                        ],
                    },
                    'session_id': self.discum_client.gateway.session_id,
                    'nonce': nonce,
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
                    logger.error(f"{self.account_index} | Failed to send a result to WickBot.")
                    sleep(1)
                    if retry == 2:
                        self.captcha_in_process = False
                        self.end_websockets()
                        return False

                    continue

                elif resp.status_code == 204:
                    logger.success(f"{self.account_index} | Successfully sent the captcha result to the WickBot.")
                    return True

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to send captcha solution to WickBot -> {err}")
                if retry == 2:
                    self.captcha_in_process = False
                    sleep(2)
                    return False

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


class PandezBot:
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

        self.pandez_message_id: str = ""
        self.verified: bool = False
        self.captcha_in_process: bool = False
        self.list_hints: {} = {}

    def bypass_pandez_bot(self) -> bool:
        self.start_websockets()

        if self.verified:
            return True

        return False

    def listen_events(self, response):
        if response.event.ready_supplemental:
            self.press_verify_button()
            for retry in range(180):
                sleep(1)

            logger.error(f"{self.account_index} | Unable to solve PandezBot. Too much time has passed.")
            self.end_websockets()

        if response.event.message:
            if "You are already verified" in str(response.raw):
                logger.success(f"{self.account_index} | You are already verified.")
                self.verified = True
                self.end_websockets()

            # press Continue button
            elif "To continue, you must turn off your DMs" in str(response.raw):
                message = response.raw.get("d")
                self.press_continue_button(message)

        if response.event.message_updated:
            if "You are already verified" in str(response.raw):
                logger.success(f"{self.account_index} | You are already verified.")
                self.verified = True
                self.end_websockets()

            elif "You have been verified" in str(response.raw):
                logger.success(f"{self.account_index} | You are successfully verified!")
                self.verified = True
                self.end_websockets()

            # press Continue button
            elif "Read the rules" in str(response.raw):
                message = response.raw.get("d")
                if not self.press_continue_button(message):
                    self.end_websockets()

            # enter captcha result
            elif "Are you human?" in str(response.raw):
                if not self.captcha_in_process:
                    self.captcha_in_process = True
                    message = response.raw.get("d")
                    self.pandez_message_id = message['id']
                    if self.solve_captcha(message):
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
                data=button_manager.getButton("Verify"),
            )
            logger.success(f"{self.account_index} | Verify button pressed.")
            self.is_verify_pressed: bool = True
            return True

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to press verify button: {err}")
            return False

    def press_continue_button(self, message) -> bool:
        try:
            button_manager = Buttoner(message.get("components"))
            sleep(2)

            if len(button_manager.findButton("Continue")):
                self.discum_client.click(
                    message.get("author").get("id"),
                    message.get("channel_id"),
                    message.get("id"),
                    message.get("flags"),
                    self.guild_id,
                    data=button_manager.getButton("Continue"),
                )

            logger.success(f"{self.account_index} | Continue button pressed.")
            return True

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to press continue button: {err}")
            return False

    def solve_captcha(self, message):
        try:
            captcha_options = {}
            captcha_type = ""

            if "Choose the option that best describes the following image" in str(message):
                button_manager = Buttoner(message["components"])
                options = button_manager.components[0]["components"][0]["options"]

                for x in options:
                    self.list_hints[x.get("label").lower()] = x.get("value")

                hint = "Write down the name (not number) that best describes the following image: "
                for k, v in self.list_hints.items():
                    hint += f"| {k} "

                captcha_type = "list"
                captcha_options = {
                    "regsense": 0,
                    "numeric": 2,
                    "min_len": 3,
                    "language": 2,
                    "textinstructions": hint
                }

            elif "The image contains 6 green numbers" in str(message):
                captcha_type = "6 digits"
                captcha_options = {
                    "numeric": 1,
                    "min_len": 6,
                    "max_len": 6,
                    "textinstructions": "The image contains 6 big GREEN numbers, not gray"
                }

            captcha_image_url = message["embeds"][0]['image']['url']

            response = default_requests.get(captcha_image_url)

            img = Image.open(BytesIO(response.content))
            img = img.resize((int(img.size[0] * 0.9), int(img.size[1] * 0.9)), Image.LANCZOS)
            img = img.convert("RGB")

            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=70, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()

            result, ok = self.two_captcha_client.solve_image_to_text(img_str, captcha_options)

            if ok:
                if captcha_type == "6 digits":
                    return self.send_captcha_solution_numbers(result)

                elif captcha_type == "list":
                    return self.send_captcha_solution_list(result)

            else:
                return False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to solve the captcha: {err}")
            return False

    def send_captcha_solution_numbers(self, result: str) -> bool:
        for index, digit in enumerate(result, start=1):
            for retry in range(3):
                try:
                    data = {
                        'type': 3,
                        'nonce': calculate_nonce(),
                        'guild_id': self.guild_id,
                        'channel_id': self.channel_id,
                        'message_flags': 64,
                        'message_id': self.pandez_message_id,
                        'application_id': '967155551211491438',
                        'session_id': self.discum_client.gateway.session_id,
                        'data': {
                            'component_type': 2,
                            'custom_id': str(digit),
                        },
                    }

                    resp = self.http_client.post("https://discord.com/api/v10/interactions",
                                                 headers={
                                                     'authority': 'discord.com',
                                                     'accept': '*/*',
                                                     'content-type': 'application/json',
                                                     'origin': 'https://discord.com',
                                                     'referer': f'https://discord.com/channels/{self.guild_id}/{self.channel_id}',
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
                        logger.error(f"{self.account_index} | Failed to send a digit to Pandez.")
                        sleep(1)
                        if retry == 2:
                            self.captcha_in_process = False
                            self.end_websockets()
                            return False

                        continue

                    elif resp.status_code == 204 and index == 6:
                        sleep(5)
                        if not self.verified:
                            logger.error(f"{self.account_index} | Wrong captcha!")
                            return False

                        else:
                            logger.success(f"{self.account_index} | Successfully sent the captcha result to the PandezBot.")
                            return True

                    elif resp.status_code == 204:
                        sleep(2)
                        break

                except Exception as err:
                    logger.error(f"{self.account_index} | Failed to send captcha solution to PandezBot -> {err}")
                    if retry == 2:
                        self.captcha_in_process = False
                        sleep(2)
                        return False

    def send_captcha_solution_list(self, result: str) -> bool:
        for retry in range(3):
            try:
                data = {
                    'type': 3,
                    'nonce': calculate_nonce(),
                    'guild_id': self.guild_id,
                    'channel_id': self.channel_id,
                    'message_flags': 64,
                    'message_id': self.pandez_message_id,
                    'application_id': '967155551211491438',
                    'session_id': self.discum_client.gateway.session_id,
                    'data': {
                        'component_type': 3,
                        'custom_id': 'verificationMenu',
                        'type': 3,
                        'values': [
                            self.list_hints[result.lower().strip()]
                        ]
                    },
                }

                resp = self.http_client.post("https://discord.com/api/v10/interactions",
                                             headers={
                                                 'authority': 'discord.com',
                                                 'accept': '*/*',
                                                 'content-type': 'application/json',
                                                 'origin': 'https://discord.com',
                                                 'referer': f'https://discord.com/channels/{self.guild_id}/{self.channel_id}',
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
                    logger.error(f"{self.account_index} | Failed to send the solution to Pandez.")
                    sleep(1)
                    if retry == 2:
                        self.captcha_in_process = False
                        self.end_websockets()
                        return False

                    continue

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to send list solution to PandezBot: {err}")
                if retry == 2:
                    self.captcha_in_process = False
                    sleep(2)
                    return False

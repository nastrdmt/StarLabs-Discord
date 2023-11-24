from typing import Tuple

from curl_cffi import requests
from functools import partial
from loguru import logger
from time import sleep
import discum

from . import utilities


class DiscordTower:
    def __init__(self, account_index: int, proxy: str, discord_token: str, config: dict):
        self.account_index = account_index
        self.discord_token = discord_token
        self.config = config
        self.proxy = proxy

        self.discum_client: discum.Client | None = None
        self.capmonstercloud: None | utilities.Capmonstercloud = None
        self.two_captcha_client: None | utilities.TwoCaptcha = None
        self.client: requests.Session | None = None
        self.captcha_rqtoken: str = ""
        self.captcha_rqdata: str = ""

        self.x_content_properties: str = ""
        self.location_channel_id: str = ""
        self.location_guild_id: str = ""

        self.websocket_conn_successful = False
        self.profile_picture = None
        self.new_password = None
        self.old_password = None
        self.new_username = None
        self.change_status: str = "undone"
        self.changed_token: str = ""

        self.user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        self.captcha_sitekey: str = "a9b5fb07-92ff-493f-86fe-352a2803b3df"

        self.__prepare_data()

    def __prepare_data(self):
        for x in range(5):
            try:
                # create http client session
                self.client = utilities.create_client(self.proxy, self.discord_token, self.user_agent)
                self.client.headers.update({"user_agent": self.user_agent})
                # collect cloudflare cookies needed to bypass protection
                if not utilities.init_cf(self.account_index, self.client, self.user_agent):
                    raise Exception
                # initialize cf_clearance bypasser and generate cf_clearance
                cf = utilities.CloudflareBypasser(self.client, self.user_agent)
                if not cf.get_cf_clearance():
                    logger.error(f"{self.account_index} | Failed to get necessary discord info.")
                    raise Exception
                else:
                    logger.success(f"{self.account_index} | Collected discord data.")

                self.capmonstercloud = utilities.Capmonstercloud(self.account_index, self.config["capmonster_api_key"], self.client, self.proxy)
                self.two_captcha_client = utilities.TwoCaptcha(self.account_index, self.config['2captcha_api_key'], self.client, self.proxy)

                return True

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to prepare data: {err}")
                if x + 1 == 5:
                    raise Exception(f"{self.account_index} | Failed to prepare data 5 times. Exit...")

    def send_guild_chat_message(self, guild_id: str, channel_id: str, message_content: str) -> bool:
        try:
            resp = self.client.post(f"https://discord.com/api/v9/channels/{channel_id}/messages",
                                    headers={
                                        'authority': 'discord.com',
                                        'accept': '*/*',
                                        'content-type': 'application/json',
                                        'origin': 'https://discord.com',
                                        'referer': f'https://discord.com/channels/{guild_id}/{channel_id}',
                                        'sec-ch-ua-mobile': '?0',
                                        'sec-ch-ua-platform': '"Windows"',
                                        'sec-fetch-dest': 'empty',
                                        'sec-fetch-mode': 'cors',
                                        'sec-fetch-site': 'same-origin',
                                        'x-debug-options': 'bugReporterEnabled',
                                        'x-discord-locale': 'en-US',
                                    },
                                    json={
                                        'mobile_network_type': 'unknown',
                                        'content': message_content.replace("\\n", "\n"),
                                        'nonce': utilities.calculate_nonce(),
                                        'tts': False,
                                        'flags': 0,
                                    }
                                    )

            if resp.status_code == 200 and "channel_id" in resp.text:
                logger.success(f'{self.account_index} | Message sent!')
                return True

            elif "This content is blocked by this server" in resp.text:
                logger.error(f"{self.account_index} | This content is blocked by this server")
                return False

            elif resp.json()['code'] == 200000:
                logger.error(f"{self.account_index} | {resp.json()['message']}")
                return False

            elif resp.status_code == 429 or "rate limit" in resp.text:
                try:
                    logger.error(f"{self.account_index} | {resp.json()['message']}")
                    return False
                except:
                    logger.error(f"{self.account_index} | {resp.text}")
                    return False

            elif "Unknown Channel" in resp.text:
                logger.error(f"{self.account_index} | Most likely the account is not on the server.")
                return False

            else:
                logger.error(f"{self.account_index} | Failed to sent the message (unknown): {resp.text}")
                return False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to send guild chat message: {err}")
            return False

    def send_reaction_on_message(self, channel_id: str, message_id: str, emoji: str) -> bool:
        try:
            resp = self.client.put(f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/%40me")

            if resp.status_code == 204:
                logger.success(f"{self.account_index} | Successfully reacted to the message!")
                return True

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to send a reaction to the message: {err}")
            return False

    def press_button(self, guild_id: str, channel_id: str, message_id: str, button_data: dict, application_id: str) -> bool:
        try:
            resp = self.client.post("https://discord.com/api/v9/interactions",
                                    headers={
                                        'authority': 'discord.com',
                                        'accept': '*/*',
                                        'content-type': 'application/json',
                                        'origin': 'https://discord.com',
                                        'referer': f'https://discord.com/channels/{guild_id}/{channel_id}',
                                        'sec-ch-ua-mobile': '?0',
                                        'sec-ch-ua-platform': '"Windows"',
                                        'sec-fetch-dest': 'empty',
                                        'sec-fetch-mode': 'cors',
                                        'sec-fetch-site': 'same-origin',
                                        'x-debug-options': 'bugReporterEnabled',
                                        'x-discord-locale': 'en-US',
                                    },
                                    json={
                                        'type': 3,
                                        'nonce': utilities.calculate_nonce(),
                                        'guild_id': guild_id,
                                        'channel_id': channel_id,
                                        'message_flags': 0,
                                        'message_id': message_id,
                                        'application_id': application_id,
                                        'session_id': utilities.generate_random_session_id(),
                                        'data': {
                                            'component_type': button_data['type'],
                                            'custom_id': button_data['custom_id'],
                                        },
                                    }
                                    )

            if resp.status_code == 204:
                logger.success(f"{self.account_index} | Successfully pressed the button.")
                return True
            else:
                raise Exception("Unknown error")

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to press a button: {err}")
            return False

    def change_password(self):
        try:
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'uk',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'https://discord.com',
                'Referer': 'https://discord.com/channels/@me',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-Debug-Options': 'bugReporterEnabled',
                'X-Discord-Locale': 'en-US',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }

            resp = self.client.patch('https://discord.com/api/v9/users/@me',
                                     headers=headers,
                                     json={
                                         'password': self.old_password,
                                         'new_password': self.new_password,
                                     })

            if "Password is too weak or common to use." in resp.text:
                logger.error(f"{self.account_index} | Password is too weak or common to use.")
                self.change_status = "failed"
                self.end_websockets()

            elif "Password does not match." in resp.text:
                logger.error(f"{self.account_index} | Password does not match. You provided wrong password.")
                self.change_status = "failed"
                self.end_websockets()

            elif resp.status_code == 200 and "token" in resp.text:
                logger.success(f"{self.account_index} | Successfully changed the password.")
                self.changed_token = resp.json()['token']
                self.change_status = "done"
                self.end_websockets()
            else:
                raise Exception(f"Unknown error: {resp.text}")

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to change the password: {err}")
            self.change_status = "failed"
            self.end_websockets()

    def change_name(self, new_name: str) -> bool:
        try:
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'uk',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'https://discord.com',
                'Referer': 'https://discord.com/channels/@me',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-Debug-Options': 'bugReporterEnabled',
                'X-Discord-Locale': 'en-US',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }

            resp = self.client.patch('https://discord.com/api/v9/users/@me',
                                     headers=headers,
                                     json={'global_name': new_name})

            if resp.status_code == 200:
                logger.success(f"{self.account_index} | Successfully changed the name.")
                return True
            else:
                raise Exception(f"Unknown error :{resp.text}")

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to change the name: {err}")
            return False

    def change_username(self):
        try:
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'uk',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'https://discord.com',
                'Referer': 'https://discord.com/channels/@me',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-Debug-Options': 'bugReporterEnabled',
                'X-Discord-Locale': 'en-US',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }

            resp = self.client.patch('https://discord.com/api/v9/users/@me',
                                     headers=headers,
                                     json={
                                         'username': self.new_username,
                                         'password': self.old_password,
                                     })

            if "You need to update your app to join this server." in resp.text or "captcha_rqdata" in resp.text:
                self.captcha_rqdata = resp.json()["captcha_rqdata"]
                self.captcha_rqtoken = resp.json()["captcha_rqtoken"]

                g_recaptcha_response, ok = self.capmonstercloud.solve_hcaptcha(self.captcha_sitekey, f"https://discord.com/app", self.captcha_rqdata, self.user_agent)
                if not ok:
                    self.change_status = "failed"
                    self.end_websockets()

                headers = {
                    'Accept': '*/*',
                    'Accept-Language': 'uk',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'Origin': 'https://discord.com',
                    'Referer': 'https://discord.com/channels/@me',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'X-Captcha-Key': g_recaptcha_response,
                    'X-Captcha-Rqtoken': self.captcha_rqtoken,
                    'X-Debug-Options': 'bugReporterEnabled',
                    'X-Discord-Locale': 'en-US',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                }

                resp = self.client.patch('https://discord.com/api/v9/users/@me',
                                         headers=headers,
                                         json={
                                             'username': self.new_username,
                                             'password': self.old_password,
                                         })

                if resp.status_code == 200:
                    logger.success(f"{self.account_index} | Successfully changed the username!")
                    self.change_status = "done"
                    self.end_websockets()
                else:
                    logger.error(f"{self.account_index} | Wrong response.")
                    self.change_status = "failed"
                    self.end_websockets()

            elif "PASSWORD_DOES_NOT_MATCH" in resp.text:
                logger.error(f"{self.account_index} | Wrong password.")
                self.change_status = "failed"
                self.end_websockets()

            elif resp.status_code == 200:
                logger.success(f"{self.account_index} | Successfully changed the username!")
                self.change_status = "done"
                self.end_websockets()

            else:
                raise Exception(f"Unknown error: {resp.text}")

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to change the username: {err}")
            self.change_status = "failed"
            self.end_websockets()

    # profile picture should be in encoded string format like
    # with open(file_path, 'rb') as image_file:
    #     profile_picture_encoded = base64.b64encode(image_file.read()).decode('utf-8')
    def change_self_data(self, profile_picture_encoded: str = None, new_password: str = None, password: str = None, new_username: str = None) -> tuple[bool, str]:
        self.profile_picture = profile_picture_encoded
        self.new_password = new_password
        self.old_password = password
        self.new_username = new_username

        self.start_websockets()
        return self.change_status == "done", self.changed_token

    def change_profile_picture(self):
        try:
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'uk',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'https://discord.com',
                'Referer': 'https://discord.com/channels/@me',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-Debug-Options': 'bugReporterEnabled',
                'X-Discord-Locale': 'en-US',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }

            resp = self.client.patch('https://discord.com/api/v9/users/@me',
                                     headers=headers,
                                     json={'avatar': f'data:image/png;base64,{self.profile_picture}'})

            if resp.status_code == 200:
                logger.success(f"{self.account_index} | Successfully changed profile picture.")
                self.change_status = "done"
                self.end_websockets()

            else:
                raise Exception("Unknown error")

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to change profile picture: {err}")
            self.change_status = "failed"
            self.end_websockets()

    def bypass_captcha_bot(self, guild_id: str, channel_id: str, message_id: str) -> bool:
        try:
            captcha_bot_instance = utilities.captcha_bot_bypass.CaptchaBot(self.account_index, self.client, self.user_agent, self.proxy, self.discord_token, self.config, self.capmonstercloud, guild_id, channel_id, message_id)
            return captcha_bot_instance.bypass_captcha_bot()

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to bypass captcha bot: {err}")
            return False

    def bypass_enter_form(self, invite_code: str) -> bool:
        try:
            resp = self.client.get(f"https://discord.com/api/v9/invites/{invite_code}")
            guild_id = resp.json()["guild_id"]

            resp = self.client.get(f"https://discord.com/api/v9/guilds/{guild_id}/onboarding")

            sleep(2)

            resp = self.client.post(f"https://discord.com/api/v9/guilds/{guild_id}/onboarding-responses",
                                    json={
                                        'onboarding_responses': resp.json()['responses'],
                                        'onboarding_prompts_seen': resp.json()['onboarding_prompts_seen'],
                                        'onboarding_responses_seen': resp.json()['onboarding_responses_seen'],
                                    })

            if resp.status_code == 200:
                logger.success(f"{self.account_index} | Successfully bypassed enter form.")
                return True
            else:
                raise Exception("Unknown error")

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to bypass enter form: {err}")
            return False

    def bypass_pandez_bot(self, guild_id: str, channel_id: str, message_id: str) -> bool:
        try:
            pandez_bot_instance = utilities.pandez_bot_bypass.PandezBot(self.account_index, self.client, self.user_agent, self.proxy, self.discord_token, self.config, self.capmonstercloud, guild_id, channel_id, message_id, self.two_captcha_client)
            return pandez_bot_instance.bypass_pandez_bot()

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to bypass Pandez bot: {err}")
            return False

    def bypass_sledgehammer_bot(self, guild_id: str, channel_id: str, message_id: str) -> bool:
        try:
            pandez_bot_instance = utilities.sledgehammer_bot_bypass.SledgehammerBot(self.account_index, self.client, self.user_agent, self.proxy, self.discord_token, self.config, self.capmonstercloud, guild_id, channel_id, message_id, self.two_captcha_client)
            return pandez_bot_instance.bypass_sledgehammer_bot()

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to bypass Sledgehammer bot: {err}")
            return False

    def token_checker(self) -> tuple[bool, str] | bool:
        try:
            guilds_url = "https://discord.com/api/v9/users/@me/affinities/guilds"
            me_url = "https://discord.com/api/v9/users/@me"

            resp = self.client.get(guilds_url)

            if resp.status_code in (401, 403):
                logger.warning(f"{self.account_index} | Token is locked: {self.discord_token}")
                return True, "locked"

            if resp.status_code in (200, 204):
                response = self.client.get(me_url)
                flags_data = response.json()['flags'] - response.json()['public_flags']

                if flags_data == 17592186044416:
                    logger.warning(f"{self.account_index} | Token is quarantined: {self.discord_token}")
                elif flags_data == 1048576:
                    logger.warning(f"{self.account_index} | Token is flagged as spammer: {self.discord_token}")
                elif flags_data == 17592186044416 + 1048576:
                    logger.warning(f"{self.account_index} | Token is flagged as spammer and quarantined: {self.discord_token}")

                logger.success(f"{self.account_index} | Token is working!")

            else:
                logger.error(f"Invalid status code {resp.status_code} while checking token.")

            return True, ""
        except Exception as err:
            logger.error(f"{self.account_index} | Failed to check token status: {err}")
            return False, ""

    def leave_guild(self, guild_id: str) -> bool:
        try:
            leave_guild_url = f"https://discord.com/api/v9/users/@me/guilds/{guild_id}"
            headers = {
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
            }

            json_data = {
                'lurking': False,
            }

            resp = self.client.delete(leave_guild_url, headers=headers, json=json_data)

            if resp.status_code == 204:
                logger.success(f"{self.account_index} | Successfully leaved the guild!")
                return True

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to leave the guild: {err}")
            return False

    def show_all_token_guilds(self) -> bool:
        try:
            all_guilds_headers = {
                'authority': 'discord.com',
                'accept': '*/*',
                'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4',
                'referer': 'https://discord.com/channels/@me',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-debug-options': 'bugReporterEnabled',
                'x-discord-locale': 'en-US',
            }

            token_id = self.client.get("https://discord.com/api/v9/users/@me").json()['id']
            all_guilds_url = f"https://discord.com/api/v9/users/{token_id}/profile"

            token_guilds = self.client.get(all_guilds_url,
                                           params={
                                               'with_mutual_guilds': 'true',
                                               'with_mutual_friends_count': 'false',
                                           },
                                           headers=all_guilds_headers).json()['mutual_guilds']

            all_guilds_message = ""

            for guild in token_guilds:
                for x in range(3):
                    try:
                        guild_name = self.client.get(f"https://discord.com/api/v9/guilds/{guild['id']}").json()['name']
                        all_guilds_message += f"{guild_name} | "
                        break
                    except Exception as err:
                        if x == 2:
                            raise Exception(f"unable to get guild name: {err}")

            logger.success(f"{self.account_index} | {self.discord_token} | Guilds: {all_guilds_message}")
            return True

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to get token's guilds: {err}")
            return False

    # def bypass_wick_bot(self, guild_id: str, channel_id: str, message_id: str) -> bool:
    #     try:
    #         wick_bot_instance = utilities.wick_bot_bypass.WickBot(self.account_index, self.client, self.user_agent, self.proxy, self.discord_token, self.config, self.capmonstercloud, guild_id, channel_id, message_id, self.two_captcha_client)
    #         return wick_bot_instance.bypass_wick_bot()
    #
    #     except Exception as err:
    #         logger.error(f"{self.account_index} | Failed to bypass Wick bot: {err}")
    #         return False

    def start_websockets(self):
        if self.proxy != "":
            proxy_str = f"http://{self.proxy}"
            self.discum_client = discum.Client(token=self.discord_token, proxy=proxy_str, log={"console": False, "file": False})
        else:
            self.discum_client = discum.Client(token=self.discord_token, log={"console": False, "file": False})

        prepare = partial(self.listen_events)

        self.discum_client.gateway.command(prepare)
        self.discum_client.gateway.run(False)

        if not self.websocket_conn_successful:
            logger.error(f"{self.account_index} | Failed to establish a websocket connection. Check if the token is working properly.")

    def end_websockets(self):
        self.discum_client.gateway.close()

    def listen_events(self, response):
        if response.event.ready_supplemental:
            self.websocket_conn_successful = True

            if self.profile_picture:
                self.change_profile_picture()

            if self.new_username:
                self.change_username()

            if self.new_password:
                self.change_password()

            for retry in range(60):
                if self.change_status in ("done", "failed"):
                    return
                sleep(1)

            if self.change_status == "undone":
                logger.error(f"{self.account_index} | Unable to change self data. Too much time has passed.")
            self.end_websockets()

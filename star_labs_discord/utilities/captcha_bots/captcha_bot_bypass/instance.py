from functools import partial
from time import sleep

import discum
from curl_cffi import requests
from discum.utils.button import Buttoner
from loguru import logger


class CaptchaBot:
    def __init__(self, account_index: int, client: requests.Session, user_agent: str, proxy: str, discord_token: str, config: dict, capmonster_client,
                 guild_id: str, channel_id: str, message_id: str):

        self.account_index = account_index
        self.discord_token = discord_token
        self.user_agent = user_agent
        self.http_client = client
        self.config = config
        self.proxy = proxy

        self.discum_client: None | discum.Client = None
        self.capmonster_client = capmonster_client
        self.channel_id: str = channel_id
        self.message_id: str = message_id
        self.guild_id: str = guild_id

        self.captcha_bot_invite_hash: str | None = None
        self.captcha_bot_link: str | None = None
        self.is_verify_pressed: bool = False
        self.agree_bypassed: bool = False
        self.verified: bool = False

    def bypass_captcha_bot(self) -> bool:
        self.start_websockets()

        if self.captcha_bot_link is not None and not self.verified:
            captcha_bot_code, ok = self.login_via_discord()
            if ok:
                return self.bypass_captcha_bot_cloudflare(captcha_bot_code)
        else:
            return False

    def listen_events(self, response):
        if response.event.ready_supplemental:
            self.press_verify_button()
            for retry in range(10):
                if self.agree_bypassed:
                    break
                sleep(1)

            if not self.agree_bypassed:
                logger.error(f"{self.account_index} | Unable to get CaptchaBot link. Probably low verification level.")
                self.end_websockets()

        if response.event.message:
            if "Please verify yourself to gain access to" in str(response.raw):
                message = response.raw.get("d")
                self.captcha_bot_link = str(message).split('Please complete this captcha to prove you are a human: [Click here](')[1].split(')')[0].strip()
                logger.success(f"{self.account_index} | Got CaptchaBot link!")
                self.agree_bypassed = True
                self.end_websockets()

            elif "You are already verified." in str(response.raw):
                logger.success(f"{self.account_index} | This account already verified!")
                self.agree_bypassed = True
                self.verified = True
                self.end_websockets()

            elif 'Channel verification level is too high' in str(response.raw):
                logger.error(f"{self.account_index} | Channel verification level is too high.")
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

    def login_via_discord(self) -> tuple[str, bool]:
        for _ in range(3):
            try:
                self.captcha_bot_invite_hash = self.captcha_bot_link.split('/')[-1]

                new_captcha_user_link = "https://captcha.bot/api/v1/captcha/" + self.guild_id + "/" + self.captcha_bot_link.split('/')[-1]
                self.http_client.get(new_captcha_user_link, params={"new": True})

                resp = self.http_client.post("https://discord.com/api/v9/oauth2/authorize",
                                             headers={
                                                 'authority': 'discord.com',
                                                 'accept': '*/*',
                                                 'content-type': 'application/json',
                                                 'origin': 'https://discord.com',
                                                 'referer': f'https://discord.com/oauth2/authorize?client_id=512333785338216465&redirect_uri=https%3A%2F%2Fcaptcha.bot%2Fcallback&response_type=code&scope=identify%20guilds%20guilds.members.read%20role_connections.write&state=%2Fverify%2Fguild%2F{self.guild_id}%2F' + self.captcha_bot_invite_hash,
                                                 'sec-ch-ua-mobile': '?0',
                                                 'sec-ch-ua-platform': '"Windows"',
                                                 'sec-fetch-dest': 'empty',
                                                 'sec-fetch-mode': 'cors',
                                                 'sec-fetch-site': 'same-origin',
                                                 'x-debug-options': 'bugReporterEnabled',
                                                 'x-discord-locale': 'en-US',
                                             },
                                             params={
                                                 'client_id': '512333785338216465',
                                                 'response_type': 'code',
                                                 'redirect_uri': 'https://captcha.bot/callback',
                                                 'scope': 'identify guilds guilds.members.read role_connections.write',
                                                 'state': f'/verify/guild/' + self.guild_id + "/" + self.captcha_bot_invite_hash
                                             },
                                             json={
                                                 'permissions': '0',
                                                 'authorize': True,
                                                 'user_install': False,
                                             }
                                             )

                if "Unauthorized" in resp.text:
                    logger.error(f"{self.account_index} | Check your discord token, it might be locked.")
                    return "", False

                url = resp.json()["location"]
                captcha_bot_code = url.split('code=')[1].split('&')[0]

                resp = self.http_client.get(url,
                                            headers={
                                                'authority': 'captcha.bot',
                                                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                                                'referer': 'https://discord.com/',
                                                'sec-ch-ua-mobile': '?0',
                                                'sec-ch-ua-platform': '"Windows"',
                                                'sec-fetch-dest': 'document',
                                                'sec-fetch-mode': 'navigate',
                                                'sec-fetch-site': 'cross-site',
                                                'sec-fetch-user': '?1',
                                                'upgrade-insecure-requests': '1',
                                            })

                if resp.status_code == 200:
                    logger.success(f"{self.account_index} | Logged in CaptchaBot via Discord.")
                    return captcha_bot_code, True

                else:
                    logger.error(f"{self.account_index} | Error while connecting to Discord. Trying one more time...")

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to login in captcha bot: {err}")

        return "", False

    def bypass_captcha_bot_cloudflare(self, captcha_bot_code: str):
        for _ in range(3):
            try:
                captcha_bot_cloudflare_token = "0x4AAAAAAAD-1BvLrXzkAN84"

                resp = self.http_client.post('https://captcha.bot/api/v1/oauth/callback',
                                             params={
                                                 'code': captcha_bot_code,
                                             },
                                             headers={
                                                 'authority': 'captcha.bot',
                                                 'accept': 'application/json, text/plain, */*',
                                                 'authorization': 'null',
                                                 'content-type': 'text/plain',
                                                 'origin': 'https://captcha.bot',
                                                 'sec-ch-ua-mobile': '?0',
                                                 'sec-ch-ua-platform': '"Windows"',
                                                 'sec-fetch-dest': 'empty',
                                                 'sec-fetch-mode': 'cors',
                                                 'sec-fetch-site': 'same-origin',
                                             })

                captcha_bot_token = resp.json()['token']

                captcha_solved_token, ok = self.capmonster_client.solve_turnstile(captcha_bot_cloudflare_token, f"https://captcha.bot/verify/guild/{self.guild_id}/{self.captcha_bot_invite_hash}")
                if not ok:
                    return False

                resp = self.http_client.post("https://captcha.bot/api/v1/captcha/verify",
                                             json={
                                                 'token': captcha_solved_token,
                                                 'hash': self.captcha_bot_invite_hash,
                                                 'guildID': self.guild_id
                                             },
                                             headers={
                                                 'authority': 'captcha.bot',
                                                 'accept': 'application/json, text/plain, */*',
                                                 'authorization': captcha_bot_token,
                                                 'content-type': 'application/json;charset=UTF-8',
                                                 'origin': 'https://captcha.bot',
                                                 'referer': f'https://captcha.bot/verify/guild/{self.guild_id}/{self.captcha_bot_invite_hash}',
                                                 'sec-ch-ua-mobile': '?0',
                                                 'sec-ch-ua-platform': '"Windows"',
                                                 'sec-fetch-dest': 'empty',
                                                 'sec-fetch-mode': 'cors',
                                                 'sec-fetch-site': 'same-origin',
                                             }
                                             )

                if resp.json()["status"] == "ACKNOWLEDGED":
                    logger.success(f"{self.account_index} | Welcome!")
                    return True

                else:
                    logger.error(f"{self.account_index} | Failed to bypass CaptchaBot.")

            except Exception as err:
                logger.error(f"{self.account_index} | Failed to bypass cloudflare in CaptchaBot: {err}")

        return False

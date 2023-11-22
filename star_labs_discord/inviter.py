from loguru import logger

from . import DiscordTower
from . import utilities


class Inviter(DiscordTower):
    def __init__(self, account_index: int, proxy: str, discord_token: str, config: dict, invite_code: str):
        super().__init__(account_index, proxy, discord_token, config)

        self.invite_code: str = invite_code

    def invite(self):
        try:
            self.location_guild_id, self.location_channel_id, ok = utilities.get_guild_ids(self.client, self.invite_code, self.account_index)
            if not ok:
                if self.location_guild_id == "verification_failed":
                    return False

            self.x_content_properties = utilities.create_x_context_properties(self.location_guild_id, self.location_channel_id)
            self.client.headers.update({"x_content_properties": self.x_content_properties})

        except Exception as err:
            logger.error(f'{self.account_index} | Failed to invite: {err}')
            return False

        if not self.solve_invite_captcha():
            return False

        return self.agree_with_rules()

    def solve_invite_captcha(self):
        for retry in range(self.config['max_invite_retries']):
            try:
                resp = self.client.post(f"https://discord.com/api/v9/invites/{self.invite_code}",
                                        json={'session_id': None},
                                        headers={
                                            'authority': 'discord.com',
                                            'accept': '*/*',
                                            'accept-language': 'en-US,en;q=0.8',
                                            'content-type': 'application/json',
                                            'origin': 'https://discord.com',
                                            'referer': f'https://discord.com/invite/{self.invite_code}',
                                            'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
                                            'sec-ch-ua-mobile': '?0',
                                            'sec-ch-ua-platform': '"Windows"',
                                            'sec-fetch-dest': 'empty',
                                            'sec-fetch-mode': 'cors',
                                            'sec-fetch-site': 'same-origin',
                                            'user-agent': self.user_agent,
                                            'x-context-properties': self.x_content_properties,
                                            'x-debug-options': 'bugReporterEnabled',
                                            'x-discord-locale': 'en-US',
                                            'x-discord-timezone': 'America/New_York',
                                        })

                if "You need to update your app to join this server." in resp.text or "captcha_rqdata" in resp.text:
                    self.captcha_rqdata = resp.json()["captcha_rqdata"]
                    self.captcha_rqtoken = resp.json()["captcha_rqtoken"]

                    g_recaptcha_response, ok = self.capmonstercloud.solve_hcaptcha(self.captcha_sitekey, f"https://discord.com/invite/{self.invite_code}", self.captcha_rqdata, self.user_agent)
                    if not ok:
                        continue

                    resp = self.client.post(f"https://discord.com/api/v9/invites/{self.invite_code}",
                                            json={'session_id': None},
                                            headers={
                                                'authority': 'discord.com',
                                                'accept': '*/*',
                                                'accept-language': 'en-US,en;q=0.8',
                                                'content-type': 'application/json',
                                                'origin': 'https://discord.com',
                                                'referer': f'https://discord.com/invite/{self.invite_code}',
                                                'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
                                                'sec-ch-ua-mobile': '?0',
                                                'sec-ch-ua-platform': '"Windows"',
                                                'sec-fetch-dest': 'empty',
                                                'sec-fetch-mode': 'cors',
                                                'sec-fetch-site': 'same-origin',
                                                'user-agent': self.user_agent,
                                                'x-captcha-key': g_recaptcha_response,
                                                'x-captcha-rqtoken': self.captcha_rqtoken,
                                                'x-context-properties': self.x_content_properties,
                                                'x-debug-options': 'bugReporterEnabled',
                                                'x-discord-locale': 'en-US',
                                                'x-discord-timezone': 'America/New_York',
                                            }
                                            )

                    if resp.status_code == 200 and resp.json()["type"] == 0:
                        logger.success(f"{self.account_index} | Joined the server!")
                        return True
                    else:
                        logger.info(f"{self.account_index} | Wrong invite response | {retry + 1}/{self.config['max_invite_retries']}")
                        continue

                elif resp.status_code == 200 and resp.json()["type"] == 0:
                    logger.success(f"{self.account_index} | Account already joined the server!")
                    return True

                elif "Unauthorized" in resp.text:
                    logger.error(f"{self.account_index} | Incorrect discord token or your account is blocked.")
                    return False

                elif "You need to verify your account in order to" in resp.text:
                    logger.error(f"{self.account_index} | Account needs verification (Email code etc).")
                    return False

                else:
                    logger.error(f"{self.account_index} | Unknown error: {resp.text}")

            except Exception as err:
                logger.error(f"{self.account_index} | Error joining the server: {err}")
                if retry + 1 == self.config['max_invite_retries']:
                    return False

    def agree_with_rules(self) -> bool:
        try:
            resp = self.client.get(f"https://discord.com/api/v9/guilds/{self.location_guild_id}/member-verification?with_guild=false&invite_code={self.invite_code}")
            if "Unknown Guild" in resp.text:
                logger.info(f"{self.account_index} | This guild does not require agreement with the rules.")
                return True

            resp = self.client.put(f"https://discord.com/api/v9/guilds/{self.location_guild_id}/requests/@me",
                                   headers={
                                       'authority': 'discord.com',
                                       'accept': '*/*',
                                       'content-type': 'application/json',
                                       'origin': 'https://discord.com',
                                       'referer': f'https://discord.com/channels/{self.location_guild_id}/{self.location_channel_id}',
                                       'sec-ch-ua-mobile': '?0',
                                       'sec-ch-ua-platform': '"Windows"',
                                       'sec-fetch-dest': 'empty',
                                       'sec-fetch-mode': 'cors',
                                       'sec-fetch-site': 'same-origin',
                                       'x-debug-options': 'bugReporterEnabled',
                                       'x-discord-locale': 'en-US',
                                   },
                                   json={
                                       'version': resp.json()['version'],
                                       'form_fields': [
                                           {
                                               'field_type': resp.json()['form_fields'][0]['field_type'],
                                               'label': resp.json()['form_fields'][0]['label'],
                                               'description': resp.json()['form_fields'][0]['description'],
                                               'automations': resp.json()['form_fields'][0]['automations'],
                                               'required': True,
                                               'values': resp.json()['form_fields'][0]['values'],
                                               'response': True,
                                           },
                                       ],
                                   })

            if 'You need to verify your account' in resp.text:
                logger.error(f"{self.account_index} | Account needs verification (Email code etc).")
                return False

            elif 'This user is already a member' in resp.text:
                logger.success(f"{self.account_index} | This user is already a member!")
                return True

            if "application_status" in resp.text:
                if resp.json()['application_status'] == "APPROVED":
                    logger.success(f"{self.account_index} | Agreed to the server rules.")
                    return True
                else:
                    logger.error(f"{self.account_index} | Failed to agree to the server rules: {resp.text}")
                    return False

            else:
                logger.error(f"{self.account_index} | Failed to agree to the server rules: {resp.json()['rejection_reason']}")
                return False

        except Exception as err:
            logger.error(f"{self.account_index} | Failed to agree to the server rules: {err}")
            return False

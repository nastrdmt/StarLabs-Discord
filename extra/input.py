from loguru import logger

import extra


def get_user_choice(tasks_list: list, text_to_show: str) -> list:
    user_choice = input(text_to_show + ": ").split()
    return [tasks_list[int(task.strip())-1] for task in user_choice]


def ask_for_task_data(all_tasks: list, config: dict) -> dict | None:
    tasks_user_data = {
        "inviter": {},
        "press button": {},
        "press reaction": {},
        "change name": False,
        "change username": False,
        "change password": False,
        "change profile picture": False,
        "send message channel": {},
        "token checker": False,
        "leave guild": {},
        "show all token guilds": False
    }

    if "Inviter [Token]" in all_tasks:
        invite_link = input("Paste your invite code or link: ").strip()
        if "/" in invite_link:
            invite_code = invite_link.split('/')[-1]
        else:
            invite_code = invite_link

        tasks_user_data['inviter']['invite_code'] = invite_code

        extra.show_menu(extra.CAPTCHA_BOTS)
        captcha_choice = get_user_choice(extra.CAPTCHA_BOTS,  "Select from the list the type of captcha the server has")

        if len(captcha_choice) > 1:
            logger.error("Choose only one type of captcha")
            return
        tasks_user_data['inviter']['captcha_bot'] = captcha_choice[0].strip()
        if tasks_user_data['inviter']['captcha_bot'] in ("Pandez", "CaptchaBot", "Sledgehammer"):
            message_link = input("Paste the link to the message: ").strip()
            tasks_user_data['inviter']['guild_id'] = message_link.split("/")[-3]
            tasks_user_data['inviter']['channel_id'] = message_link.split("/")[-2]
            tasks_user_data['inviter']['message_id'] = message_link.split("/")[-1]

    if "Press Button [Token]" in all_tasks:
        visible_discord_token = config['main_discord_token']
        message_link = input("Paste the link to the message: ").strip()
        tasks_user_data['press button']['guild_id'] = message_link.split("/")[-3]
        tasks_user_data['press button']['channel_id'] = message_link.split("/")[-2]
        tasks_user_data['press button']['message_id'] = message_link.split("/")[-1]

        button_data, application_id, ok = extra.message_click_button_info(tasks_user_data['press button']['channel_id'], tasks_user_data['press button']['message_id'], visible_discord_token)
        tasks_user_data['press button']['button_data'] = button_data
        tasks_user_data['press button']['application_id'] = application_id

    if "Press Reaction [Token]" in all_tasks:
        visible_discord_token = config['main_discord_token']
        message_link = input("Paste the link to the message: ").strip()
        tasks_user_data['press reaction']['channel_id'] = message_link.split("/")[-2]
        tasks_user_data['press reaction']['message_id'] = message_link.split("/")[-1]

        tasks_user_data['press reaction']['emojis_info'], ok = extra.message_reactions_emojis_info(tasks_user_data['press reaction']['channel_id'], tasks_user_data['press reaction']['message_id'], visible_discord_token)
        if not ok:
            return

    if "Change Name [Token]" in all_tasks:
        tasks_user_data['change name'] = True

    if "Change Username [Token + Password]" in all_tasks:
        tasks_user_data['change username'] = True

    if "Change Password [Token + Password]" in all_tasks:
        tasks_user_data['change password'] = True

    if "Change Profile Picture [Token + Password]" in all_tasks:
        tasks_user_data['change profile picture'] = True

    if "Send message to the channel [Token]" in all_tasks:
        message_link = input("Paste the link to the channel: ").strip()
        tasks_user_data['send message channel']['guild_id'] = message_link.split("/")[-2]
        tasks_user_data['send message channel']['channel_id'] = message_link.split("/")[-1]

    if "Token Checker [Token]" in all_tasks:
        tasks_user_data['token checker'] = True

    if "Leave Guild [Token]" in all_tasks:
        tasks_user_data['leave guild']['guild_id'] = input("Paste the ID of the server you want to leave: ").strip()

    if "Show all servers account is in [Token]" in all_tasks:
        tasks_user_data['show all token guilds'] = True

    return tasks_user_data


def no_proxies() -> bool:
    user_choice = int(input("No proxies were detected. Do you want to continue without proxies? (1 or 2)\n"
                            "[1] Yes\n"
                            "[2] No\n>> ").strip())

    return True if user_choice == 1 else False

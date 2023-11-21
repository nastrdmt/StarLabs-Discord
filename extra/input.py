import inquirer
from loguru import logger

import extra


def get_user_choice(tasks_list: list, task_id: str, message_to_show: str) -> list:
    questions = [
        inquirer.Checkbox(task_id,
                          message=message_to_show,
                          choices=tasks_list,
                          ),
    ]

    return inquirer.prompt(questions)[task_id]


def ask_for_task_data(all_tasks: list) -> dict | None:
    tasks_user_data = {
        "inviter": {},
        "press button": {},
        "press reaction": {},
        "change name": False,
        "change username": False,
        "change password": False,
        "change profile picture": False,
        "send message channel": {}
    }

    if "Inviter" in all_tasks:
        invite_link = input("Paste your invite code or link: ").strip()
        if "/" in invite_link:
            invite_code = invite_link.split('/')[-1]
        else:
            invite_code = invite_link

        tasks_user_data['inviter']['invite_code'] = invite_code
        captcha_choice = get_user_choice(extra.CAPTCHA_BOTS, "captcha_bot", "Select from the list the type of captcha the server has")
        if len(captcha_choice) > 1:
            logger.error("Choose only one type of captcha")
            return
        tasks_user_data['inviter']['captcha_bot'] = captcha_choice[0].strip()
        if tasks_user_data['inviter']['captcha_bot'] in ("Pandez", "CaptchaBot", "Sledgehammer"):
            tasks_user_data['inviter']['guild_id'] = input("Paste the guild ID: ").strip()
            tasks_user_data['inviter']['channel_id'] = input("Paste the channel ID: ").strip()
            tasks_user_data['inviter']['message_id'] = input("Paste the message ID: ").strip()

    if "Press Button" in all_tasks:
        visible_discord_token = input("Paste the discord token that can see the message: ").strip()
        tasks_user_data['press button']['guild_id'] = input("Paste the guild ID: ").strip()
        tasks_user_data['press button']['channel_id'] = input("Paste the channel ID: ").strip()
        tasks_user_data['press button']['message_id'] = input("Paste the message ID: ").strip()

        button_data, application_id, ok = extra.message_click_button_info(tasks_user_data['press button']['channel_id'], tasks_user_data['press button']['message_id'], visible_discord_token)
        tasks_user_data['press button']['button_data'] = button_data
        tasks_user_data['press button']['application_id'] = application_id

    if "Press Reaction" in all_tasks:
        visible_discord_token = input("Paste the discord token that can see the message: ").strip()
        tasks_user_data['press reaction']['channel_id'] = input("Paste the channel ID: ").strip()
        tasks_user_data['press reaction']['message_id'] = input("Paste the message ID: ").strip()

        tasks_user_data['press reaction']['emojis_info'], ok = extra.message_reactions_emojis_info(tasks_user_data['press reaction']['channel_id'], tasks_user_data['press reaction']['message_id'], visible_discord_token)
        if not ok:
            return

    if "Change Name" in all_tasks:
        tasks_user_data['change name'] = True

    if "Change Username" in all_tasks:
        tasks_user_data['change username'] = True

    if "Change Password" in all_tasks:
        tasks_user_data['change password'] = True

    if "Change Profile Picture" in all_tasks:
        tasks_user_data['change profile picture'] = True

    if "Send message to the channel" in all_tasks:
        tasks_user_data['send message channel']['guild_id'] = input("Paste the guild ID: ").strip()
        tasks_user_data['send message channel']['channel_id'] = input("Paste the channel ID: ").strip()
        tasks_user_data['send message channel']['message_content'] = input("Paste the message you want to send: ").strip()

    return tasks_user_data

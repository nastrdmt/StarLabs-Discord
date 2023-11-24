from urllib.parse import quote
from loguru import logger
import requests

import extra


# returns dict with message data (label, custom_id) and application_id
def message_click_button_info(channel_id: str, message_id: str, visible_discord_token: str) -> tuple[dict, str, bool]:
    try:
        resp = requests.get("https://discord.com/api/v9/channels/" + channel_id + "/messages?limit=1&around=" + message_id,
                            headers={"Authorization": visible_discord_token})

        result, ok = choose_button_to_click(resp.json()[0]['components'])

        return result, resp.json()[0]['author']['id'], ok

    except Exception as err:
        logger.error(f'Failed to get message info: {err}')
        return {}, "", False


def choose_button_to_click(components: list) -> tuple[dict, bool]:
    try:
        def collect_components(element):
            parsed_components = []
            if isinstance(element, dict):
                if element.get("type") == 2:
                    parsed_components.append(element)
                for key, value in element.items():
                    parsed_components.extend(collect_components(value))
            elif isinstance(element, list):
                for item in element:
                    parsed_components.extend(collect_components(item))
            return parsed_components

        all_components = collect_components(components)

        buttons = []
        for index, comp in enumerate(all_components, start=1):
            buttons.append(comp['label'])

        extra.show_menu(buttons)
        button = extra.get_user_choice(buttons, "Choose the button")

        for index, comp in enumerate(all_components, start=1):
            if comp['label'] == button[0]:
                return comp, True

    except Exception as err:
        logger.error(f"Failed to choose button to click: {err}")
        return {}, False


def message_reactions_emojis_info(channel_id: str, message_id: str, visible_discord_token: str) -> tuple[list, bool]:
    try:
        resp = requests.get(f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=1&around={message_id}",
                            headers={
                                "Authorization": visible_discord_token
                            })

        emojis = resp.json()[0]['reactions']
        emojis_list = [f"{emoji['emoji']['name']} | Count: {emoji['count']}" for emoji in emojis]

        extra.show_menu(emojis_list)
        emojis = extra.get_user_choice(emojis_list, "Choose the emoji")
        emojis_names = [quote(emoji.split(" |")[0]) for emoji in emojis]

        return emojis_names, True

    except Exception as err:
        logger.error(f'Failed to get emojis info: {err}')
        return [], False

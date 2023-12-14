from configparser import ConfigParser


# read config.ini
def read_config() -> dict:
    settings = {}
    config = ConfigParser()
    config.read('config.ini')
    # INFO
    settings["main_discord_token"] = str(config['info']['main_discord_token'])
    settings['max_tasks_retries'] = int(config['info']['max_tasks_retries'])
    settings['max_invite_retries'] = int(config['info']['max_invite_retries'])

    pause_between_tasks = config['info']['pause_between_tasks']
    settings['pause_start'] = int(pause_between_tasks.split("-")[0])
    settings['pause_end'] = int(pause_between_tasks.split("-")[1])

    pause_between_accounts = config['info']['pause_between_accounts']
    settings['pause_accs_start'] = int(pause_between_accounts.split("-")[0])
    settings['pause_accs_end'] = int(pause_between_accounts.split("-")[1])

    # CAPTCHA
    settings["capmonster_api_key"] = str(config['captcha']['capmonster_api_key'])
    settings["2captcha_api_key"] = str(config['captcha']['2captcha_api_key'])
    settings["hcoptcha_api_key"] = str(config['captcha']['hcoptcha_api_key'])
    settings["capsolver_api_key"] = str(config['captcha']['capsolver_api_key'])
    settings["anticaptcha_api_key"] = str(config['captcha']['anticaptcha_api_key'])

    settings["captcha_service_to_use"] = str(config['captcha']['captcha_service_to_use'])

    # PROXY
    settings["mobile_proxy"] = str(config['proxy']['mobile_proxy']).strip().lower()
    settings["change_ip_pause"] = int(config['proxy']['change_ip_pause'])

    # MESSAGES
    settings["messages_endless_loop"] = str(config['messages']['endless_loop']).strip().lower()
    settings["messages_random_message"] = str(config['messages']['random_message']).strip().lower()
    pause_between_messages = config['messages']['pause_between_messages']
    settings['pause_between_message_start'] = int(pause_between_messages.split("-")[0])
    settings['pause_between_message_end'] = int(pause_between_messages.split("-")[1])


    return settings

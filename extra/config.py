from configparser import ConfigParser


# read config.ini
def read_config() -> dict:
    settings = {}
    config = ConfigParser()
    config.read('config.ini')

    settings['max_tasks_retries'] = int(config['info']['max_tasks_retries'])
    settings['max_invite_retries'] = int(config['info']['max_invite_retries'])

    pause_between_tasks = config['info']['pause_between_tasks']
    settings['pause_start'] = int(pause_between_tasks.split("-")[0])
    settings['pause_end'] = int(pause_between_tasks.split("-")[1])

    settings["capmonster_api_key"] = str(config['captcha']['capmonster_api_key'])
    settings["2captcha_api_key"] = str(config['captcha']['2captcha_api_key'])

    return settings

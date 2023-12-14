import random
import time
from concurrent.futures import ThreadPoolExecutor
from random import randint
from loguru import logger
from time import sleep
import threading
import requests
import queue
import os

import star_labs_discord
import extra


def options():
    def launch_wrapper(index, discord_token, proxy):
        account_flow(lock, index, discord_token, proxy, config, change_data, tasks_data, failed_queue)

    extra.show_menu(extra.MENU_ITEMS)
    config = extra.read_config()
    all_tasks = extra.get_user_choice(extra.MENU_ITEMS, "Choose one or a few tasks")
    tasks_data = extra.ask_for_task_data(all_tasks, config)
    if tasks_data is None:
        return

    os.system("cls")
    threads = int(input("How many threads do you want: ").strip())
    discord_tokens = extra.read_txt_file("discord tokens", "data/discord_tokens.txt")
    proxies = extra.read_txt_file("proxies", "data/proxies.txt")
    indexes = [i + 1 for i in range(len(discord_tokens))]
    mobile_proxy_queue = queue.Queue()
    failed_queue = queue.Queue()
    lock = threading.Lock()
    failed_count = 0

    change_data, ok = extra.get_change_data(tasks_data)
    if not ok:
        return

    use_proxy = True
    if len(proxies) == 0:
        if not extra.no_proxies():
            return
        else:
            use_proxy = False

    if config['mobile_proxy'].lower() == "yes":
        ip_change_links = extra.read_txt_file("ip change links", "data/ip_change_links.txt")

        for i in range(len(discord_tokens)):
            mobile_proxy_queue.put(i)
        cycle = []
        for i in range(len(proxies)):
            data_list = (proxies[i], ip_change_links[i], mobile_proxy_queue, config, lock, discord_tokens, change_data, tasks_data, failed_queue)
            cycle.append(data_list)

        with ThreadPoolExecutor() as executor:
            executor.map(mobile_proxy_wrapper, cycle)

    else:
        if not use_proxy:
            proxies = ["" for _ in range(len(discord_tokens))]
        elif len(proxies) < len(discord_tokens):
            proxies = [proxies[i % len(proxies)] for i in range(len(discord_tokens))]

        logger.info("Starting...")
        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(launch_wrapper, indexes, discord_tokens, proxies)

    while not failed_queue.empty():
        failed_count += failed_queue.get()

    print()
    logger.info(f"STATISTICS: {len(discord_tokens) - failed_count} SUCCESS | {failed_count} FAILED")
    input("Press Enter to exit...")


def account_flow(lock: threading.Lock, account_index: int, discord_token: str, proxy: str, config: dict, change_data: dict, tasks_data: dict, failed_queue: queue.Queue):
    report = False

    try:
        if tasks_data['inviter']:
            discord_instance = star_labs_discord.Inviter(account_index, proxy, discord_token, config, tasks_data['inviter']['invite_code'])
            if not wrapper(discord_instance.invite, config['max_tasks_retries']):
                report = True
            if 'captcha_bot' in tasks_data['inviter']:
                match tasks_data['inviter']['captcha_bot']:
                    case "Pandez":
                        ok = wrapper(discord_instance.bypass_pandez_bot, config['max_tasks_retries'], tasks_data['inviter']['guild_id'], tasks_data['inviter']['channel_id'], tasks_data['inviter']['message_id'])
                        if not ok:
                            report = True

                    case "CaptchaBot":
                        ok = wrapper(discord_instance.bypass_captcha_bot, config['max_tasks_retries'], tasks_data['inviter']['guild_id'], tasks_data['inviter']['channel_id'], tasks_data['inviter']['message_id'])
                        if not ok:
                            report = True

                    case "Sledgehammer":
                        ok = wrapper(discord_instance.bypass_sledgehammer_bot, config['max_tasks_retries'], tasks_data['inviter']['guild_id'], tasks_data['inviter']['channel_id'], tasks_data['inviter']['message_id'])
                        if not ok:
                            report = True

                    case "Enter Form":
                        ok = wrapper(discord_instance.bypass_enter_form, config['max_tasks_retries'], tasks_data['inviter']['invite_code'])
                        if not ok:
                            report = True
        else:
            discord_instance = star_labs_discord.DiscordTower(account_index, proxy, discord_token, config)

        if tasks_data['press button']:
            ok = wrapper(discord_instance.press_button, config['max_tasks_retries'], tasks_data['press button']['guild_id'], tasks_data['press button']['channel_id'], tasks_data['press button']['message_id'],
                         tasks_data['press button']['button_data'], tasks_data['press button']['application_id'])
            if not ok:
                report = True
            random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['press reaction']:
            for emoji in tasks_data['press reaction']['emojis_info']:
                ok = wrapper(discord_instance.send_reaction_on_message, config['max_tasks_retries'], tasks_data['press reaction']['channel_id'], tasks_data['press reaction']['message_id'],
                             emoji)
                if not ok:
                    report = True
                random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['change name']:
            ok = wrapper(discord_instance.change_name, config['max_tasks_retries'], change_data['new_names'][account_index - 1])
            if not ok:
                report = True
            random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['change username']:
            ok, _ = wrapper(discord_instance.change_self_data, config['max_tasks_retries'], "", "", change_data['passwords'][account_index - 1], change_data['new_usernames'][account_index - 1])
            if not ok:
                report = True
            random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['change password']:
            ok, new_token = wrapper(discord_instance.change_self_data, config['max_tasks_retries'], "", change_data['new_passwords'][account_index - 1], change_data['passwords'][account_index - 1], "")
            if not ok:
                report = True

            extra.update_new_token(discord_token, new_token, lock)

            random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['change profile picture']:
            ok, _ = wrapper(discord_instance.change_self_data, config['max_tasks_retries'], change_data['profile_pictures'][account_index - 1], "", "", "")
            if not ok:
                report = True
            random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['send message channel']:
            ok = wrapper(discord_instance.wrapper_send_guild_chat_message, config['max_tasks_retries'], tasks_data['send message channel']['guild_id'], tasks_data['send message channel']['channel_id'], change_data['messages_to_send'])
            if not ok:
                report = True
            random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['token checker']:
            ok, token_status = wrapper(discord_instance.token_checker, config['max_tasks_retries'])
            if not ok:
                report = True
            else:
                if token_status == "locked":
                    report_locked_token(discord_token, lock)

            random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['leave guild']:
            ok = wrapper(discord_instance.leave_guild, config['max_tasks_retries'], tasks_data['leave guild']['guild_id'])
            if not ok:
                report = True
            random_pause(config['pause_start'], config['pause_end'])

        if tasks_data['show all token guilds']:
            ok = wrapper(discord_instance.show_all_token_guilds, config['max_tasks_retries'])
            if not ok:
                report = True
            random_pause(config['pause_start'], config['pause_end'])

    except Exception as err:
        logger.error(f"{account_index} | Account flow failed: {err}")

    random_pause(config['pause_accs_start'], config['pause_accs_end'])

    if report:
        report_failed_token(discord_token, lock, failed_queue)


def wrapper(function, attempts: int, *args, **kwargs):
    for _ in range(attempts):
        result = function(*args, **kwargs)

        if isinstance(result, tuple) and result and isinstance(result[0], bool):
            if result[0]:
                return result
        elif isinstance(result, bool):
            if result:
                return True

    return result


def report_failed_token(discord_token: str, lock: threading.Lock, failed_queue: queue.Queue):
    try:
        with lock:
            with open("data/failed_tokens.txt", "a") as file:
                file.write(discord_token + "\n")
                failed_queue.put(1)
                return

    except Exception as err:
        logger.error(f"{discord_token} | Error while reporting failed token: {err}")


def report_locked_token(discord_token: str, lock: threading.Lock):
    try:
        with lock:
            with open("data/locked_tokens.txt", "a") as file:
                file.write(discord_token + "\n")
                return

    except Exception as err:
        logger.error(f"{discord_token} | Error while reporting locked token: {err}")


def random_pause(start: int, end: int):
    sleep(randint(start, end))


def mobile_proxy_wrapper(data):
    # proxies[i], ip_change_links[i], mobile_proxy_queue, config, lock, discord_tokens, change_data, tasks_data, failed_queue
    proxy, ip_change_link, q, config, lock, discord_tokens, change_data, tasks_data, failed_queue = data[:9]

    while not q.empty():
        i = q.get()

        try:
            for _ in range(3):
                try:
                    requests.get(f"{ip_change_link}",
                                 headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"},
                                 timeout=60)

                    time.sleep(config['change_ip_pause'])
                    logger.success(f"{i + 1} | Successfully changed IP")
                    break

                except Exception as err:
                    logger.error(f"{i + 1} | Mobile proxy error! Check your ip change link: {err}")
                    time.sleep(2)

            account_flow(lock, i + 1, discord_tokens[i], proxy, config, change_data, tasks_data, failed_queue)

        except Exception as err:
            logger.error(f"{i + 1} | Mobile proxy flow error: {err}")

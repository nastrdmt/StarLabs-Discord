from loguru import logger
import base64
import os


def read_txt_file(file_name: str, file_path: str) -> list:
    with open(file_path, "r") as file:
        items = [line.strip() for line in file]

    logger.success(f"Successfully loaded {len(items)} {file_name}.")
    return items


def get_change_data(tasks: dict) -> tuple[dict, bool]:
    try:
        change_data = {}

        if tasks['change name']:
            change_data['new_names'] = read_txt_file("new names", "data/new_names.txt")

        if tasks['change username']:
            with open("data/new_usernames.txt", "r") as file:
                change_data['new_usernames'] = [line.strip() for line in file]

        if tasks['change password'] or tasks['change username']:
            with open("data/passwords.txt", "r") as file:
                change_data['passwords'] = [line.strip() for line in file]

        if tasks['change password']:
            with open("data/new_passwords.txt", "r") as file:
                change_data['new_passwords'] = [line.strip() for line in file]

        if tasks['send message channel']:
            with open("data/messages_to_send.txt", "r") as file:
                change_data['messages_to_send'] = [line.strip() for line in file]

        if tasks['change profile picture']:
            encoded_images = []

            for filename in os.listdir("data/profile_pictures"):
                if filename.endswith((".png", ".jpg", ".jpeg")):
                    file_path = os.path.join("data/profile_pictures", filename)

                    with open(file_path, 'rb') as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                        encoded_images.append(encoded_image)

            change_data['profile_pictures'] = encoded_images

        return change_data, True

    except Exception as err:
        logger.error(f"Failed to get change data: {err}")
        return {}, False

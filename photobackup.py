import requests
from datetime import datetime
import json
import logging
import time

file_logger = logging.getLogger('file')
file_logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] <%(thread)d> [%(levelname)s] %(message)s', '%d.%m.%Y %H:%M:%S')
file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setFormatter(formatter)
file_logger.addHandler(file_handler)

console_logger = logging.getLogger('console')
console_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_logger.addHandler(console_handler)


class VkPhotoBackup:
    def __init__(self, photos_owner_id, vk_access_token, ya_access_token):
        self.photos_owner_id = photos_owner_id
        self.vk_access_token = vk_access_token
        self.headers = {
            'authorization': ya_access_token
        }

    def __get_photos(self):
        album_id = 'profile'
        extended = '1'
        api_version = '5.130'
        params = {
            'owner_id': self.photos_owner_id,
            'album_id': album_id,
            'extended': extended,
            'access_token': self.vk_access_token,
            'v': api_version
        }
        get_photos_api = 'https://api.vk.com/method/photos.get'

        console_logger.info(f"Getting photos from 'https://vk.com/id{(params['owner_id'])}'")
        file_logger.info('===================================================================')
        file_logger.info(f'Starting new log')
        file_logger.info(f"Getting photos from 'https://vk.com/id{(params['owner_id'])}'")
        get_photos_api_response = requests.get(get_photos_api, params=params)

        if 'error' in get_photos_api_response.json():
            error_message = get_photos_api_response.json()['error']['error_msg']
            console_logger.error(f"Failed to get photos from 'https://vk.com/id{(params['owner_id'])}'")
            console_logger.error(f"Error: {error_message}")
            file_logger.error(f"Failed to get photos from 'https://vk.com/id{(params['owner_id'])}'")
            file_logger.error(f"Error: {error_message}\n")
            return {
                'error': {
                    'message': error_message
                }
            }

        if get_photos_api_response.json()['response']['count'] == 0:
            error_message = 'The user does not have any profile photos'
            console_logger.error(f"Failed to get photos from 'https://vk.com/id{(params['owner_id'])}'")
            console_logger.error(f"Error: {error_message}")
            file_logger.error(f"Failed to get photos from 'https://vk.com/id{(params['owner_id'])}'")
            file_logger.error(f"Error: {error_message}\n")
            return {
                'error': {
                    'message': error_message
                }
            }

        console_logger.info(
            f"Successfully got [{len(get_photos_api_response.json()['response']['items'])}] photos\n")
        file_logger.info(
            f"Successfully got [{len(get_photos_api_response.json()['response']['items'])}]] photos")

        photos = []
        for photo in get_photos_api_response.json()['response']['items']:
            photos.append(
                {
                    'file_name': f"{photo['likes']['count']}_"
                                 f"{datetime.fromtimestamp(photo['date']).strftime('%d%m%Y_%H%M%S')}.jpg",
                    'size': photo['sizes'][-1]['type'],
                    'url': photo['sizes'][-1]['url']
                }
            )
        file_logger.info(f'Obtained photos: {photos}')
        return photos

    def __log_uploaded_photos(self, uploaded_photos):
        file = 'uploaded_photos.json'
        console_logger.info(f"Saving uploaded photos to file: '{file}'")
        file_logger.info(f"Saving uploaded photos to file: '{file}'")
        with open(file, 'a+', encoding='utf-8') as output_file:
            output_file.write('===================================================================\n')
            output_file.write(f"Upload session from {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n")
            json.dump(uploaded_photos, output_file, indent=4)
            output_file.write('\n\n')
        console_logger.info(f"Successfully saved photos to file '{file}'\n")
        file_logger.info(f"Successfully saved photos to file '{file}'\n")

    def __create_photos_folder(self):
        params = {
            'path': f"vkphotobackup_{str(datetime.now().strftime('%d%m%Y_%H%M%S'))}"
        }
        create_folder_api = 'https://cloud-api.yandex.net/v1/disk/resources'
        console_logger.info(f"Creating folder '{params['path']}' on Yandex Disk")
        file_logger.info(f"Creating folder '{params['path']}' on Yandex Disk")
        create_folder_api_response = requests.put(create_folder_api, headers=self.headers, params=params)

        if create_folder_api_response.status_code != 201:
            console_logger.error(
                f"Failed to create folder '{params['path']}' on Yandex Disk'")
            file_logger.error(
                f"Failed to create folder '{params['path']}' on Yandex Disk'\n")
            return {
                'error': {
                    'message': create_folder_api_response.json()['message']
                }
            }

        console_logger.info(f"Successfully created folder '{params['path']}'\n")
        file_logger.info(f"Successfully created folder '{params['path']}'")
        return params['path']

    def upload_photos(self):
        photos = self.__get_photos()
        if 'error' in photos:
            return photos['error']

        path = self.__create_photos_folder()
        if 'error' in path:
            return path['error']

        upload_photos_api = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        uploaded_photos = []
        uploaded_photos_count = 0

        console_logger.info(f"Uploading photos to folder '{path}'\n")
        file_logger.info(f"Uploading photos to folder '{path}'")
        for index, photo in enumerate(photos):
            params = {
                'url': photo['url'],
                'path': f"{path}/{photo['file_name']}"
            }

            console_logger.info(f"Uploading [{index + 1}/{len(photos)}] photo '{photo['file_name']}'")
            file_logger.info(f"Uploading [{index + 1}/{len(photos)}] photo '{photo['file_name']}'")
            upload_photos_api_response = requests.post(upload_photos_api, headers=self.headers, params=params)

            if upload_photos_api_response.status_code == 401:
                console_logger.error(
                    f"Failed to upload [{index + 1}/{len(photos)}] photo '{photo['file_name']}' to '{upload_photos_api}'")
                file_logger.error(
                    f"Failed to upload [{index + 1}/{len(photos)}] photo '{photo['file_name']}' to '{upload_photos_api}'\n")
                return upload_photos_api_response.json()

            for i in range(5):
                upload_photos_api_response_status = requests.get(
                    upload_photos_api_response.json()['href'],
                    headers=self.headers
                )
                if upload_photos_api_response_status.json()['status'] == 'success':
                    console_logger.info(f"Successfully uploaded photo '{photo['file_name']}'\n")
                    file_logger.info(f"Successfully uploaded photo '{photo['file_name']}'")
                    uploaded_photos_count += 1
                    break
                time.sleep(2)
            else:
                console_logger.warning(f"Photo '{photo['file_name']}' could not be uploaded in 10 second\n")
                file_logger.warning(f"Photo '{photo['file_name']}' could not be uploaded in 10 second")

            uploaded_photos.append(
                {
                    'file_name': photo['file_name'],
                    'size': photo['size']
                }
            )
        console_logger.info(
            f"Successfully uploaded {uploaded_photos_count}/{len(photos)} photos\n")
        file_logger.info(f"Successfully uploaded {uploaded_photos_count}/{len(photos)} photos")

        self.__log_uploaded_photos(uploaded_photos)

        return {
            'message': f'{uploaded_photos_count}/{len(photos)} photos successfully uploaded'
        }

from pprint import pprint
import datetime
import requests
import os
import json
import os.path
from dotenv import load_dotenv
from tqdm import tqdm
from time import sleep

# import google.auth
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

dotenv_path = 'config_example.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
vk_token = os.getenv('VK_TOKEN')
ya_token = os.getenv('YD_TOKEN')
gd_token = os.getenv('GD_TOKEN')

def main():
    class VKDownload:
        API_BASE_URL = 'https://api.vk.com/method'

        def __init__(self, token, version='5.199'):
            self.token = token
            self.version = version
            self.params = {
                'access_token': self.token,
                'v': self.version
            }

        def get_common_params(self, count=50, offset=0):
            return {
                'access_token': self.token,
                'v': '5.199',
                'extended': '1',
                'photo_sizes': '1'
            }

        def _build_url(self, api_method):
            return f'{self.API_BASE_URL}/{api_method}'

        def users_info(self, user_id: str):
            params = self.get_common_params()
            params.update({'user_ids': user_id})
            response = requests.get(self._build_url('users.get'), params=params)
            return response.json()

        def get_photos(self, offset=0, count=50):
            params = self.get_common_params()
            params.update({'owner_id': user_id, 'album_id': album_id, 'count': count, 'offset': offset})
            response = requests.get(self._build_url('photos.get'), params=params)
            return response.json()

        def get_all_photos(self):
            data = self.get_photos()
            all_photo_count = data['response']['count']
            i = 0
            count = 50
            photos = []
            max_size_photo = {}

            # Создаем папку на ПК для фото
            if not os.path.exists(f'id{user_id}_photo'):
                os.mkdir(f'id{user_id}_photo')

            # Перебираем все фото
            while i <= all_photo_count:
                if i != 0:
                    data = self.get_photos(offset=i, count=count)
                # Выбираем фото максимального размера и присваиваем фото имя по количеству лайков и записываем в словарь max_size_photos
                for photo in data['response']['items']:
                    photo['date'] = datetime.date.fromtimestamp(photo['date'])
                    max_size = 0
                    photos_info = {}
                    for size in photo['sizes']:
                        if size['height'] >= max_size:
                            max_size = size['height']
                    # Проверяем, есть ли уже фото с таким же количеством лайков и, если есть, добавляем к имени дату загрузки
                    if photo['likes']['count'] not in max_size_photo.keys():
                        max_size_photo[photo['likes']['count']] = size['url']
                        photos_info['file_name'] = f"{photo['likes']['count']}.jpg"
                    else:
                        max_size_photo[f"{photo['likes']['count']} _ {photo['date']}"] = size['url']
                        photos_info['file_name'] = f"{photo['likes']['count']} _ {photo['date']}.jpg"

                    # Формируем список всех фотографий для дальнейшей упаковки в файл .json
                    photos_info['size'] = size['type']
                    photos.append(photos_info)

                for photo_name, photo_url in tqdm(max_size_photo.items(), desc='Total'):
                    with open(f'id{user_id}_photo/%s' % f'{photo_name}.jpg', 'wb') as file:
                        img = requests.get(photo_url)
                        file.write(img.content)
                i += count
            print(f'Загружено {len(max_size_photo)} фото')

            # Записываем данные о всех скачанных фотографиях в файл photos.json
            with open("photos.json", "w") as file:
                json.dump(photos, file, indent=4)

    class YaUploader:
        def __init__(self, token: str):
            self.token = token

        def folder_creation(self):
            url = f'https://cloud-api.yandex.net/v1/disk/resources/'
            headers = {'Content-Type': 'application/json',
                       'Authorization': f'OAuth {ya_token}'}
            params = {'path': f'{folder_name}',
                      'overwrite': 'true'}
            response = requests.put(url=url, headers=headers, params=params)

        def upload(self, file_path: str):
            url = 'https://cloud-api.yandex.net/v1/disk/resources/upload/'
            headers = {'Content-Type': 'application/json',
                       'Authorization': f'OAuth {ya_token}'}
            params = {'path': f'{folder_name}/{file_name}',
                      'overwrite': 'true'}

            # Получение ссылки на загрузку
            response = requests.get(url=url, headers=headers, params=params)
            href = response.json().get('href')

            # Загрузка файла
            uploader = requests.put(href, data=open(files_path, 'rb'))

    class GDUploader:
        def folder_creation():
            creds, _ = google.auth.default()

            try:
                # create drive api client
                service = build("drive", "v3", credentials=creds)
                file_metadata = {
                    "name": "Invoices",
                    "mimeType": "application/vnd.google-apps.folder",
                }

                # pylint: disable=maybe-no-member
                file = service.files().create(body=file_metadata, fields="id").execute()
                print(f'Folder ID: "{file.get("id")}".')
                return file.get("id")

            except HttpError as error:
                print(f"Произошла ошибка: {error}")
                return None


    user_id = str(input('Введите id пользователя VK: '))
    vk = VKDownload(vk_token, user_id)
    album_id = str(input('Введите id альбома ВК (profile, wall): '))
    vk.get_all_photos()
    # disk = 'Яндекс диск'

    current_drive = 'YD' # str(input('Введите тип диска (YD или GD): '))
    uploader = None
    if current_drive == 'YD':
        disk = 'Яндекс диск'
        uploader = YaUploader(ya_token)
    elif current_drive == 'GD':
        uploader = GDUploader(gd_token)
        disk = 'Гугл диск'

    folder_name = f'id{user_id}_photo'
    uploader.folder_creation()

    photos_list = os.listdir(folder_name)
    count = 0
    for photo in tqdm(photos_list, desc='Total'):
        sleep(0.01)
        file_name = photo
        files_path = os.getcwd() + '\\' + folder_name +'\\' + photo
        result = uploader.upload(files_path)
        count += 1
    print(f'На {disk} загружено фотографий: {count}')

if __name__ == '__main__':
    main()

import json
import requests
from pprint import pprint
from config import vk_token, ya_token


class VK:

    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_photos(self):
        data = {}
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id if self.id.isdigit() else self.users_info()['response'][0]['id'],
                  'album_id': 'profile',
                  'extended': 1,
                  }
        response = requests.get(url, params={**self.params, **params})
        if response.status_code == 200:
            photos = response.json()['response']['items']
            for photo in photos:
                id, likes, url, date = photo['id'], photo['likes']['count'], get_max_width(
                    photo), photo['date']
                data[f'{id}'] = {'likes': likes,
                                 'url': url,
                                 'date': date,
                                 'name': likes
                                 }

            if data:
                search_rename(data)
                data = search_rename(data)
                with open('file.json', 'w+', encoding='UTF8') as f:
                    json.dump(data, f)
                    print('файл создан')
            else:
                print('нет данных')


class YA:
    url_ya_api = 'https://cloud-api.yandex.net/v1/disk/resources'

    def upload_photo(self, ya_token):

        # функция загрузки фото
        def urls(names: list):
            target_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            # тянем данные для загрузки из файла
            with open('file.json', 'r') as f:
                data = json.load(f)
                for id, value in enumerate(data.values()):
                    print('файл', value['name'])
                    # сверяем с текущими файлами в папке на ya disk, если нет то отправляем запрос на закачку, если есть то пропускаем
                    if f"{value['name']}" not in names:
                        response = requests.post(url=target_url, headers=headers, params={
                            'path': f'{path}/{value['name']}', 'url': value['url']})
                        print(f'обработан, загружен {id+1}/{len(data)}')
                    else:
                        print(f'обработан, пропущен {id+1}/{len(data)}')
                print('готово')

        headers = {'Authorization': ya_token,
                   'Accept': 'application/json'}

        path = str(input('Укажите куда залить файлы на ya.disk=')) or 'Vk_photo'
        print(path)
        params = {'path': path}

        response = requests.get(url=self.url_ya_api,
                                headers=headers, params=params)
        # проверяем существует ли папка для ВК фото, если да то грузим, если нет то создаем и грузим
        if response.status_code == 200:
            # получаю список дочерних элементов папки
            files_in_dir_ya = requests.get(url=self.url_ya_api, headers=headers, params={
                                           **params, **{'fields': '_embedded.items.name'}}).json()["_embedded"]["items"]
            names = list(set([a['name'] for a in files_in_dir_ya]))
            urls(names)
        else:
            create_query = requests.put(url=self.url_ya_api,
                                        headers=headers, params=params)

            if create_query.status_code == 201:
                print(f'создана папка {params["path"]}')
                urls([])

# метод для получения максимального размера фото из ВК


def get_max_width(object):
    if object.get('orig_photo'):
        return object['orig_photo']['url']
    else:
        return object['sizes'][-1]['url']


# метод для поиска повторов в лайках
def search_rename(data: dict):
    pre_set = {}
    # формируем словарь ключ/кол-во лайков
    for key, value in data.items():
        pre_set[key] = value['likes']

    # поиск повторяющихся лайков
    likes = list(pre_set.values())
    likes_set = list(set(likes))
    repeating_likes = [v for v in likes_set if likes.count(v) > 1]
    repeating_ids = [k for k, v in pre_set.items() if v in repeating_likes]
    # замена имени в повторах
    for el in repeating_ids:
        data[el]['name'] = f"{data[el]['likes']}_{data[el]['date']}"
    return data


user_id_vk = 'erbol_rustemov'

vk = VK(access_token=vk_token, user_id=user_id_vk)
# pprint(vk.users_info())
photos = vk.get_photos()

obj = YA()
obj.upload_photo(ya_token)

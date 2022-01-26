"""
По материалам статьи "СТАТИЧЕСКАЯ OSM КАРТА НА PYTHON"
https://smyt.ru/blog/statc-osm-map-with-python/
"""
import io
import math
import os
import tempfile
import requests
import random
from cairo import ImageSurface, FORMAT_ARGB32, Context
import mercantile


class Route:
    """
    Класс объекта построения пути по OSM карте с использование менеджера контекста

    Пример использования:
    with Route(36.07087, 52.98307, 36.0688, 52.9899) as rout:
        print(f"Расстояние: {rout['distance']} м., время в пути: {rout['duration']} мин.")
        print(rout['img_route']) -> <_io.BufferedReade>
    """

    def __init__(self, w_1, s_1, w_2, s_2):
        self.w_1 = w_1
        self.s_1 = s_1
        self.w_2 = w_2
        self.s_2 = s_2

    def _get_img(self, url):
        """ Загрузка тайлов из OpenStreetMap

        :param url: url
        :return: PNG content
        """
        headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '1',
            'Sec-Fetch-Dest': 'document',
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '0',
            'sec-ch-ua-platform': '"Windows"',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        response = requests.get(url=url, headers=headers)
        return response

    def _get_map(self, west, south, east, north, zoom: int):
        """ Создаёт фрагмент карты с координатами

        :param west: координаты
        :param south: координаты
        :param east: координаты
        :param north: координаты
        :param zoom: масштаб
        :return: dict {ImageSurface: ImageSurface, bounds: west: GPS координаты ..}
        """
        tiles = list(mercantile.tiles(west, south, east, north, zoom))
        # Список тайлов
        # print(tiles)
        tile_size = (256, 256)

        min_x = min([t.x for t in tiles])
        min_y = min([t.y for t in tiles])
        max_x = max([t.x for t in tiles])
        max_y = max([t.y for t in tiles])

        # Создаём пустую поверхности для изображения в которое будем вставлять тайлы
        map_image = ImageSurface(
            FORMAT_ARGB32,
            tile_size[0] * (max_x - min_x + 1),
            tile_size[1] * (max_y - min_y + 1)
        )
        # Создаем контекст для рисования
        ctx = Context(map_image)
        # Встявляем тайы в ImageSurface (поверхность для изображения)
        for t in tiles:
            server = random.choice(['a', 'b', 'c'])
            url = 'http://{server}.tile.openstreetmap.org/{zoom}/{x}/{y}.png'.format(
                server=server,
                zoom=t.z,
                x=t.x,
                y=t.y
            )
            response = self._get_img(url)
            img = ImageSurface.create_from_png(io.BytesIO(response.content))
            # указываем корректный сдвиг
            ctx.set_source_surface(
                img,
                (t.x - min_x) * tile_size[0],
                (t.y - min_y) * tile_size[1]
            )
            ctx.paint()
        # сохраняем собраное изображение в файл
        # with open("map.png", "wb") as f:
        #     map_image.write_to_png(f)
        return {
            'image': map_image,
            # определим реально занимаемую тайлами область,
            # для этого будем конвертить тайл в gps координаты,
            # а потом уже искать минимум и максимум
            'bounds': {
                "west": min([mercantile.bounds(t).west for t in tiles]),
                "east": max([mercantile.bounds(t).east for t in tiles]),
                "south": min([mercantile.bounds(t).south for t in tiles]),
                "north": max([mercantile.bounds(t).north for t in tiles]),
            }
        }

    def _get_routing(self, w_1, s_1, w_2, s_2) -> dict:
        """ Возвращает список координат пути

        :param w_1: координаты начала
        :param s_1: координаты начала
        :param w_2: координаты конца
        :param s_2: координаты конца
        :return: dict {'coordinates':coordinates, 'distance':distance, 'duration':duration}
        """
        url = f'https://routing.openstreetmap.de/routed-foot/route/v1/driving/{w_1},{s_1};{w_2},{s_2}?overview=full&geometries=geojson'
        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '0',
            'sec-ch-ua-platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 '
                          'Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                      'application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '1',
            'Sec-Fetch-Dest': 'document',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        response = requests.get(url=url, headers=headers).json()
        coordinates = response['routes'][0]['geometry']['coordinates']
        distance = response['routes'][0]['distance']
        duration = response['routes'][0]['duration']
        distance = int(round(distance, 0))
        duration = duration // 60
        return {'coordinates': coordinates, 'distance': distance, 'duration': duration}

    def _get_img_routing(self, w_1, s_1, w_2, s_2):
        """ Отрисовка пути на карте

        :param w_1: координаты начала
        :param s_1: координаты начала
        :param w_2: координаты конца
        :param s_2: координаты конца
        :return:
        """
        # Загружаем координаты и информацию о пути
        dc_rout = self._get_routing(w_1, s_1, w_2, s_2)
        # Определение координат для загрузки тайлов
        min_w = min([t[0] for t in dc_rout['coordinates']])
        min_s = min([t[1] for t in dc_rout['coordinates']])
        max_w = max([t[0] for t in dc_rout['coordinates']])
        max_s = max([t[1] for t in dc_rout['coordinates']])
        west = round(min_w, 6)
        south = round(min_s, 6)
        east = round(max_w, 6)
        north = round(max_s, 6)
        zoom = 17
        # Получаем фрагмент карты с координатами
        out = self._get_map(west, south, east, north, zoom)
        # рассчитываем координаты углов в веб-меркаторе
        leftTop = mercantile.xy(out['bounds']['west'], out['bounds']['north'])
        rightBottom = mercantile.xy(out['bounds']['east'], out['bounds']['south'])
        # расчитываем коэффициенты
        kx = out['image'].get_width() / (rightBottom[0] - leftTop[0])
        ky = out['image'].get_height() / (rightBottom[1] - leftTop[1])
        # Создание контекста рисунка
        context = Context(out['image'])
        # Отрисовку маркеров начала
        c = dc_rout['coordinates'][0]
        x, y = mercantile.xy(c[0], c[1])
        x = (x - leftTop[0]) * kx
        y = (y - leftTop[1]) * ky
        context.arc(x, y, 12, 0, 2 * math.pi)
        context.set_source_rgba(0, 1, 0, 0.8)  # зёный
        context.fill()  # заливаем контур выбранным цветом
        # Отрисовка надмиси "Я"
        context.move_to(x - 5, y + 2)
        context.set_source_rgba(0, 0, 0)  # чёрная заливка
        context.set_font_size(15)  # выбираем размер шрифта, можно дробный
        context.show_text("Я")  # пишем слово «буквы»
        # Отрисовку маркеров конца пути
        c = dc_rout['coordinates'][-1]
        x, y = mercantile.xy(c[0], c[1])
        x = (x - leftTop[0]) * kx
        y = (y - leftTop[1]) * ky
        context.arc(x, y, 5, 0, 2 * math.pi)
        context.set_source_rgba(0, 0, 1, 0.8)  # синий, полупрозрачный
        context.fill()  # заливаем контур выбранным цветом
        # отрисовка траектории пути
        for c in dc_rout['coordinates']:
            # конвертируем gps в web-mercator
            x, y = mercantile.xy(c[0], c[1])
            # переводим x, y в координаты изображения
            x = (x - leftTop[0]) * kx
            y = (y - leftTop[1]) * ky
            # проводим линию
            context.line_to(x, y)
        # заливка траектории пути
        context.set_source_rgba(1, 0, 0, 0.8)  # красный, полупрозрачный
        context.set_dash([14.0, 6.0])  # пунктир
        context.set_line_width(4)  # ширина пикселей
        context.stroke()  # обводим контур выбранной линией
        # ОТЛАДКА сохранение результатов
        # with open('map_with_route.png', 'wb') as f:
        #     out['image'].write_to_png(f)
        # Схранение результатов во временный файл
        self.fd, self.path = tempfile.mkstemp(suffix='.img', dir='./')
        with open(self.path, 'wb') as f: \
                out['image'].write_to_png(f)
        return dc_rout

    def __enter__(self):
        dc_rout = self._get_img_routing(self.w_1, self.s_1, self.w_2, self.s_2)
        self.f = open(self.path, 'rb')
        dc_rout['img_route'] = self.f
        return dc_rout

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Метод вызывается при выходе из контекста
        """
        self.f.close()
        if not os.path.exists(self.path):
            return None
        # закрываем дескриптор файла
        os.close(self.fd)
        # уничтожаем файл
        os.unlink(self.path)

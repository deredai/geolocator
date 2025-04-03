import requests
import urllib.parse


def get_nearby_objects_osm(lat, lon, radius=1000, filter_types=["достопримечательность"]):
    """
    Функция для поиска объектов с помощью Overpass API (OpenStreetMap).
    Поддерживает несколько фильтров одновременно (например, музеи и церкви).

    Аргументы:
        lat (float): Широта геопозиции
        lon (float): Долгота геопозиции
        radius (int): Радиус поиска в метрах (по умолчанию 1000 м)
        filter_types (list): Список типов объектов для фильтрации (например, ["музей", "церковь"])

    Возвращает:
        list: Список объектов с названием, типом, ссылками и координатами
    """
    overpass_url = "http://overpass-api.de/api/interpreter"

    # Определяем теги для фильтрации
    filter_tags = {
        "достопримечательность": '["tourism"]',
        "кафе": '["amenity"="cafe"]',
        "ресторан": '["amenity"="restaurant"]',
        "магазин": '["shop"]',
        "церковь": '["amenity"="place_of_worship"]',
        "музей": '["tourism"="museum"]',
        "статуя": '["tourism"="artwork"]',
        "дворец": '["attraction"]'
    }

    # Формируем части запроса для каждого фильтра
    query_parts = []
    for f_type in filter_types:
        filter_tag = filter_tags.get(f_type.lower(), '["tourism"]')
        query_parts.append(f'node(around:{radius},{lat},{lon}){filter_tag}')

    # Собираем полный Overpass QL запрос
    query = f"""
    [out:json];
    (
      {" ; ".join(query_parts)};
    );
    out body;
    """

    try:
        response = requests.post(overpass_url, data=query)
        response.raise_for_status()
        data = response.json()

        objects = []
        for element in data["elements"]:
            tags = element.get("tags", {})

            # Проверяем наличие названия и пропускаем объекты без имени
            name = tags.get("name")
            if not name:
                continue

            # Координаты объекта
            obj_lat = element["lat"]
            obj_lon = element["lon"]

            # Ссылка на OpenStreetMap
            osm_url = f"https://www.openstreetmap.org/?mlat={obj_lat}&mlon={obj_lon}#map=16/{obj_lat}/{obj_lon}"

            # Ссылка на Яндекс.Карты с привязкой к объекту
            encoded_name = urllib.parse.quote(name)
            yandex_url = f"https://yandex.ru/maps/?ll={obj_lon},{obj_lat}&z=16&text={encoded_name}"

            # Ссылка на сайт объекта (если есть)
            website = tags.get("website") or tags.get("contact:website", "Сайт отсутствует")

            # Определяем тип объекта из тегов или списка фильтров
            obj_type = tags.get("tourism") or tags.get("amenity") or tags.get("shop")
            if not obj_type:
                for f_type in filter_types:
                    if f_type.lower() in filter_tags and filter_tags[f_type.lower()] in str(element):
                        obj_type = f_type
                        break
                obj_type = obj_type or filter_types[0]  # По умолчанию первый фильтр

            objects.append({
                "name": name,
                "type": obj_type,
                "osm_url": osm_url,
                "yandex_url": yandex_url,
                "website": website,
                "longitude": obj_lon,
                "latitude": obj_lat
            })

        return objects

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Overpass API: {e}")
        return []
    except (KeyError, IndexError) as e:
        print(f"Ошибка при обработке ответа: {e}")
        return []


if __name__ == "__main__":
    latitude = 59.930025
    longitude = 30.286968

    objects = get_nearby_objects_osm(latitude, longitude, radius=10000, filter_types=["дворец"])

    if objects:
        print("Найденные объекты:")
        for obj in objects:
            print(f"Название: {obj['name']}")
            print(f"Тип: {obj['type']}")
            print(f"Ссылка на OSM: {obj['osm_url']}")
            print(f"Ссылка на Яндекс.Карты: {obj['yandex_url']}")
            print(f"Ссылка на сайт: {obj['website']}")
            print(f"Координаты: ({obj['latitude']}, {obj['longitude']})")
            print("-" * 40)
    else:
        print("Объекты не найдены или произошла ошибка.")
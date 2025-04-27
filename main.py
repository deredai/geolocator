import requests
import urllib.parse


def get_nearby_objects_osm(lat, lon, radius=1000,
                           filter_types=["статуя", "памятник", "церковь", "дацан", "мечеть", "индуистский храм",
                                         "музей", "достопримечательность"]):
    """
    Функция для поиска объектов (статуи, памятники, храмы, музеи, достопримечательности) с помощью Overpass API (OpenStreetMap).
    Ссылка на Яндекс.Карты включает метку на месте объекта.

    Аргументы:
        lat (float): Широта геопозиции
        lon (float): Долгота геопозиции
        radius (int): Радиус поиска в метрах (по умолчанию 1000 м)
        filter_types (list): Список типов объектов для фильтрации (например, ["статуя", "памятник", "церковь", "дацан", "мечеть", "индуистский храм", "музей", "достопримечательность"])

    Возвращает:
        list: Список объектов с названием, типом, ссылками, координатами, адресом и сайтом
    """
    overpass_url = "http://overpass-api.de/api/interpreter"

    query_parts = []
    for f_type in filter_types:
        f_type_lower = f_type.lower()
        if f_type_lower == "статуя":
            query_parts.append(f'node(around:{radius},{lat},{lon})["artwork"="statue"]["name"]')
            query_parts.append(f'node(around:{radius},{lat},{lon})["artwork"="sculpture"]["name"]')
            query_parts.append(f'way(around:{radius},{lat},{lon})["artwork"="statue"]["name"]')
            query_parts.append(f'way(around:{radius},{lat},{lon})["artwork"="sculpture"]["name"]')
        elif f_type_lower == "памятник":
            query_parts.append(f'node(around:{radius},{lat},{lon})["historic"="monument"]["name"]')
            query_parts.append(f'node(around:{radius},{lat},{lon})["historic"="memorial"]["name"]')
            query_parts.append(f'way(around:{radius},{lat},{lon})["historic"="monument"]["name"]')
            query_parts.append(f'way(around:{radius},{lat},{lon})["historic"="memorial"]["name"]')
        elif f_type_lower in ["церковь", "дацан", "мечеть", "индуистский храм"]:
            query_parts.append(f'node(around:{radius},{lat},{lon})["amenity"="place_of_worship"]["name"]')
            query_parts.append(f'way(around:{radius},{lat},{lon})["amenity"="place_of_worship"]["name"]')
        elif f_type_lower == "музей":
            query_parts.append(f'node(around:{radius},{lat},{lon})["tourism"="museum"]["name"]')
            query_parts.append(f'way(around:{radius},{lat},{lon})["tourism"="museum"]["name"]')
        elif f_type_lower == "достопримечательность":
            query_parts.append(f'node(around:{radius},{lat},{lon})["tourism"]["name"]')
            query_parts.append(f'way(around:{radius},{lat},{lon})["tourism"]["name"]')

    query = f"""
    [out:json];
    (
      {" ; ".join(query_parts)};
    );
    out center;
    """

    try:
        response = requests.post(overpass_url, data=query)
        response.raise_for_status()
        data = response.json()

        objects = []
        seen_names = set()

        for element in data["elements"]:
            tags = element.get("tags", {})

            name = tags.get("name")
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            if element["type"] == "node":
                obj_lat = element["lat"]
                obj_lon = element["lon"]
            else:
                obj_lat = element["center"]["lat"]
                obj_lon = element["center"]["lon"]

            osm_url = f"https://www.openstreetmap.org/?mlat={obj_lat}&mlon={obj_lon}#map=16/{obj_lat}/{obj_lon}"

            encoded_name = urllib.parse.quote(name)
            yandex_url = f"https://yandex.ru/maps/?ll={obj_lon},{obj_lat}&z=16&text={encoded_name}&pt={obj_lon},{obj_lat},pm2rdm"

            address_parts = []
            if tags.get("addr:street"):
                address_parts.append(tags["addr:street"])
            if tags.get("addr:housenumber"):
                address_parts.append(tags["addr:housenumber"])
            if tags.get("addr:city"):
                address_parts.append(tags["addr:city"])
            if tags.get("addr:postcode"):
                address_parts.append(tags["addr:postcode"])
            if tags.get("addr:country"):
                address_parts.append(tags["addr:country"])

            address = ", ".join(address_parts) if address_parts else "Адрес не указан"
            website = tags.get("website") or tags.get("contact:website") or "Сайт отсутствует"

            obj_type = "интересное место"
            if "artwork" in tags and tags["artwork"] in ["statue", "sculpture"]:
                obj_type = "статуя"
            elif "historic" in tags and tags["historic"] in ["monument", "memorial"]:
                obj_type = "памятник"
            elif "amenity" in tags and tags["amenity"] == "place_of_worship":
                religion = tags.get("religion", "").lower()
                if religion == "christian":
                    obj_type = "церковь"
                elif religion == "buddhist":
                    obj_type = "дацан"
                elif religion == "muslim":
                    obj_type = "мечеть"
                elif religion == "hindu":
                    obj_type = "индуистский храм"
            elif "tourism" in tags and tags["tourism"] == "museum":
                obj_type = "музей"
            elif "tourism" in tags:
                obj_type = "достопримечательность"

            if obj_type not in filter_types:
                continue

            objects.append({
                "name": name,
                "type": obj_type,
                "osm_url": osm_url,
                "yandex_url": yandex_url,
                "website": website,
                "longitude": obj_lon,
                "latitude": obj_lat,
                "address": address
            })

        return objects

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Overpass API: {e}")
        return []
    except (KeyError, IndexError) as e:
        print(f"Ошибка при обработке ответа: {e}")
        return []


# Пример использования
if __name__ == "__main__":
    # Координаты (Санкт-Петербург, рядом с Дацаном Гунзэчойнэй)
    latitude = 59.955232
    longitude = 30.323435

    # Поиск статуй, памятников, храмов, музеев и достопримечательностей в радиусе 1000 м
    objects = get_nearby_objects_osm(latitude, longitude, radius=250,
                                     filter_types=["музей"])

    # Вывод результатов
    if objects:
        print("Найденные объекты:")
        for obj in objects:
            print(f"Название: {obj['name']}")
            print(f"Тип: {obj['type']}")
            print(f"Ссылка на OSM: {obj['osm_url']}")
            print(f"Ссылка на Яндекс.Карты: {obj['yandex_url']}")
            print(f"Ссылка на сайт: {obj['website']}")
            print(f"Координаты: ({obj['latitude']}, {obj['longitude']})")
            print(f"Адрес: {obj['address']}")
            print("-" * 40)
    else:
        print("Объекты не найдены или произошла ошибка.")
 Класс объекта построения пути по OSM карте с использование менеджера контекста

    Пример использования:
    with Route(36.07087, 52.98307, 36.0688, 52.9899) as rout:
        print(f"Расстояние: {rout['distance']} м., время в пути: {rout['duration']} мин.")
        print(rout['img_route']) -> <_io.BufferedReade>
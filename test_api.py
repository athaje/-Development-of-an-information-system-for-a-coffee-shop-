# test_api.py
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_json(data, title=""):
    """Красиво выводит JSON данные"""
    if title:
        print(title)
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        print(data)

def wait_for_server():
    """Ожидание запуска сервера"""
    print("Ожидание запуска сервера...")
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                print("Сервер запущен!")
                return True
        except requests.exceptions.ConnectionError:
            if attempt < max_attempts - 1:
                print(f"Попытка {attempt + 1}/{max_attempts}...")
                import time
                time.sleep(2)
            else:
                print("Не удалось подключиться к серверу")
                return False

def test_api():
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ API КОФЕЙНИ")
    print("=" * 70)
    
    # Проверяем подключение к серверу
    if not wait_for_server():
        print("Убедитесь, что сервер запущен на http://localhost:8000")
        sys.exit(1)
    
    try:
        # 1. Проверка основного эндпоинта
        print("\n1. Проверка основного эндпоинта: GET /")
        response = requests.get(f"{BASE_URL}/")
        print(f"Статус: {response.status_code}")
        print_json(response.json(), "Ответ:")
        
        # 2. Проверка состояния базы данных
        print("\n2. Проверка состояния базы данных: GET /database/health")
        response = requests.get(f"{BASE_URL}/database/health")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"База данных: {health_data.get('status', 'unknown')}")
            print(f"Тип БД: {health_data.get('database', 'unknown')}")
        else:
            print("Ошибка:", response.text)
        
        # 3. Получение всех клиентов
        print("\n3. Получение всех клиентов: GET /customers")
        response = requests.get(f"{BASE_URL}/customers")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            customers = response.json()
            print(f"Найдено {len(customers)} клиентов:")
            print_json(customers, "Клиенты:")
            customer_id = customers[0]['id'] if customers else None
        else:
            print("Ошибка:", response.text)
            return
        
        # 4. Получение всего меню
        print("\n4. Получение всего меню: GET /menu")
        response = requests.get(f"{BASE_URL}/menu")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            menu_items = response.json()
            print(f"Найдено {len(menu_items)} пунктов меню:")
            print_json(menu_items, "Меню:")
            menu_item_id = menu_items[0]['id'] if menu_items else None
        else:
            print("Ошибка:", response.text)
            return
        
        # 5. Получение только доступного меню
        print("\n5. Получение доступного меню: GET /menu/available")
        response = requests.get(f"{BASE_URL}/menu/available")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            available_menu = response.json()
            print(f"Доступно {len(available_menu)} пунктов:")
            print_json(available_menu, "Доступное меню:")
        
        # 6. Получение меню по категории
        print("\n6. Получение напитков: GET /menu/напиток")
        response = requests.get(f"{BASE_URL}/menu/напиток")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            drinks = response.json()
            print(f"Найдено {len(drinks)} напитков:")
            print_json(drinks, "Напитки:")
        
        # 7. Создание нового клиента
        print("\n7. Создание нового клиента: POST /customers")
        new_customer = {
            "name": "Анна Смирнова",
            "phone": "+79045556677",
            "email": "anna@example.com"
        }
        response = requests.post(f"{BASE_URL}/customers", json=new_customer)
        print(f"Статус: {response.status_code}")
        if response.status_code == 201:
            print("Новый клиент создан:")
            created_customer = response.json()
            print_json(created_customer, "Данные клиента:")
            new_customer_id = created_customer['id']
        else:
            print("Ошибка:", response.text)
        
        # 8. Получение конкретного клиента
        if customer_id:
            print(f"\n8. Получение клиента по ID: GET /customers/{customer_id}")
            response = requests.get(f"{BASE_URL}/customers/{customer_id}")
            print(f"Статус: {response.status_code}")
            if response.status_code == 200:
                print("Клиент найден:")
                print_json(response.json(), "Данные клиента:")
            else:
                print("Ошибка:", response.text)
        
        # 9. Получение всех заказов
        print("\n9. Получение всех заказов: GET /orders")
        response = requests.get(f"{BASE_URL}/orders")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            orders = response.json()
            print(f"Найдено {len(orders)} заказов:")
            for order in orders:
                print(f"  - Заказ #{order['id']}: {order['status']}, {order['total_amount']} руб.")
            order_id = orders[0]['id'] if orders else None
        else:
            print("Ошибка:", response.text)
            return
        
        # 10. Создание нового заказа
        if customer_id:
            print("\n10. Создание нового заказа: POST /orders")
            new_order = {
                "customer_id": customer_id,
                "total_amount": 500.0
            }
            response = requests.post(f"{BASE_URL}/orders", json=new_order)
            print(f"Статус: {response.status_code}")
            if response.status_code == 201:
                print("Заказ успешно создан!")
                created_order = response.json()
                print_json(created_order, "Данные заказа:")
                new_order_id = created_order['id']
            else:
                print("Ошибка:", response.text)
                new_order_id = None
        else:
            print("Недостаточно данных для создания заказа")
            new_order_id = None
        
        # 11. Добавление позиции в заказ
        if new_order_id and menu_item_id:
            print("\n11. Добавление позиции в заказ: POST /order-items")
            order_item = {
                "order_id": new_order_id,
                "menu_item_id": menu_item_id,
                "quantity": 2,
                "customizations": "Без сахара"
            }
            response = requests.post(f"{BASE_URL}/order-items", json=order_item)
            print(f"Статус: {response.status_code}")
            if response.status_code == 201:
                print("Позиция добавлена в заказ!")
                created_item = response.json()
                print_json(created_item, "Данные позиции:")
            else:
                print("Ошибка:", response.text)
        
        # 12. Получение конкретного заказа
        if order_id:
            print(f"\n12. Получение заказа по ID: GET /orders/{order_id}")
            response = requests.get(f"{BASE_URL}/orders/{order_id}")
            print(f"Статус: {response.status_code}")
            if response.status_code == 200:
                print("Заказ найден:")
                print_json(response.json(), "Данные заказа:")
            else:
                print("Ошибка:", response.text)
        
        # 13. Проверка ошибок
        print("\n13. Тестирование обработки ошибок")
        
        # Несуществующий клиент
        print("   GET /customers/999999:")
        response = requests.get(f"{BASE_URL}/customers/999999")
        print(f"   Статус: {response.status_code}")
        print(f"   Ожидаемый: 404")
        
        # Создание заказа с несуществующим клиентом
        print("   POST /orders с несуществующим клиентом:")
        invalid_order = {
            "customer_id": 999999,
            "total_amount": 100.0
        }
        response = requests.post(f"{BASE_URL}/orders", json=invalid_order)
        print(f"   Статус: {response.status_code}")
        print(f"   Ожидаемый: 404")
        
        # Некорректный запрос
        print("   POST /customers без обязательных полей:")
        invalid_customer = {
            "name": "Только имя"
        }
        response = requests.post(f"{BASE_URL}/customers", json=invalid_customer)
        print(f"   Статус: {response.status_code}")
        print(f"   Ожидаемый: 422")
        
        print("\n" + "=" * 70)
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("=" * 70)
        print("\nДля проверки всех эндпоинтов откройте:")
        print(" Документация API: http://localhost:8000/docs")
        print("\nПримеры команд для тестирования:")
        print("  Получить всех клиентов:")
        print(f"  curl {BASE_URL}/customers")
        print("\n  Создать нового клиента:")
        print(f'  curl -X POST {BASE_URL}/customers \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"name": "Тест", "phone": "+79000000000"}\'')
        print("\n  Проверить состояние БД:")
        print(f"  curl {BASE_URL}/database/health")
        
    except requests.exceptions.RequestException as e:
        print(f"\nОшибка сети: {e}")
        print("Убедитесь, что сервер запущен и доступен")
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()

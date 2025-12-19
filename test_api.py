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
    print("⏳ Ожидание запуска сервера...")
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                print("Сервер запущен!")
                return True
        except requests.exceptions.ConnectionError:
            if attempt < max_attempts - 1:
                print(f"   Попытка {attempt + 1}/{max_attempts}...")
                import time
                time.sleep(2)
            else:
                print("Не удалось подключиться к серверу")
                return False

def test_api():
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ API КОФЕЙНИ (ПОЛНАЯ ВЕРСИЯ)")
    print("=" * 70)
    
    # Проверяем подключение к серверу
    if not wait_for_server():
        print(" Убедитесь, что сервер запущен на http://localhost:8000")
        sys.exit(1)
    
    try:
        # Инициализация переменных для хранения ID
        test_customer_id = None
        test_menu_item_id = None
        test_order_id = None
        test_order_item_id = None
        
        # 1. Проверка основного эндпоинта
        print("\n1. Проверка основного эндпоинта: GET /")
        response = requests.get(f"{BASE_URL}/")
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            print("   Успешно")
        print_json(response.json(), "   Ответ:")
        
        # 2. Проверка состояния базы данных
        print("\n2.  Проверка состояния базы данных: GET /database/health")
        response = requests.get(f"{BASE_URL}/database/health")
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   База данных: {health_data.get('status', 'unknown')}")
            print(f"   Тип БД: {health_data.get('database', 'unknown')}")
        else:
            print("   Ошибка:", response.text)
        
        # 3. Получение всех клиентов
        print("\n3. Получение всех клиентов: GET /customers")
        response = requests.get(f"{BASE_URL}/customers")
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            customers = response.json()
            print(f"   Найдено {len(customers)} клиентов:")
            for customer in customers[:3]:  # Показываем только первых 3
                print(f"      • {customer['id']}: {customer['name']} ({customer['phone']})")
            test_customer_id = customers[0]['id'] if customers else None
        else:
            print("   Ошибка:", response.text)
            return
        
        # 4. Получение всего меню
        print("\n4. Получение всего меню: GET /menu")
        response = requests.get(f"{BASE_URL}/menu")
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            menu_items = response.json()
            print(f"   Найдено {len(menu_items)} пунктов меню:")
            for item in menu_items[:3]:  # Показываем только первых 3
                print(f"      • {item['id']}: {item['name']} - {item['price']} руб.")
            test_menu_item_id = menu_items[0]['id'] if menu_items else None
        else:
            print("   Ошибка:", response.text)
            return
        
        # 5. Создание тестового клиента для операций удаления/обновления
        print("\n5. Создание тестового клиента: POST /customers")
        test_customer = {
            "name": "Тестовый Клиент",
            "phone": "+79998887766",
            "email": "test@example.com"
        }
        response = requests.post(f"{BASE_URL}/customers", json=test_customer)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 201:
            created_customer = response.json()
            print(f"   Тестовый клиент создан: ID {created_customer['id']}")
            test_customer_id = created_customer['id']  # Используем нового клиента для тестов
        else:
            print("   Ошибка:", response.text)
            # Используем существующего клиента
            print("    Использую существующего клиента")
        
        # 6. Обновление клиента
        if test_customer_id:
            print(f"\n6.  Обновление клиента: PATCH /customers/{test_customer_id}")
            update_data = {
                "phone": "+79991112233",
                "email": "updated@example.com"
            }
            response = requests.patch(f"{BASE_URL}/customers/{test_customer_id}", json=update_data)
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                updated_customer = response.json()
                print(f"   Клиент обновлен:")
                print(f"      • Телефон: {updated_customer['phone']}")
                print(f"      • Email: {updated_customer['email']}")
            else:
                print("   Ошибка:", response.text)
        
        # 7. Создание тестовой позиции меню
        print("\n7. Создание тестовой позиции меню: POST /menu")
        test_menu_item = {
            "name": "Тестовый Напиток",
            "category": "напиток",
            "price": 150.0,
            "is_available": True
        }
        response = requests.post(f"{BASE_URL}/menu", json=test_menu_item)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 201:
            created_menu_item = response.json()
            print(f"  Позиция меню создана: ID {created_menu_item['id']}")
            test_menu_item_id = created_menu_item['id']  # Используем новую позицию
        else:
            print("   Ошибка:", response.text)
        
        # 8. Обновление позиции меню
        if test_menu_item_id:
            print(f"\n8.  Обновление позиции меню: PATCH /menu/{test_menu_item_id}")
            menu_update = {
                "price": 170.0,
                "is_available": False
            }
            response = requests.patch(f"{BASE_URL}/menu/{test_menu_item_id}", json=menu_update)
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                updated_item = response.json()
                print(f" Позиция меню обновлена:")
                print(f"      • Новая цена: {updated_item['price']} руб.")
                print(f"      • Доступность: {'Да' if updated_item['is_available'] else 'Нет'}")
            else:
                print("  Ошибка:", response.text)
        
        # 9. Создание тестового заказа
        if test_customer_id:
            print("\n9. Создание тестового заказа: POST /orders")
            test_order = {
                "customer_id": test_customer_id,
                "total_amount": 300.0
            }
            response = requests.post(f"{BASE_URL}/orders", json=test_order)
            print(f"   Статус: {response.status_code}")
            if response.status_code == 201:
                created_order = response.json()
                print(f"  Заказ создан: ID {created_order['id']}")
                test_order_id = created_order['id']
            else:
                print("   Ошибка:", response.text)
        
        # 10. Добавление позиции в тестовый заказ
        if test_order_id and test_menu_item_id:
            print("\n10. Добавление позиции в заказ: POST /order-items")
            # Сначала вернем позицию в доступное состояние
            requests.patch(f"{BASE_URL}/menu/{test_menu_item_id}", json={"is_available": True})
            
            order_item = {
                "order_id": test_order_id,
                "menu_item_id": test_menu_item_id,
                "quantity": 1,
                "customizations": "Тестовая настройка"
            }
            response = requests.post(f"{BASE_URL}/order-items", json=order_item)
            print(f"   Статус: {response.status_code}")
            if response.status_code == 201:
                created_order_item = response.json()
                print(f"   Позиция добавлена в заказ: ID {created_order_item['id']}")
                test_order_item_id = created_order_item['id']
            else:
                print("   Ошибка:", response.text)
        
        # 11. Получение позиций конкретного заказа
        if test_order_id:
            print(f"\n11. Получение позиций заказа: GET /orders/{test_order_id}/items")
            response = requests.get(f"{BASE_URL}/orders/{test_order_id}/items")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                order_items = response.json()
                print(f"   Найдено {len(order_items.get('items', []))} позиций в заказе:")
                print(f"      • Общая сумма: {order_items.get('total_amount', 0)} руб.")
                for item in order_items.get('items', []):
                    print(f"      • {item['menu_item_name']}: {item['quantity']} x {item['price_per_item']} руб.")
            else:
                print("   Ошибка:", response.text)
        
        # 12. Получение заказов клиента
        if test_customer_id:
            print(f"\n12. Получение заказов клиента: GET /customers/{test_customer_id}/orders")
            response = requests.get(f"{BASE_URL}/customers/{test_customer_id}/orders")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                customer_orders = response.json()
                print(f"   Клиент {customer_orders.get('customer_name')} имеет {customer_orders.get('total_orders', 0)} заказов")
            else:
                print("   Ошибка:", response.text)
        
        # 13. Оплата заказа
        if test_order_id:
            print(f"\n13. Оплата заказа: PATCH /orders/{test_order_id}/pay")
            response = requests.patch(f"{BASE_URL}/orders/{test_order_id}/pay")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                paid_order = response.json()
                print(f"   Заказ оплачен:")
                print(f"      • Статус оплаты: {paid_order['payment_status']}")
                print(f"      • Статус заказа: {paid_order['status']}")
            else:
                print("   Ошибка:", response.text)
        
        # 14. Завершение заказа
        if test_order_id:
            print(f"\n14. Завершение заказа: PATCH /orders/{test_order_id}/complete")
            response = requests.patch(f"{BASE_URL}/orders/{test_order_id}/complete")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                completed_order = response.json()
                print(f"   Заказ завершен:")
                print(f"      • Статус: {completed_order['status']}")
                print(f"      • Время завершения: {completed_order.get('completed_at', 'не указано')}")
            else:
                print("   Ошибка:", response.text)
        
        # 15. Удаление позиции из заказа
        if test_order_item_id:
            print(f"\n15.  Удаление позиции из заказа: DELETE /order-items/{test_order_item_id}")
            response = requests.delete(f"{BASE_URL}/order-items/{test_order_item_id}")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                print(f"   Позиция заказа удалена")
                print_json(response.json(), "   Ответ:")
            else:
                print("   Ошибка:", response.text)
        
        # 16. Удаление тестового заказа
        if test_order_id:
            print(f"\n16.  Удаление заказа: DELETE /orders/{test_order_id}")
            response = requests.delete(f"{BASE_URL}/orders/{test_order_id}")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                print(f"   Заказ удален")
                print_json(response.json(), "   Ответ:")
            else:
                print("   Ошибка:", response.text)
        
        # 17. Удаление тестовой позиции меню
        if test_menu_item_id:
            print(f"\n17.  Удаление позиции меню: DELETE /menu/{test_menu_item_id}")
            response = requests.delete(f"{BASE_URL}/menu/{test_menu_item_id}")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                print(f"   Позиция меню удалена")
                print_json(response.json(), "   Ответ:")
            else:
                print("   Ошибка:", response.text)
                print("    Возможно, позиция используется в других заказах")
        
        # 18. Удаление тестового клиента
        if test_customer_id:
            print(f"\n18.  Удаление клиента: DELETE /customers/{test_customer_id}")
            response = requests.delete(f"{BASE_URL}/customers/{test_customer_id}")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                print(f"   Клиент удален")
                print_json(response.json(), "   Ответ:")
            else:
                print("   Ошибка:", response.text)
                print("    Возможно, у клиента есть не удаленные заказы")
        
        # 19. Тестирование обработки ошибок
        print("\n19.  Тестирование обработки ошибок")
        
        # Попытка удалить несуществующего клиента
        print("   DELETE /customers/999999:")
        response = requests.delete(f"{BASE_URL}/customers/999999")
        print(f"   Статус: {response.status_code} (ожидается 404)")
        
        # Попытка обновить несуществующую позицию меню
        print("   PATCH /menu/999999:")
        response = requests.patch(f"{BASE_URL}/menu/999999", json={"price": 100})
        print(f"   Статус: {response.status_code} (ожидается 404)")
        
        # Некорректные данные для обновления
        print("   PATCH /customers/1 с некорректными данными:")
        invalid_update = {
            "phone": "некорректный телефон"
        }
        response = requests.patch(f"{BASE_URL}/customers/1", json=invalid_update)
        print(f"   Статус: {response.status_code} (ожидается 422)")
        
        # Попытка создать заказ без обязательных полей
        print("   POST /orders без обязательных полей:")
        invalid_order = {
            "customer_id": 1
            # Нет total_amount
        }
        response = requests.post(f"{BASE_URL}/orders", json=invalid_order)
        print(f"   Статус: {response.status_code} (ожидается 422)")
        
        # 20. Финальная проверка состояния системы
        print("\n20. Финальная проверка состояния системы")
        
        # Получение всех клиентов
        response = requests.get(f"{BASE_URL}/customers")
        if response.status_code == 200:
            customers = response.json()
            print(f"   Всего клиентов в системе: {len(customers)}")
        
        # Получение всего меню
        response = requests.get(f"{BASE_URL}/menu")
        if response.status_code == 200:
            menu_items = response.json()
            print(f"   Всего позиций в меню: {len(menu_items)}")
        
        # Получение всех заказов
        response = requests.get(f"{BASE_URL}/orders")
        if response.status_code == 200:
            orders = response.json()
            print(f"   Всего заказов в системе: {len(orders)}")
            
            # Статистика по статусам заказов
            status_count = {}
            for order in orders:
                status = order.get('status', 'UNKNOWN')
                status_count[status] = status_count.get(status, 0) + 1
            
            print(f"   Статистика заказов:")
            for status, count in status_count.items():
                print(f"      • {status}: {count}")
        
        print("\n" + "=" * 70)
        print("ТЕСТИРОВАНИЕ УСПЕШНО ЗАВЕРШЕНО!")
        print("=" * 70)
        print("\nДля проверки всех эндпоинтов откройте:")
        print("   Документация API: http://localhost:8000/docs")
        print("\nПримеры команд для ручного тестирования:")
        print("   Удалить клиента:")
        print(f'   curl -X DELETE {BASE_URL}/customers/1')
        print("\n   Обновить клиента:")
        print(f'   curl -X PATCH {BASE_URL}/customers/1 \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"phone": "+79990001122"}\'')
        print("\n   Оплатить заказ:")
        print(f'   curl -X PATCH {BASE_URL}/orders/1/pay')
        print("\n   Завершить заказ:")
        print(f'   curl -X PATCH {BASE_URL}/orders/1/complete')
        print("\n   Получить позиции заказа:")
        print(f'   curl {BASE_URL}/orders/1/items')
        print("\n   Получить заказы клиента:")
        print(f'   curl {BASE_URL}/customers/1/orders')
        
    except requests.exceptions.RequestException as e:
        print(f"\nОшибка сети: {e}")
        print("⚠️  Убедитесь, что сервер запущен и доступен")
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()

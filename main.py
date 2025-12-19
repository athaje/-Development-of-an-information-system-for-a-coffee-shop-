# Импортируем необходимые библиотеки
from sqlmodel import SQLModel, Field, Session, select, create_engine
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn
import psycopg2
import sys

# ==================== НАСТРОЙКА БАЗЫ ДАННЫХ POSTGRESQL ====================
# Здесь указываем параметры для подключения к базе данных
# Эти настройки можно менять в зависимости от вашей системы
POSTGRES_CONFIG = {
    "user": "postgres",          # Имя пользователя базы данных
    "password": "password",      # Пароль пользователя
    "host": "localhost",         # Адрес сервера базы данных
    "port": "5432",              # Порт PostgreSQL
    "database": "coffee_shop_db" # Имя нашей базы данных
}

# Создаем строку для подключения к базе данных
# Формат: postgresql://пользователь:пароль@адрес:порт/база_данных
DATABASE_URL = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

# ==================== ОПРЕДЕЛЕНИЕ ТАБЛИЦ В БАЗЕ ДАННЫХ ====================

# Модель для таблицы "Клиенты"
class Customer(SQLModel, table=True):
    """Таблица для хранения информации о клиентах кофейни"""
    id: Optional[int] = Field(default=None, primary_key=True)  # Уникальный номер клиента
    name: str = Field(index=True)                              # Имя клиента
    phone: str = Field(index=True)                             # Телефон клиента
    email: Optional[str] = None                                # Email (может быть пустым)
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Дата создания записи

# Модель для таблицы "Позиции меню"
class MenuItem(SQLModel, table=True):
    """Таблица для хранения информации о блюдах и напитках в меню"""
    id: Optional[int] = Field(default=None, primary_key=True)  # Уникальный номер позиции
    name: str = Field(index=True)                              # Название позиции (например, "Капучино")
    category: str = Field(index=True)                          # Категория: "напиток" или "десерт"
    price: float                                               # Цена в рублях
    is_available: bool = True                                  # Доступна ли позиция для заказа
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Дата добавления в меню

# Модель для таблицы "Заказы"
class Order(SQLModel, table=True):
    """Таблица для хранения информации о заказах"""
    id: Optional[int] = Field(default=None, primary_key=True)  # Уникальный номер заказа
    customer_id: int = Field(foreign_key="customer.id", index=True)  # ID клиента, сделавшего заказ
    status: str = Field(default="CREATED", index=True)          # Статус заказа: CREATED, PAID, COMPLETED
    payment_status: str = Field(default="PENDING", index=True)  # Статус оплаты: PENDING, PAID
    total_amount: float                                         # Общая сумма заказа
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Дата создания заказа
    completed_at: Optional[datetime] = None                     # Дата завершения заказа (если завершен)

# Модель для таблицы "Позиции в заказе"
class OrderItem(SQLModel, table=True):
    """Таблица для хранения информации о том, что входит в заказ"""
    id: Optional[int] = Field(default=None, primary_key=True)  # Уникальный номер позиции в заказе
    order_id: int = Field(foreign_key="order.id", index=True)   # ID заказа, к которому относится позиция
    menu_item_id: int = Field(foreign_key="menuitem.id", index=True)  # ID позиции из меню
    quantity: int = 1                                           # Количество (сколько штук)
    customizations: Optional[str] = None                        # Особые пожелания (например, "без сахара")
    price: float                                                # Цена позиции на момент заказа

# ==================== ПОДГОТОВКА БАЗЫ ДАННЫХ ====================

def setup_postgresql_database():
    """
    Проверяет подключение к PostgreSQL и создает базу данных если она не существует
    Возвращает True если все успешно, False если есть ошибки
    """
    print("🔍 Проверяю подключение к PostgreSQL...")
    
    try:
        # Пробуем подключиться к серверу PostgreSQL
        conn = psycopg2.connect(
            user=POSTGRES_CONFIG["user"],
            password=POSTGRES_CONFIG["password"],
            host=POSTGRES_CONFIG["host"],
            port=POSTGRES_CONFIG["port"],
            database="postgres"  # Сначала подключаемся к стандартной базе данных
        )
        conn.autocommit = True  # Разрешаем автоматическое сохранение изменений
        cursor = conn.cursor()  # Создаем курсор для выполнения SQL команд
        
        # Проверяем, существует ли уже наша база данных
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_CONFIG['database']}'")
        exists = cursor.fetchone()  # Получаем результат запроса
        
        if not exists:
            # Если базы данных нет - создаем ее
            print(f"Создаю базу данных '{POSTGRES_CONFIG['database']}'...")
            cursor.execute(f"CREATE DATABASE {POSTGRES_CONFIG['database']}")
            print(f"База данных создана")
        else:
            print(f"База данных '{POSTGRES_CONFIG['database']}' уже существует")
        
        # Закрываем соединения
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        # Обрабатываем ошибки подключения
        print(f"Ошибка подключения: {e}")
        print("\nВозможные причины:")
        print(f"1. Неправильный пароль для пользователя '{POSTGRES_CONFIG['user']}'")
        print(f"2. PostgreSQL не запущен на {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
        print(f"3. Пользователь '{POSTGRES_CONFIG['user']}' не существует")
        return False
    except Exception as e:
        # Обрабатываем любые другие ошибки
        print(f"Ошибка: {e}")
        return False

def init_database():
    """
    Инициализирует базу данных: создает таблицы и добавляет тестовые данные
    Возвращает объект для подключения к базе данных (engine)
    """
    print("\n🔧 Инициализация базы данных...")
    
    # Проверяем и создаем базу данных
    if not setup_postgresql_database():
        print("\nНе могу подключиться к PostgreSQL!")
        print("Проверьте пароль и убедитесь, что PostgreSQL запущен.")
        sys.exit(1)  # Завершаем программу с ошибкой
    
    try:
        # Создаем движок для работы с базой данных
        engine = create_engine(DATABASE_URL, echo=True)  # echo=True включает вывод SQL запросов в консоль
        
        # Создаем все таблицы в базе данных
        SQLModel.metadata.create_all(engine)
        print("Таблицы созданы успешно")
        
        # Добавляем тестовые данные
        with Session(engine) as session:  # Открываем сессию для работы с базой данных
            # Проверяем, есть ли уже данные в таблице клиентов
            if not session.exec(select(Customer)).first():
                print("Добавляю тестовые данные...")
                
                # 1. Добавляем клиентов
                customers = [
                    Customer(name="Иван Иванов", phone="+79123456789", email="ivan@example.com"),
                    Customer(name="Мария Петрова", phone="+79161234567", email="maria@example.com"),
                    Customer(name="Алексей Сидоров", phone="+79031112233", email="alex@example.com"),
                ]
                
                for customer in customers:
                    session.add(customer)  # Добавляем клиента в сессию
                
                # 2. Добавляем позиции меню
                menu_items = [
                    MenuItem(name="Капучино", category="напиток", price=180.0),
                    MenuItem(name="Латте", category="напиток", price=190.0),
                    MenuItem(name="Эспрессо", category="напиток", price=120.0),
                    MenuItem(name="Американо", category="напиток", price=150.0),
                    MenuItem(name="Круассан", category="десерт", price=120.0),
                    MenuItem(name="Чизкейк", category="десерт", price=200.0),
                ]
                
                for item in menu_items:
                    session.add(item)  # Добавляем позицию меню в сессию
                
                session.commit()  # Сохраняем все изменения в базе данных
                
                # 3. Добавляем заказы (после коммита, чтобы получить ID клиентов и меню)
                all_customers = session.exec(select(Customer)).all()  # Получаем всех клиентов
                all_menu_items = session.exec(select(MenuItem)).all()  # Получаем все позиции меню
                
                if all_customers and all_menu_items:
                    # Заказ 1
                    order1 = Order(
                        customer_id=all_customers[0].id,
                        total_amount=360.0,
                        status="COMPLETED",
                        payment_status="PAID"
                    )
                    session.add(order1)
                    
                    # Заказ 2
                    order2 = Order(
                        customer_id=all_customers[1].id,
                        total_amount=310.0,
                        status="IN_PROGRESS",
                        payment_status="PAID"
                    )
                    session.add(order2)
                    
                    session.commit()  # Сохраняем заказы
                    
                    # Обновляем объекты заказов из базы данных (получаем их ID)
                    session.refresh(order1)
                    session.refresh(order2)
                    
                    # Добавляем позиции в заказы
                    order_item1 = OrderItem(
                        order_id=order1.id,
                        menu_item_id=all_menu_items[0].id,
                        quantity=2,
                        price=180.0 * 2
                    )
                    session.add(order_item1)
                    
                    order_item2 = OrderItem(
                        order_id=order2.id,
                        menu_item_id=all_menu_items[1].id,
                        quantity=1,
                        price=190.0
                    )
                    session.add(order_item2)
                    
                    order_item3 = OrderItem(
                        order_id=order2.id,
                        menu_item_id=all_menu_items[4].id,
                        quantity=1,
                        price=120.0
                    )
                    session.add(order_item3)
                    
                    session.commit()  # Сохраняем позиции заказов
                    
                    print("Тестовые данные добавлены:")
                    print(f"   - Клиентов: {len(customers)}")
                    print(f"   - Позиций меню: {len(menu_items)}")
                    print(f"   - Заказов: 2 с позициями")
            
        print("База данных готова к работе")
        return engine  # Возвращаем объект для подключения к базе данных
        
    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")
        raise  # Пробрасываем ошибку дальше

# ==================== СОЗДАНИЕ FASTAPI ПРИЛОЖЕНИЯ ====================

# Создаем основное приложение FastAPI
app = FastAPI(
    title="Кофейня API",  # Название API
    version="1.0",        # Версия API
    description="API для управления кофейней с использованием локального PostgreSQL"  # Описание
)

# ==================== МОДЕЛИ ДЛЯ ВХОДНЫХ ДАННЫХ API ====================
# Эти модели используются для проверки данных, которые приходят в API

# Модель для создания нового клиента
class CustomerCreate(BaseModel):
    name: str                     # Имя клиента (обязательное поле)
    phone: str                    # Телефон клиента (обязательное поле)
    email: Optional[str] = None   # Email клиента (необязательное поле)

# Модель для создания новой позиции в меню
class MenuItemCreate(BaseModel):
    name: str                     # Название позиции
    category: str                 # Категория
    price: float                  # Цена
    is_available: bool = True     # Доступность (по умолчанию доступна)

# Модель для создания нового заказа
class OrderCreate(BaseModel):
    customer_id: int              # ID клиента
    total_amount: float           # Общая сумма заказа

# Модель для добавления позиции в заказ
class OrderItemCreate(BaseModel):
    order_id: int                 # ID заказа
    menu_item_id: int             # ID позиции из меню
    quantity: int = 1             # Количество (по умолчанию 1)
    customizations: Optional[str] = None  # Особые пожелания

# ==================== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ====================

print("=" * 70)
print("ЛОКАЛЬНЫЙ POSTGRESQL")
print("=" * 70)

# Инициализируем базу данных при запуске приложения
engine = init_database()

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_session():
    """
    Функция для получения сессии работы с базой данных
    Используется в зависимости для каждого эндпоинта API
    """
    with Session(engine) as session:
        yield session  # Возвращаем сессию для использования

# ==================== API ЭНДПОИНТЫ (КОНЕЧНЫЕ ТОЧКИ) ====================

@app.get("/")
def read_root():
    """
    Корневой эндпоинт API
    Возвращает информацию о доступных эндпоинтах
    """
    return {
        "message": "Добро пожаловать в API кофейни!",
        "database": "Локальный PostgreSQL",
        "endpoints": {
            "customers": "/customers",    # Эндпоинт для работы с клиентами
            "menu": "/menu",              # Эндпоинт для работы с меню
            "orders": "/orders",          # Эндпоинт для работы с заказами
            "docs": "/docs"               # Автоматическая документация API
        }
    }

@app.get("/customers", response_model=List[Customer])
def get_customers(session: Session = Depends(get_session)):
    """
    Получить список всех клиентов
    GET запрос на /customers
    """
    return session.exec(select(Customer)).all()  # Выполняем SQL запрос и возвращаем всех клиентов

@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int, session: Session = Depends(get_session)):
    """
    Получить информацию о конкретном клиенте по его ID
    GET запрос на /customers/{id}
    """
    customer = session.get(Customer, customer_id)  # Ищем клиента по ID
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")  # Если клиент не найден - ошибка 404
    return customer

@app.post("/customers", response_model=Customer, status_code=201)
def create_customer(customer: CustomerCreate, session: Session = Depends(get_session)):
    """
    Создать нового клиента
    POST запрос на /customers с данными клиента в теле запроса
    """
    new_customer = Customer(**customer.dict())  # Создаем объект клиента из полученных данных
    session.add(new_customer)                   # Добавляем клиента в сессию
    session.commit()                            # Сохраняем изменения в базе данных
    session.refresh(new_customer)               # Обновляем объект из базы данных (получаем ID)
    return new_customer

@app.get("/menu", response_model=List[MenuItem])
def get_menu(session: Session = Depends(get_session)):
    """
    Получить все позиции меню
    GET запрос на /menu
    """
    return session.exec(select(MenuItem)).all()

@app.get("/menu/available", response_model=List[MenuItem])
def get_available_menu(session: Session = Depends(get_session)):
    """
    Получить только доступные позиции меню
    GET запрос на /menu/available
    """
    return session.exec(select(MenuItem).where(MenuItem.is_available == True)).all()

@app.get("/menu/{category}", response_model=List[MenuItem])
def get_menu_by_category(category: str, session: Session = Depends(get_session)):
    """
    Получить позиции меню по категории
    GET запрос на /menu/{категория}
    """
    return session.exec(
        select(MenuItem).where(
            MenuItem.category == category,
            MenuItem.is_available == True
        )
    ).all()

@app.get("/orders", response_model=List[Order])
def get_orders(session: Session = Depends(get_session)):
    """
    Получить все заказы
    GET запрос на /orders
    """
    return session.exec(select(Order)).all()

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int, session: Session = Depends(get_session)):
    """
    Получить информацию о конкретном заказе по его ID
    GET запрос на /orders/{id}
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order

@app.post("/orders", response_model=Order, status_code=201)
def create_order(order: OrderCreate, session: Session = Depends(get_session)):
    """
    Создать новый заказ
    POST запрос на /orders с данными заказа в теле запроса
    """
    # Проверяем существование клиента
    customer = session.get(Customer, order.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    new_order = Order(**order.dict())  # Создаем объект заказа
    session.add(new_order)             # Добавляем заказ в сессию
    session.commit()                   # Сохраняем изменения
    session.refresh(new_order)         # Обновляем объект из базы данных
    return new_order

@app.post("/order-items", response_model=OrderItem, status_code=201)
def add_order_item(item: OrderItemCreate, session: Session = Depends(get_session)):
    """
    Добавить позицию в существующий заказ
    POST запрос на /order-items с данными позиции в теле запроса
    """
    # Проверяем существование заказа
    order = session.get(Order, item.order_id)
    menu_item = session.get(MenuItem, item.menu_item_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if not menu_item:
        raise HTTPException(status_code=404, detail="Позиция меню не найдена")
    
    # Проверяем, доступна ли позиция меню
    if not menu_item.is_available:
        raise HTTPException(status_code=400, detail="Позиция меню недоступна")
    
    # Рассчитываем цену позиции (цена из меню × количество)
    price = menu_item.price * item.quantity
    
    # Создаем новую позицию в заказе
    new_order_item = OrderItem(
        order_id=item.order_id,
        menu_item_id=item.menu_item_id,
        quantity=item.quantity,
        price=price,
        customizations=item.customizations
    )
    
    session.add(new_order_item)        # Добавляем позицию в сессию
    session.commit()                   # Сохраняем изменения
    session.refresh(new_order_item)    # Обновляем объект из базы данных
    
    # Обновляем общую сумму заказа
    # Получаем все позиции этого заказа
    order_items = session.exec(select(OrderItem).where(OrderItem.order_id == item.order_id)).all()
    # Суммируем цены всех позиций
    order.total_amount = sum(item.price for item in order_items)
    session.add(order)                 # Добавляем обновленный заказ в сессию
    session.commit()                   # Сохраняем изменения
    session.refresh(order)             # Обновляем заказ из базы данных
    
    # Еще раз обновляем позицию заказа (на всякий случай)
    session.refresh(new_order_item)
    
    return new_order_item

@app.get("/database/health")
def database_health(session: Session = Depends(get_session)):
    """
    Проверка состояния базы данных
    GET запрос на /database/health
    Возвращает информацию о состоянии подключения к базе данных
    """
    try:
        # Пробуем выполнить простой запрос к базе данных
        session.exec(select(1))  # Простой запрос: "выбрать 1"
        return {
            "status": "healthy",        # Статус: работает
            "database": "PostgreSQL",   # Тип базы данных
            "connection": "success",    # Подключение: успешно
            "timestamp": datetime.utcnow().isoformat()  # Время проверки
        }
    except Exception as e:
        # Если произошла ошибка - возвращаем ошибку 500
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == "__main__":
    """
    Точка входа в программу
    Этот код выполняется при запуске файла напрямую
    """
    print("\n" + "=" * 70)
    print("FASTAPI СЕРВЕР ЗАПУЩЕН!")
    print("=" * 70)
    print("Полная документация API: http://localhost:8000/docs")
    print("Получить всех клиентов: GET /customers")
    print("Получить меню: GET /menu")
    print("Получить заказы: GET /orders")
    print("Проверить БД: GET /database/health")
    print("\nПримеры тестирования API:")
    print("1. curl http://localhost:8000/customers")
    print("2. curl http://localhost:8000/menu")
    print("3. curl -X POST http://localhost:8000/customers \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"name": "Новый Клиент", "phone": "+79001112233"}\'')
    print("\nДля остановки сервера нажмите Ctrl+C")
    print("=" * 70)
    
    # Запускаем веб-сервер
    # host="0.0.0.0" - слушаем все сетевые интерфейсы
    # port=8000 - используем порт 8000
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

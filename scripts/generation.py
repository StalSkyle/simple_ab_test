'''
Скрипт генерирует реалистичный массив данных подписочного мобильного приложения за 6 месяцев и распределяет его по 4 связным таблицам:  

1. Таблица users (Профиль пользователя)  
    Что попадает: Данные сессии установки приложения.  
    Данные: Уникальный user_id, дата и время установки (install_date), рекламный канал (channel), платформа (device) и страна (country).  
    Объем: 12 000 пользователей.  
2. Таблица ab_experiments (Сплитование A/B-теста)  
    Что попадает: Назначенная группа в эксперименте с новым экраном подписки.  
    Данные: user_id, название теста (paywall_discount_v1) и группа (A — текущий экран, B — экран со скидкой).  
    Объем: 12 000 записей (по 1 строке на каждого пользователя).  
3. Таблица events (Логи активности и продуктовая воронка)  
    Что попадает: Все действия пользователей в приложении — от первого клика до повторных заходов.  
    Данные: user_id, тип события (app_first_launch, onboarding_complete, paywall_view, subscription_purchase, session_start) и event_timestamp.  
    Объем: ~50 000+ событий.  
4. Таблица orders (Транзакции и выручка)  
    Что попадает: Все попытки оплаты — как первичные покупки подписок, так и их рекуррентные автопродления.  
    Данные: user_id, сумма (amount: $4.99, $14.99 или $49.99), статус (status: completed/failed) и order_timestamp.  
    Объем: ~2 000+ транзакций.  
'''

import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "product_analytics"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

np.random.seed(42)
random.seed(42)

print("Запуск генерации синтетических данных...")

NUM_USERS = 12000
START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2026, 3, 1)
TOTAL_DAYS = (END_DATE - START_DATE).days

# генерация пользователей (users)
channels = ['Google Ads', 'Yandex Direct', 'Organic', 'Apple Search Ads', 'Influencers']
channel_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
devices = ['iOS', 'Android']
device_weights = [0.35, 0.65]
countries = ['RU', 'US', 'DE', 'GB', 'KZ']
country_weights = [0.50, 0.20, 0.10, 0.10, 0.10]

users_list = []
user_ids = []

for i in range(NUM_USERS):
    u_id = str(uuid.uuid4())
    user_ids.append(u_id)
    
    random_day_offset = int(np.random.beta(a=2, b=1.5) * TOTAL_DAYS)
    install_dt = START_DATE + timedelta(days=random_day_offset, 
                                          hours=random.randint(0, 23), 
                                          minutes=random.randint(0, 59))
    
    users_list.append({
        'user_id': u_id,
        'install_date': install_dt,
        'channel': np.random.choice(channels, p=channel_weights),
        'device': np.random.choice(devices, p=device_weights),
        'country': np.random.choice(countries, p=country_weights)
    })

df_users = pd.DataFrame(users_list)
print(f"Сгенерировано {len(df_users)} пользователей.")

# генерация a/b эксперимента (ab_experiments)
ab_list = []
for u_id in user_ids:
    group = np.random.choice(['A', 'B'], p=[0.5, 0.5])
    ab_list.append({
        'user_id': u_id,
        'experiment_name': 'paywall_discount_v1',
        'group_id': group
    })

df_ab = pd.DataFrame(ab_list)

# генерация событий и транзакций (events & orders)
events_list = []
orders_list = []
ab_lookup = df_ab.set_index('user_id')['group_id'].to_dict()

for idx, user in df_users.iterrows():
    u_id = user['user_id']
    inst_dt = user['install_date']
    group = ab_lookup[u_id]
    
    events_list.append({'user_id': u_id, 'event_name': 'app_first_launch', 'event_timestamp': inst_dt})
    
    if random.random() < 0.80:
        dt_onb = inst_dt + timedelta(seconds=random.randint(30, 300))
        events_list.append({'user_id': u_id, 'event_name': 'onboarding_complete', 'event_timestamp': dt_onb})
        
        if random.random() < 0.85:
            dt_pw = dt_onb + timedelta(seconds=random.randint(10, 60))
            events_list.append({'user_id': u_id, 'event_name': 'paywall_view', 'event_timestamp': dt_pw})
            
            p_purchase = 0.125 if group == 'B' else 0.100
            
            if random.random() < p_purchase:
                dt_purchase = dt_pw + timedelta(seconds=random.randint(5, 120))
                events_list.append({'user_id': u_id, 'event_name': 'subscription_purchase', 'event_timestamp': dt_purchase})
                
                plan = np.random.choice(['weekly', 'monthly', 'annual'], p=[0.5, 0.35, 0.15])
                amounts = {'weekly': 4.99, 'monthly': 14.99, 'annual': 49.99}
                status = np.random.choice(['completed', 'failed'], p=[0.95, 0.05])
                
                orders_list.append({
                    'user_id': u_id,
                    'amount': amounts[plan],
                    'status': status,
                    'order_timestamp': dt_purchase
                })
                
                if status == 'completed':
                    if plan == 'weekly' and random.random() < 0.6:
                        orders_list.append({'user_id': u_id, 'amount': 4.99, 'status': 'completed', 'order_timestamp': dt_purchase + timedelta(days=7)})
                    elif plan == 'monthly' and random.random() < 0.7:
                        orders_list.append({'user_id': u_id, 'amount': 14.99, 'status': 'completed', 'order_timestamp': dt_purchase + timedelta(days=30)})

    num_sessions = int(np.random.exponential(scale=3))
    for _ in range(num_sessions):
        days_after = int(np.random.exponential(scale=12)) + 1
        if days_after > 180:
            continue
        session_dt = inst_dt + timedelta(days=days_after, hours=random.randint(0,23), minutes=random.randint(0,59))
        if session_dt <= END_DATE:
            events_list.append({'user_id': u_id, 'event_name': 'session_start', 'event_timestamp': session_dt})

df_events = pd.DataFrame(events_list)
df_orders = pd.DataFrame(orders_list)

# вставка в postgres
try:
    engine = create_engine(DATABASE_URL)
    print("\nЗагрузка данных в PostgreSQL...")
    
    df_users.to_sql('users', engine, if_exists='append', index=False, chunksize=1000)
    df_ab.to_sql('ab_experiments', engine, if_exists='append', index=False, chunksize=1000)
    df_events.to_sql('events', engine, if_exists='append', index=False, chunksize=2000)
    df_orders.to_sql('orders', engine, if_exists='append', index=False, chunksize=1000)

except Exception as e:
    print(f"\n Ошибка: {e}")
-- таблица пользователей
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    install_date TIMESTAMP NOT NULL,
    channel VARCHAR(50) NOT NULL,
    device VARCHAR(50) NOT NULL,
    country VARCHAR(10) NOT NULL
);

-- таблица событий приложения
CREATE TABLE events (
    event_id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    event_name VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL
);

-- таблица транзакций и подписок
CREATE TABLE orders (
    order_id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    order_timestamp TIMESTAMP NOT NULL
);

-- таблица сплитования пользователей в A/B тесте
CREATE TABLE ab_experiments (
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    experiment_name VARCHAR(50) NOT NULL,
    group_id VARCHAR(10) NOT NULL,
    PRIMARY KEY (user_id, experiment_name)
);
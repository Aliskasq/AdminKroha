# AdminKroha - Enhanced Telegram Bot for Binance Square

## 🚀 Welcome to AdminKroha

**AdminKroha — это продвинутый Telegram-бот для публикации контента в Binance Square.** Поддерживает круглосуточную работу через systemd, улучшенное виртуальное окружение и расширенную систему напоминаний.

![Bot Logo](https://github.com/Aliskasq/AdminKroha/blob/main/docs/logo.png?raw=true)

## 📋 Обзор

AdminKroha — это бот нового поколения, позволяющий пользователям публиковать контент в Binance Square через команды Telegram. Особенности:

- **🔒 Работа только в группах** — бот отвечает только в групповых чатах и супергруппах
- **👮 Права администратора** — команды доступны только администраторам группы
- **📝 Публикация постов** — текст, изображения, опросы с тикерами
- **🔔 Система напоминаний** — гибкое расписание по времени и дням недели
- **📊 Данные тикеров** — реальные курсы криптовалют
- **⏰ Планировщик постов** — отложенная публикация
- **🛡️ Production-ready** — systemd, логирование, лимиты ресурсов
- **🇷🇺 Полностью на русском языке**

## ✨ Основные функции

### 🔒 Безопасность
- **Только группы**: бот работает только в групповых чатах и супергруппах
- **Только админы**: команды доступны только администраторам группы
- **Контроль доступа**: проверка прав через Telegram API

### 🔔 Система напоминаний
- **Типы**: задача, рынок, анализ, новости, общее
- **Время**: формат ЧЧ:ММ (24-часовой)
- **Дни недели**: 0=Понедельник ... 6=Воскресенье (например: "0,2,4" = Пн/Ср/Пт)
- **Управление**: добавление, список, удаление, обновление, принудительный запуск

### 🛠️ Production развёртывание
- **Python 3.11+** виртуальное окружение
- **Systemd сервис** для 24/7 работы
- **Автоперезапуск** при ошибках
- **Логирование** в journald
- **Ограничение ресурсов** (CPU, память, файловые дескрипторы)

## 📱 Команды Telegram

### Базовые
| Команда | Описание | Пример |
|---------|----------|--------|
| `/start` | Запуск бота и справка | `/start` |
| `/help` | Показать все команды | `/help` |
| `/status` | Статус бота и статистика | `/status` |

### Публикация контента
| Команда | Описание | Пример |
|---------|----------|--------|
| `/post <текст>` | Опубликовать текст в Binance Square | `/post BTC пробивает уровень #crypto #trading` |
| `/post_image <текст>` | Опубликовать с изображением | `/post_image Анализ рынка` (потом отправьте фото) |
| `/get_tickers <тики>` | Получить данные тикеров | `/get_tickers BTCUSDT ETHUSDT SOLUSDT` |
| `/poll <вопрос> <варианты>` | Создать опрос | `/poll Куда пойдёт BTC? Вверх Вниз Бок` |
| `/schedule <время> <текст>` | Запланировать пост | `/schedule 14:30 Анализ на завтра` |
| `/scheldue <время> <детали>` | Расширенное планирование | `/scheldue 14:30 "Вопрос?" Да Нет $btc #crypto` |

### Напоминания
| Команда | Описание | Пример |
|---------|----------|--------|
| `/add_reminder <тип> <время> [дни] [сообщение]` | Добавить напоминание | `/add_reminder task 09:00 Проверить задачи` |
| `/list_reminders` | Список напоминаний | `/list_reminders` |
| `/remove_reminder <id>` | Удалить напоминание | `/remove_reminder rem_123` |
| `/update_reminder <id> <поле> <значение>` | Обновить напоминание | `/update_reminder rem_123 time 10:00` |
| `/trigger_reminder <id>` | Запустить немедленно | `/trigger_reminder rem_123` |

**Типы напоминаний:** `task`, `market`, `analysis`, `news`, `general`

**Примеры дней:** `0,2,4` (Пн/Ср/Пт), `5,6` (Сб/Вс), пусто = каждый день

## 🛠️ Установка и запуск

### Требования
- **Python 3.11+** (рекомендуется для production)
- **Linux** с systemd (для 24/7 работы)
- **python3-venv** пакет
- **Git**

### Способ 1: Автоматическая установка (рекомендуется)

```bash
# Клонировать репозиторий
git clone https://github.com/Aliskasq/AdminKroha.git
cd AdminKroha

# Запустить установщик
python3 install.py

# Следовать инструкциям:
# • Настройка Python 3.11+ venv
# • Конфигурация systemd сервиса
# • Настройка переменных окружения
```

### Способ 2: Ручная установка

```bash
# 1. Клонировать
git clone https://github.com/Aliskasq/AdminKroha.git
cd AdminKroha

# 2. Проверить Python
python3 --version  # должен быть 3.11+

# 3. Создать виртуальное окружение
python3 -m venv venv_production
source venv_production/bin/activate

# 4. Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt

# 5. Настроить .env
cp configs/.env.example .env
# Отредактируйте .env с вашими ключами (см. ниже)

# 6. Создать директории
mkdir -p logs data configs systemd docs tests backups cache
```

### Настройка .env (обязательно!)

```bash
# Telegram Bot Token (от @BotFather)
BOT_TOKEN=ваш_токен_бота

# ID группы (получите через @userinfobot после добавления бота в группу)
# Формат: -1001234567890
TELEGRAM_GROUP_ID=-100xxxxxxxxxx

# Binance Square API Key (один ключ для постов)
BINANCE_API_KEY=ваш_ключ_binance

# Опционально: ID админа (для некоторых функций)
ADMIN_USER_ID=123456789

# Настройки бота
LOG_LEVEL=INFO
MAX_POST_LENGTH=1000
RATE_LIMIT=60
ENABLE_SCHEDULED_POSTS=true
ENABLE_AUTO_REPLIES=true
ALLOWED_HASHTAGS=#crypto,#btc,#eth,#trading,#binance,#square
DEFAULT_POST_TYPE=text
```

### Настройка Systemd (для production)

```bash
# Скопировать сервис
sudo cp systemd/admin-kroha.service /etc/systemd/system/

# ВАЖНО: Отредактировать пути в сервисе под ваш сервер!
# WorkingDirectory=/путь/к/AdminKroha
# ExecStart=/путь/к/venv_production/bin/python main.py
# User=ваш_пользователь

# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозапуск и стартовать
sudo systemctl enable admin-kroha
sudo systemctl start admin-kroha

# Проверить статус
sudo systemctl status admin-kroha

# Логи
sudo journalctl -u admin-kroha -f
```

## 🚀 Быстрый старт

### Разработка
```bash
source venv_production/bin/activate
python3 main.py
```

### Production
```bash
sudo systemctl start admin-kroha
sudo systemctl status admin-kroha
sudo journalctl -u admin-kroha -f
```

## ⚠️ Важно: Доступ к группе

**Бот работает ТОЛЬКО в групповых чатах!**

1. **Добавьте бота в вашу Telegram группу**
2. **Сделайте бота администратором** (для получения списка админов)
3. **Узнайте ID группы**: перешлите сообщение из группы боту @userinfobot
4. **Вставьте ID в .env**: `TELEGRAM_GROUP_ID=-100xxxxxxxxxx`

❌ Бот **НЕ** отвечает в личных сообщениях
✅ Команды работают **ТОЛЬКО для администраторов группы**

## 🔔 Система напоминаний — подробнее

### Добавление напоминания
```
/add_reminder <тип> <время> [дни] [сообщение]
```

**Параметры:**
- `<тип>`: `task`, `market`, `analysis`, `news`, `general`
- `<время>`: ЧЧ:ММ (24ч), например `09:00`, `14:30`
- `[дни]`: дни недели через запятую (0=Пн, 6=Вс), например `0,2,4` или `5,6`
- `[сообщение]`: текст напоминания

**Примеры:**
```
/add_reminder task 09:00 Ежедневные задачи
/add_reminder market 14:30 Проверка BTC #crypto 0,2,4
/add_reminder analysis 19:00 Вечерний анализ
/add_reminder news 08:00 Утренние новости
/add_reminder general 17:00 Командный стендап
```

### Управление
- `/list_reminders` — показать все ваши напоминания
- `/remove_reminder rem_123` — удалить по ID
- `/update_reminder rem_123 time 10:00` — изменить время
- `/update_reminder rem_123 days 1,3,5` — изменить дни
- `/update_reminder rem_123 message Новый текст` — изменить сообщение
- `/trigger_reminder rem_123` — выполнить прямо сейчас

## 📁 Структура проекта

```
AdminKroha/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Основная логика бота + напоминания
│   ├── config.py           # Конфигурация (dataclass Config)
│   ├── binance_api.py      # Binance Square API
│   ├── content_generator.py # Генерация контента
│   ├── image_handler.py    # Обработка изображений
│   ├── scheduler.py        # Планировщик постов
│   ├── logger.py           # Логирование
│   └── reminder.py         # Система напоминаний
├── configs/
│   └── .env.example        # Пример конфигурации
├── systemd/
│   └── admin-kroha.service # Systemd сервис
├── logs/                   # Логи (авто)
├── data/                   # Данные
├── docs/                   # Документация
├── tests/                  # Тесты
├── backups/                # Бэкапы
├── cache/                  # Кэш
├── install.py              # Установщик
├── main.py                 # Точка входа
├── requirements.txt        # Зависимости
└── README.md               # Этот файл
```

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | Обязательна |
|------------|----------|-------------|
| `BOT_TOKEN` | Токен бота от @BotFather | Да |
| `TELEGRAM_GROUP_ID` | ID группы (формат -100...) | Да |
| `BINANCE_API_KEY` | API ключ Binance Square | Да |
| `ADMIN_USER_ID` | ID админа (опционально) | Нет |
| `LOG_LEVEL` | Уровень логов (DEBUG/INFO/WARNING/ERROR) | Нет |
| `MAX_POST_LENGTH` | Макс. длина поста | Нет |
| `RATE_LIMIT` | Лимит запросов/мин | Нет |

### Настройка бота

Редактируйте `src/config.py` для изменения поведения:

```python
@dataclass
class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    TELEGRAM_GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    MAX_POST_LENGTH = int(os.getenv('MAX_POST_LENGTH', '1000'))
    RATE_LIMIT = int(os.getenv('RATE_LIMIT', '60'))
```

## 📊 API интеграции

### Binance Square OpenAPI
- **Текстовый пост**: `POST https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add`
  - Headers: `X-Square-OpenAPI-Key`, `clienttype: binanceSkill`
  - Body: `{"contentType": 1, "bodyTextOnly": "text"}`
- **Изображение (4 шага)**:
  1. `POST https://www.binance.com/bapi/composite/v2/public/pgc/openApi/image/presignedUrl`
  2. `PUT` к presigned URL с бинарными данными изображения
  3. `POST https://www.binance.com/bapi/composite/v2/public/pgc/openApi/image/imageStatus` (polling)
  4. `POST content/add` с `imageList`
- **Тикеры**: `GET https://api.binance.com/api/v3/ticker/24hr` (публичный)

> ⚠️ **Важно**: Не пишите API запросы вручную для обычного постинга. Используйте официальные скрипты Binance Skills Hub. Бот использует правильные эндпоинты согласно официальной документации.

### Telegram Bot API
- Long polling через python-telegram-bot
- Проверка админов через `getChatMember`

## 🐛 Устранение проблем

### Бот не отвечает
```bash
# 1. Проверить статус
sudo systemctl status admin-kroha

# 2. Логи
sudo journalctl -u admin-kroha --since "1 hour ago"

# 3. Перезапуск
sudo systemctl restart admin-kroha
```

### Неверные API ключи
- Проверьте токен в @BotFather
- Проверьте Binance API ключ на платформе Binance Square

### Ошибки прав доступа
- Бот должен быть в группе
- Пользователь должен быть админом группы
- Проверьте `TELEGRAM_GROUP_ID` в .env

### Отладка
```bash
export LOG_LEVEL=DEBUG
python3 main.py
```

## 📚 Документация

- `docs/` — подробная API документация
- `src/config.py` — опции конфигурации
- `CONTRIBUTING.md` — гайд по разработке

## 🆘 Поддержка

- **Issues**: https://github.com/Aliskasq/AdminKroha/issues
- **Discussions**: https://github.com/Aliskasq/AdminKroha/discussions
- **GitHub**: @AdminKroha

## 📖 Лицензия

MIT License. См. `LICENSE`.

## 🌟 Авторы

- Binance Square API — социальные посты
- Telegram Bot API — платформа
- Python Community — экосистема
- Open Source Contributors

## 🚀 Roadmap

1. **Расширенная аналитика** — детальная рыночная аналитика
2. **Мультиязычность** — поддержка языков
3. **Умное планирование** — на основе рыночных условий
4. **Real-time данные** — стриминг цен
5. **Web интерфейс** — админка для управления
6. **Mobile app** — управление с телефона

## 🔄 Changelog

### v2.1.1 (Current)
- ✅ Исправлены Binance Square API эндпоинты (www.binance.com/bapi/composite)
- ✅ Правильный формат запросов: contentType=1, bodyTextOnly
- ✅ 4-шаговая загрузка изображений (presigned URL → PUT → poll → post)
- ✅ Сохранение пользовательского контента без изменений (хэштеги/каштэги парсит бэкенд Binance)
- ✅ Убраны лишние теги, таймстампы и префикс "Tags:" в ответе
- ✅ Правильные ссылки на посты через shareLink API

### v2.1.0
- ✅ Бот полностью на русском языке
- ✅ Команды для всех админов группы (не только хардкодного)
- ✅ Ссылка на пост после публикации
- ✅ Исправлен config.py, добавлен aiohttp
- ✅ Обновлена документация

### v2.0.0
- Systemd интеграция для 24/7
- Python 3.11+ venv
- Расширенные напоминания
- Security hardening

### v1.0.0
- Базовая функциональность
- Публикация контента
- Тикеры и опросы

---

**AdminKroha v2.1.0** — готов к production! 🌟

*GitHub: https://github.com/Aliskasq/AdminKroha*
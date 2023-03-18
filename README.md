# quiz_bot
Два бота для проведения викторин - для telegram и vk.  

## Как настроить

Для запуска ботов вам понадобится Python третьей версии.  

Создайте файл .env с переменными окружения  

Затем установите зависимости

```sh
pip install -r requirements.txt
```

## Переменные окружения

Часть настроек проекта берётся из переменных окружения. Чтобы их определить, создайте файл `.env` рядом в корне проекта и запишите туда данные в таком формате: `ПЕРЕМЕННАЯ=значение`.

Доступны переменные:
- `TG_TOKEN` — token телеграмм бота (получается у @BotFather при регистрации бота).  
- `VK_TOKEN` - token vk бота (получается при создании группы в vk)  

## Telegram бот

![Alt text](https://github.com/lexashvetsoff/supportVerbGame/blob/main/screen/demo_tg_bot.gif)  
[Пример рабочего бота](https://t.me/quiz_questionsBot)

### Запуск

```sh
python3 tg_quiz_bot.py
```

## Vk бот

![Alt text](https://github.com/lexashvetsoff/supportVerbGame/blob/main/screen/demo_vk_bot.gif)  
Пример работы можно посмотреть написав в [группу в vk](https://vk.com/public219165908)

### Запуск

```sh
python3 vk_quiz_bot.py
```

## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
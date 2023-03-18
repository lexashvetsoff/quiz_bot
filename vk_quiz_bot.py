import os
import random
from dotenv import load_dotenv

from questions import union_questions

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import redis


_right = 5
_loss = 1
_win = 20


def get_start_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Начать', color=VkKeyboardColor.PRIMARY)
    return keyboard


def get_start_quiz_questions_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    return keyboard


def get_custom_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Закончить игру', color=VkKeyboardColor.SECONDARY)
    return keyboard


def get_keyboard():
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Белая кнопка', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Зелёная кнопка', color=VkKeyboardColor.POSITIVE)

    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Красная кнопка', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Синяя кнопка', color=VkKeyboardColor.PRIMARY)

    return keyboard


def echo(event, vk_api):
    keyboard = get_start_keyboard()
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard.get_keyboard(),
        message=event.text,
        random_id=random.randint(1, 1000)
    )


def start(event, vk_api, db_redis) -> None:
    """Send a message when the command /start is issued."""
    if db_redis.hget(f'user_{event.user_id}', event.user_id):
        db_redis.hdel(f'user_{event.user_id}', event.user_id)
    
    db_redis.hset(f'user_{event.user_id}', 'score', 0)

    keyboard = get_start_keyboard()
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard.get_keyboard(),
        message='Привет! Я бот для викторин!',
        random_id=random.randint(1, 1000)
    )


def handle_new_question_request(event, vk_api, db_redis, quiz_questions):
    print('hendler: handle_new_question_request')
    question = random.choice(list(quiz_questions))
    db_redis.hset(f'user_{event.user_id}', event.user_id, question)
    print(quiz_questions[db_redis.hget(f'user_{event.user_id}', event.user_id)])
    keyboard = get_custom_keyboard()
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard.get_keyboard(),
        message=question,
        random_id=random.randint(1, 1000)
    )


def start_quiz_questions(vk_api, event, db_redis):
    keyboard = get_start_quiz_questions_keyboard()
    message_text = 'Чтобы начать игру нажми на кнопку'
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard.get_keyboard(),
        message=message_text,
        random_id=random.randint(1, 1000)
    )


def handle_solution_attempt(event, vk_api, db_redis, quiz_questions):
    reseived_message = event.text
    # Новый вопрос
    if reseived_message == 'Новый вопрос':
        return handle_new_question_request(event, vk_api, db_redis, quiz_questions)
    # Сдаться
    elif reseived_message == 'Сдаться':
        score = int(db_redis.hget(f'user_{event.user_id}', 'score'))
        score -= _loss
        db_redis.hset(f'user_{event.user_id}', 'score', score)
        answer = quiz_questions[db_redis.hget(f'user_{event.user_id}', event.user_id)]
        vk_api.messages.send(
            user_id=event.user_id,
            message=f'Правильный ответ: {answer}',
            random_id=random.randint(1, 1000)
        )
        return handle_new_question_request(event, vk_api, db_redis, quiz_questions)
    # Мой счет
    elif reseived_message == 'Мой счет':
        score = db_redis.hget(f'user_{event.user_id}', 'score')
        message_text = f'Ваш счет: {score}'
        vk_api.messages.send(
            user_id=event.user_id,
            message=message_text,
            random_id=random.randint(1, 1000)
        )
        return handle_new_question_request(event, vk_api, db_redis, quiz_questions)
    # Закончить игру
    elif reseived_message == 'Закончить игру':
        end_game(event, vk_api, db_redis)
    else:
        return check_answer(event, vk_api, db_redis, quiz_questions)


def check_answer(event, vk_api, db_redis, quiz_questions):
    print('hendler: check_answer')
    if db_redis.hget(f'user_{event.user_id}', event.user_id):
        print(quiz_questions[db_redis.hget(f'user_{event.user_id}', event.user_id)])
        answer = quiz_questions[db_redis.hget(f'user_{event.user_id}', event.user_id)]
        user_say = event.text
        if user_say.lower() in answer.lower():
            score = int(db_redis.hget(f'user_{event.user_id}', 'score'))
            score += _right
            db_redis.hset(f'user_{event.user_id}', 'score', score)
            vk_api.messages.send(
                user_id=event.user_id,
                message='Правильно! Поздравляю!',
                random_id=random.randint(1, 1000)
            )
            if int(db_redis.hget(f'user_{event.user_id}', 'score')) >= _win:
                return win_game(event, vk_api, db_redis)
            return handle_new_question_request(event, vk_api, db_redis, quiz_questions)
        else:
            keyboard = get_custom_keyboard()
            vk_api.messages.send(
                user_id=event.user_id,
                keyboard=keyboard.get_keyboard(),
                message='Неправильно… Попробуешь ещё раз?',
                random_id=random.randint(1, 1000)
            )


def end_game(event, vk_api, db_redis):
    print('hendler: end_game')
    if db_redis.hget(f'user_{event.user_id}', event.user_id):
        db_redis.hdel(f'user_{event.user_id}', event.user_id)
    
    score = db_redis.hget(f'user_{event.user_id}', 'score')
    message_text = f'''Игра закончена!
Ваш счет: {score}

Чтобы начать снова - нажмите кнопку.
'''
    db_redis.hset(f'user_{event.user_id}', 'score', 0)
    keyboard = get_start_quiz_questions_keyboard()
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard.get_keyboard(),
        message=message_text,
        random_id=random.randint(1, 1000)
    )


def win_game(event, vk_api, db_redis):
    print('hendler: win_game')
    if db_redis.hget(f'user_{event.user_id}', event.user_id):
        db_redis.hdel(f'user_{event.user_id}', event.user_id)
    
    score = db_redis.hget(f'user_{event.user_id}', 'score')
    message_text = f'''Поздравляю - вы выиграли!
Ваш счет: {score}

Чтобы начать снова - нажмите кнопку.
'''
    db_redis.hset(f'user_{event.user_id}', 'score', 0)
    keyboard = get_start_quiz_questions_keyboard()
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard.get_keyboard(),
        message=message_text,
        random_id=random.randint(1, 1000)
    )


def event_listening(vk_api, longpoll, db_redis, quiz_questions):
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            reseived_message = event.text

            if reseived_message.lower() == 'привет' or reseived_message.lower() == 'start':
                start(event, vk_api, db_redis)
            elif reseived_message == 'Начать':
                start_quiz_questions(vk_api, event, db_redis)
            elif reseived_message == 'Новый вопрос':
                handle_new_question_request(event, vk_api, db_redis, quiz_questions)
            elif db_redis.hget(f'user_{event.user_id}', event.user_id):
                handle_solution_attempt(event, vk_api, db_redis, quiz_questions)
            else: echo(event, vk_api)



def main():
    load_dotenv()
    db_redis = redis.Redis(host='localhost', port=6379, db=0, charset='utf-8', decode_responses=True)

    vk_token = os.getenv('VK_TOKEN')

    quiz_questions = union_questions()

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

        
    event_listening(vk_api, longpoll, db_redis, quiz_questions)
    db_redis.close()



if __name__=='__main__':
    main()

import os
import logging
import random
from dotenv import load_dotenv
from functools import partial

from telegram import Update, ForceReply, ReplyKeyboardMarkup, MenuButtonCommands, MenuButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from questions import union_questions


logger = logging.getLogger(__name__)

START_KEYBOARD = [['Начать']]
START_QUIZ_QUESTONS_KEYBOARD = [['Новый вопрос']]
CUSTOM_KEYBOARD = [['Новый вопрос', 'Сдаться', 'Мой счет'],
                    ['Закончить игру']]

_right = 5
_loss = 1
_win = 20


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    if context.user_data:
        del context.user_data[update.effective_user.id]
        context.user_data['score'] = 0
        return start_quiz_questions(update, context)
    context.user_data['score'] = 0
    reply_markup = ReplyKeyboardMarkup(START_KEYBOARD, resize_keyboard=True)
    update.message.reply_text(
        'Привет! Я бот для викторин!',
        reply_markup=reply_markup,
    )


def start_quiz_questions(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(START_QUIZ_QUESTONS_KEYBOARD, resize_keyboard=True)
    update.message.reply_text(
        'Чтобы начать игру нажми на кнопку',
        reply_markup=reply_markup,
    )
    return 'new_question'


def handle_new_question_request(update: Update, context: CallbackContext, quiz_questions):
    question = random.choice(list(quiz_questions))
    context.user_data[update.effective_user.id] = question
    reply_markup = ReplyKeyboardMarkup(CUSTOM_KEYBOARD, resize_keyboard=True)
    update.message.reply_text(question, reply_markup=reply_markup)
    return 'user_answer'


def handle_solution_attempt(update: Update, context: CallbackContext, quiz_questions):
    # Новый вопрос
    if update.message.text == 'Новый вопрос':
        return handle_new_question_request(update, context, quiz_questions)
    # Сдаться
    elif update.message.text == 'Сдаться':
        context.user_data['score'] -= _loss
        answer = quiz_questions[context.user_data[update.effective_user.id]]
        update.message.reply_text(f'Правильный ответ: {answer}')
        return handle_new_question_request(update, context, quiz_questions)
    # Мой счет
    elif update.message.text == 'Мой счет':
        score = context.user_data['score']
        message_text = f'Ваш счет: {score}'
        update.message.reply_text(text=message_text)
        return handle_new_question_request(update, context, quiz_questions)
    # Закончить игру
    elif update.message.text == 'Закончить игру':
        return end_game(update, context)
    else:
        return check_answer(update, context, quiz_questions)


def check_answer(update: Update, context: CallbackContext, quiz_questions):
    if context.user_data:
        answer = quiz_questions[context.user_data[update.effective_user.id]]
        user_say = update.message.text
        if user_say.lower() in answer.lower():
            context.user_data['score'] += _right
            reply_markup = ReplyKeyboardMarkup(START_KEYBOARD, resize_keyboard=True)
            update.message.reply_text(
                'Правильно! Поздравляю!',
                reply_markup=reply_markup
            )
            if context.user_data['score'] >= _win:
                return win_game(update, context)
            return handle_new_question_request(update, context, quiz_questions)
        else:
            reply_markup = ReplyKeyboardMarkup(CUSTOM_KEYBOARD, resize_keyboard=True)
            update.message.reply_text(
                'Неправильно… Попробуешь ещё раз?',
                reply_markup=reply_markup
            )


def end_game(update: Update, context: CallbackContext):
    if context.user_data:
        del context.user_data[update.effective_user.id]
    
    score = context.user_data['score']
    message_text = f'''Игра закончена!
Ваш счет: {score}

Чтобы начать снова - нажмите кнопку.
'''
    reply_markup = ReplyKeyboardMarkup(START_KEYBOARD, resize_keyboard=True)
    update.message.reply_text(
        text=message_text,
        reply_markup=reply_markup,
    )
    context.user_data['score'] = 0
    return ConversationHandler.END


def win_game(update: Update, context: CallbackContext):
    if context.user_data:
        del context.user_data[update.effective_user.id]
    
    score = context.user_data['score']
    message_text = f'''Поздравляю - вы выиграли!
Ваш счет: {score}

Чтобы начать снова - нажмите кнопку.
'''
    reply_markup = ReplyKeyboardMarkup(START_KEYBOARD, resize_keyboard=True)
    update.message.reply_text(
        text=message_text,
        reply_markup=reply_markup,
    )
    context.user_data['score'] = 0
    return ConversationHandler.END


def echo(update: Update, context: CallbackContext, quiz_questions) -> None:
    update.message.reply_text(update.message.text)


def main() -> None:
    load_dotenv()

    TG_TOKEN = os.environ['TG_TOKEN']
    files_path = os.environ['FILES_PATH']

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )

    quiz_questions = union_questions(files_path)

    wrap_echo = partial(echo, quiz_questions=quiz_questions)
    wrap_handle_new_question_request = partial(handle_new_question_request, quiz_questions=quiz_questions)
    wrap_user_answer = partial(handle_solution_attempt, quiz_questions=quiz_questions)

    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TG_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    quiz = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^(Начать)$') & ~Filters.command, start_quiz_questions)],
        states={
            'new_question': [MessageHandler(Filters.regex('^(Новый вопрос)$') & ~Filters.command, wrap_handle_new_question_request)],
            'user_answer': [MessageHandler(Filters.text & ~Filters.command, wrap_user_answer)],
        },
        fallbacks=[]
    )

    # on different commands - answer in Telegram
    dispatcher.add_handler(quiz)
    dispatcher.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, wrap_echo))

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
import re

def get_questions(file_path, questions):
    with open(file_path, 'r', encoding='KOI8-R') as file:
        file_content = file.read()

    split_file_content = re.split('\n{3}', file_content)
    
    for item in split_file_content:
        split_items = re.split('\n{2}', item)
        key_question = ''
        value_question = ''
        for split_item in split_items:
            if 'Вопрос' in split_item:
                key_question = re.split(':\n', split_item)[1]
            if 'Ответ' in split_item:
                value_question = re.split(':\n', split_item)[1]
            if key_question and value_question:
                questions[key_question] = value_question


def union_questions(files_path):
    questions = {}

    for file_path in files_path:
        get_questions(file_path, questions)
    
    return questions

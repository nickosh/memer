# -*- coding: utf-8 -*-

en = {
    # Welcome message for user and descriptions for commands /show /up /down /report
    "welcome_message": """Yo! Here we share memes and then get lolz from it. You are welcome!\n\n Just trow your picture right in this chat and very soon it appear in web meme rotator.\n\n If you want, here another usefull commands:\n /start OR /help - this message;\n /show <id> - you can receive meme with this ID right in chat;\n /up <id> - thumb up meme with this ID;\n /down <id> - thumb down meme with this ID;\n /report <id> - vote for deleting this meme, 3 votes and meme will be trowing out;\n\n PS: All commands except /start and /help can be entered without / symbol. Just dont forget whitespace and ID. \n\n Have fun!""",
    # Here what bot answer when save user's meme. Choosed randomly.
    "img_save_answers": ["Haha! Got it.", "Rofl! Not bad.", "Loool! Nice one."],
    # Report accepted message
    "img_reported": "Meme with ID {} reported!",
    # Vote up accepted message
    "vote_up_accepted": "You have lolz at meme with ID {}!",
    # Vote down accepted message
    "vote_down_accepted": "You dislike meme with ID {}!",
    # Error message if no ID founded
    "error_no_id": "Ooops, can't find an ID {}. :(",
    # Error message when user try to vote for same meme another time
    "error_voted": "Already voted! ;)",
    # Error message when user try to report same meme another time
    "error_reported": "Already reported! :/",
    # 'Unknown command' error
    "error_unknown_command": "Don't understand...",
}

ru = {
    # Привественное сообщение и описание для команд /show /up /down /report
    "welcome_message": """Кукусь! Мы тут делимся мемами, а потом дружно над ними орём. Айда с нами!\n\n Просто кидай свою картинку прямо в этот чат и очень скоро увидешь её в общей ленте.\n\n Если хочешь больше, есть пара полезных комманд:\n /start или /help - увидешь данное сообщение;\n /show <id> или /покаж <id> - получить мемасик с этим ID прямо в чатик;\n /up <id> или /ор <id> - оценить мемасик как годный;\n /down <id> или /фу <id> - оценить мемасик как отстойный;\n /report <id> или /удоли <id> - проголосовать за удаление мемасика, три голоса и он отправится в корзину;\n\n ЗЫ: Все команды кроме /start и /help можно вводить без слэша (/). Только ID картинки после пробела не забудь. \n\n Наслаждайся!""",
    # Что бот скажет при сохранении мема. Выбирается случайная фраза.
    "img_save_answers": ["Орно! Схоронил.", "Кек! Хорошо так.", "Лул! Годненько."],
    # Когда пользователь успешно пожаловался на мем
    "img_reported": "Мемасик с ID {} отРосКомНадзорен!",
    # Сообщение, что положительный голос принят
    "vote_accepted": "Мемасик с ID {} успешно пооран!",
    # Сообщение, что отрицательный голос принят
    "vote_down_accepted": "Мемасик с ID {} успешно зафукан!",
    # Ошибка, если не удалось найти ID
    "error_no_id": "Упс, не могу найти ID {}. :(",
    # Когда пользователь пытается проголосовать повторно за тот же мем
    "error_voted": "Голос уже учтён! ;)",
    # Когда пользователь пытается жаловаться повторно на тот же мем
    "error_reported": "Уже донесено! :/",
    # Ошибка при неизвестной команде
    "error_unknown_command": "Моя нипанимать...",
}


class Language:
    def __init__(self, lang):
        if lang == "en":
            self.welcome_message = en["welcome_message"]
            self.img_save_answers = en["img_save_answers"]
            self.img_reported = en["img_reported"]
            self.vote_up_accepted = en["vote_up_accepted"]
            self.vote_down_accepted = en["vote_down_accepted"]
            self.error_no_id = en["error_no_id"]
            self.error_voted = en["error_voted"]
            self.error_reported = en["error_reported"]
            self.error_unknown_command = en["error_unknown_command"]
        elif lang == "ru":
            self.welcome_message = ru["welcome_message"]
            self.img_save_answers = ru["img_save_answers"]
            self.img_reported = ru["img_reported"]
            self.vote_up_accepted = ru["vote_up_accepted"]
            self.vote_down_accepted = ru["vote_down_accepted"]
            self.error_no_id = ru["error_no_id"]
            self.error_voted = ru["error_voted"]
            self.error_reported = ru["error_reported"]
            self.error_unknown_command = ru["error_unknown_command"]
        else:
            raise ValueError("Language param is wrong")

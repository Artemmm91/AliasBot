from keyboards import lobby_keyboard

from hatbot.messages_rus import msg_not_admin


def admin_required(func):
    def wrapper(self):
        if self.player_id in self.players:
            return func(self)
        else:
            self.msg_send(msg_not_admin, lobby_keyboard)
    return wrapper

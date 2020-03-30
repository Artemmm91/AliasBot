from keyboards import lobby_keyboard

from messages_rus import msg_not_admin


def admin_required(func):
    def wrapper(self):
        if self.players[self.player_id][1][6] == 1:
            return func(self)
        else:
            self.msg_send(msg_not_admin, lobby_keyboard)
    return wrapper

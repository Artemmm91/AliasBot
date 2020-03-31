from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import messages_rus as msg


def game_kb():
    kb = VkKeyboard(one_time=False)
    kb.add_button(msg.msg_done, color=VkKeyboardColor.POSITIVE)
    kb.add_button(msg.msg_pass, color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()


def customizing_kb():
    kb = VkKeyboard(one_time=True)
    kb.add_button(msg.msg_change_easy, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_change_medium, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_change_difficult, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_let_input, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_stop_settings, color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()


def lobby_kb():
    kb = VkKeyboard(one_time=True)
    kb.add_button(msg.msg_start, color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button(msg.msg_results, color=VkKeyboardColor.DEFAULT)
    kb.add_button(msg.msg_queue, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_leave, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_add_words, color=VkKeyboardColor.DEFAULT)
    return kb.get_keyboard()

def admin_lobby_kb():
    kb = VkKeyboard(one_time=True)
    kb.add_button(msg.msg_start, color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button(msg.msg_results, color=VkKeyboardColor.DEFAULT)
    kb.add_button(msg.msg_queue, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_leave, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_settings, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_add_words, color=VkKeyboardColor.DEFAULT)
    return kb.get_keyboard()


def begin_kb():
    kb = VkKeyboard(one_time=True)
    kb.add_button(msg.msg_begin, color=VkKeyboardColor.PRIMARY)
    return kb.get_keyboard()


def settings_kb():
    kb = VkKeyboard(one_time=True)
    kb.add_button(msg.msg_current_hat, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_random_hat, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_custom_hat, color=VkKeyboardColor.DEFAULT)
    kb.add_line()
    kb.add_button(msg.msg_null_results, color=VkKeyboardColor.DEFAULT)
    return kb.get_keyboard()


game_keyboard = game_kb()
lobby_keyboard = lobby_kb()
begin_keyboard = begin_kb()
admin_lobby_keyboard = admin_lobby_kb()
settings_keyboard = settings_kb()
customizing_keyboard = customizing_kb()

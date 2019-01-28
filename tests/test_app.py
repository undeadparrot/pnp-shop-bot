from unittest.mock import MagicMock
from telegram import Update, User, Message, Chat
from telegram.ext import Updater, CommandHandler, RegexHandler

from pytest import fixture


class DummyApp():
    def __init__(self):
        from pnp_shop_bot import app, db
        db.delete()
        db.initialize()
        self.chat_id = 1
        self.updater = Updater('123:123')  # fake token
        app.add_command_handlers(self.updater.dispatcher)
        self.mock_bot = MagicMock()

    def send_msg(self, text, chat_id=None):
        if not chat_id:
            chat_id = self.chat_id
        update = Update(1, Message(
            1, User(chat_id, 'test_chat_user', False),
            '',
            Chat(chat_id, 'private'),
            bot=self.mock_bot,
            text=text))
        self.updater.dispatcher.process_update(update)

    def assert_sent(self, text, chat_id=None):
        if not chat_id:
            chat_id = self.chat_id
        self.mock_bot.send_message.assert_called_with(chat_id, text)


@fixture
def app():
    return DummyApp()


def test_registering_new_user(app):
    app.send_msg('/start', chat_id=9)
    app.send_msg('/status', chat_id=9)
    app.assert_sent(
        'You are standing in the middle of 🏨 Tavern, with 0.0 gold in your pocket, and the following items in your backpack:\nnothing', chat_id=9)


def test_status(app):
    app.send_msg('/status')
    app.assert_sent(
        'You are standing in the middle of 🏨 Tavern, with 40.0 gold in your pocket, and the following items in your backpack:\nnothing')


def test_buy(app):
    app.send_msg('/buy_1')
    app.send_msg('/status')
    app.assert_sent(
        'You are standing in the middle of 🏨 Tavern, with 35.0 gold in your pocket, and the following items in your backpack:\n1x 🍞 Bread')


def test_go(app):
    app.send_msg('/go_3')
    app.send_msg('/status')
    app.assert_sent(
        'You are standing in the middle of 🛠 Old Ironworks, with 40.0 gold in your pocket, and the following items in your backpack:\nnothing')


def test_where(app):
    app.send_msg('/where')
    app.assert_sent('🏨 Tavern /go_1\n👨 Baker Barry /go_2\n🛠 Old Ironworks /go_3')


def test_buy_without_enough_money(app):
    app.send_msg('/buy_2')
    app.assert_sent('You don\'t have enough money')

    # check you haven't lost any money
    app.send_msg('/status')
    app.assert_sent(
        'You are standing in the middle of 🏨 Tavern, with 40.0 gold in your pocket, and the following items in your backpack:\nnothing')


def test_list_things_to_buy(app):
    # you start in the tavern
    app.send_msg('/list')
    app.assert_sent(
        'There is nothing for sale here. Try /where to shop somewhere else')

    # you go to the baker
    app.send_msg('/go_2')
    app.send_msg('/list')
    app.assert_sent('🍞 Bread - 5 gold /buy_1\n\tFlour, water, yeast\n')

def test_chat_in_tavern(app):
    # two players must be in tavern, so register a new player
    app.send_msg('/start', chat_id=9)
    app.mock_bot.reset_mock()
    
    # send a message when standing in the tavern, other players should hear it
    app.send_msg('/say Hi', chat_id=app.chat_id)

    # check if the newbie heard the greeting
    app.assert_sent('Tester said "Hi"', chat_id=9)



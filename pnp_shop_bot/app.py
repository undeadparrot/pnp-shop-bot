from functools import wraps
import os
import logging
from telegram import Bot
from telegram.ext import Updater, CommandHandler, RegexHandler
from pnp_shop_bot import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)


def with_db_connection(f):
    @wraps(f)
    def wrapped(bot, update, *args, **kwargs):
        with db.get_connection() as conn:
            return f(conn, bot, update, *args, **kwargs)
    return wrapped

def list_shop_items(conn, location_id:int):
    """ Helper function to print out a list like
        1x Bread /buy_1
          Bread is delicious
        1x Wheat /buy_2
          Wheat is a good ingredient for baking.
    """
    items = db.list_location_inventory(conn, location_id)
    if items:
        return '\n'.join(
            f'{_.name} - {_.price} gold /buy_{_.inventory_id}\n\t{_.description}\n' for _ in items)
    else:
        return 'There is nothing for sale here. Try /where to shop somewhere else'

@with_db_connection
def handle_status(conn, bot, update):
    entity_id = db.get_entity_id(conn, update.message.chat_id)
    status = db.status(conn, entity_id)
    inventory_text = '\n'.join(
        f'{_.quantity}x {_.name}' for _ in status.inventory)
    if not status.inventory:
        inventory_text = 'nothing'
    update.message.reply_text(f''
                              f'You are standing in the middle of {status.location_name}, '
                              f'with {status.money} gold in your pocket, '
                              f'and the following items in your backpack:\n'
                              f'{inventory_text}'
                              )


@with_db_connection
def handle_list(conn, bot, update):
    entity_id = db.get_entity_id(conn, update.message.chat_id)
    status = db.status(conn, entity_id)
    update.message.reply_text(list_shop_items(conn, status.location_id))


@with_db_connection
def handle_where(conn, bot, update):
    locations = db.list_locations(conn)
    update.message.reply_text('\n'.join(
        f'{_.name} /go_{_.location_id}' for _ in locations)) 


@with_db_connection
def handle_go(conn, bot, update, groups):
    location_id = groups[0]
    entity_id = db.get_entity_id(conn, update.message.chat_id)
    db.go(conn, entity_id, location_id)
    update.message.reply_text(list_shop_items(conn, location_id))


@with_db_connection
def handle_buy(conn, bot, update, groups):
    inventory_id = groups[0]
    entity_id = db.get_entity_id(conn, update.message.chat_id)
    db.buy(conn, entity_id, inventory_id)


@with_db_connection
def handle_start(conn, bot, update):
    db.register_player(conn, update.message.chat_id, 'Unnamed')
    update.message.reply_text(
        'Welcome to the town. Type /status to begin, and /where to find places to shop. Please use `/name Almond` to set your name. When you are in the taven, you can use `/say Blah` to talk to others')

@with_db_connection
def handle_name(conn, bot, update, args):
    text = ' '.join(args)
    entity_id = db.get_entity_id(conn, update.message.chat_id)
    db.update_name(conn, entity_id, text)

@with_db_connection
def handle_say(conn, bot, update, args):
    text = ' '.join(args)
    entity_id = db.get_entity_id(conn, update.message.chat_id)
    status = db.status(conn, entity_id)
    nearby_players = db.list_players_in_location(conn, status.location_id)
    for player in nearby_players:
        try:
            update.message.bot.send_message(player.chat_id, f'{status.name} said "{text}"')
        except Exception:
            pass

def error_callback(bot, update, error):
    logging.critical(str(error))
    update.message.reply_text(str(error))


def add_command_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler('status', handle_status))
    dispatcher.add_handler(CommandHandler('where', handle_where))
    dispatcher.add_handler(CommandHandler('list', handle_list))
    dispatcher.add_handler(CommandHandler('start', handle_start))
    dispatcher.add_handler(CommandHandler('name', handle_name, pass_args=True))
    dispatcher.add_handler(CommandHandler('say', handle_say, pass_args=True))
    dispatcher.add_handler(RegexHandler(
        r'/buy_(\d+)', handle_buy, pass_groups=True))
    dispatcher.add_handler(RegexHandler(
        r'/go_(\d+)', handle_go, pass_groups=True))
    dispatcher.add_error_handler(error_callback)


def main():
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        raise Exception(
            "environment variable TELEGRAM_TOKEN should be Telegram bot token")

    # create bot, updater (to poll for messages) and bind command handlers
    bot = Bot(token=TELEGRAM_TOKEN)
    updater = Updater(token=TELEGRAM_TOKEN)
    add_command_handlers(updater.dispatcher)

    # start your engines!
    updater.start_polling()

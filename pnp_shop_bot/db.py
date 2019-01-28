import os
import os.path
import sqlite3
import logging
from typing import List
from dataclasses import dataclass

from telegram.error import TelegramError

TConn = sqlite3.Connection

DB_PATH = os.environ.get('SQLITE3_DB')


def get_connection() -> TConn:
    """ Connect to DB, start session
    """
    if not DB_PATH:
        raise Exception("Environment variable SQLITE3_DB must be path to file")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def delete():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def initialize():
    """ Create tables
    """
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE location (
                location_id     integer primary key,
                name            text default 'Unknown',
                is_start        boolean default 0
            )
        """)
        conn.execute("""
            CREATE TABLE entity (
                entity_id       integer primary key ,
                chat_id         integer unique,
                name            text    default 'Unknown',
                location_id     integer references location(location_id),
                is_shopkeeper   boolean default 0,
                money           float default 0.0
            )
        """)
        conn.execute("""
            create TABLE item (
                item_id         integer primary key,
                name            text default 'unknown',
                description     text default 'unknown'
            )
        """)
        conn.execute("""
            CREATE TABLE inventory (
                inventory_id    integer primary key,
                entity_id       integer not null references entity(entity_id),
                item_id         integer not null references item(item_id),
                quantity        integer not null default 0,
                price           integer
            )
        """)

        # add some seed data
        conn.execute("""
            INSERT INTO location (name, is_start)
            VALUES
            ('🏨 Tavern',          1),
            ('👨 Baker Barry',     0),
            ('🛠 Old Ironworks',   0)
        """)

        conn.execute("""
            INSERT INTO entity (name, is_shopkeeper, location_id)
            VALUES
            ('Barry', 1, 2),
            ('Olga',  1, 3)
        """)

        conn.execute("""
            INSERT INTO item (name, description)
            VALUES
            ('🍞 Bread',       'Flour, water, yeast'),
            ('⚔️ Short Sword', 'Suitable for most combat needs'),
            ('⚔️ Dagger',      'Probably better in the kitchen than a fight')
        """)

        conn.execute("""
            INSERT INTO inventory (entity_id, item_id, quantity, price)
            VALUES
            (1, 1, 16, 5.0),
            (2, 2, 2,  50.0),
            (2, 3, 2,  40.0)
        """)

        # add a dummy test user
        conn.execute("""
            INSERT INTO entity (entity_id, chat_id, name, location_id, money)
            VALUES
            (-1, 1, 'Tester', 1, 40.0)
        """)


@dataclass
class InventoryItem:
    inventory_id: int
    name: str
    description: str
    quantity: int
    price: float


@dataclass
class EntityStatus:
    entity_id: int
    chat_id: int
    name: str
    location_id: str
    location_name: str
    money: float
    inventory: List[InventoryItem]


@dataclass
class Location:
    location_id: int
    name: str


def register_player(conn: TConn, chat_id: int, name: str):
    """ Add player to system, placing them in a starting location
    """
    if not name:
        raise Exception("Please provide a name, like: /start Almond")

    # get the starting location
    location_row = conn.execute("""
        SELECT location_id
        FROM location
        WHERE is_start = 1
    """).fetchone()

    if not location_row:
        raise Exception("No starting locations found")

    conn.execute("""
        INSERT INTO entity
        (chat_id, name, location_id)
        VALUES
        (:chat_id, :name, :location_id)
    """, {
        'chat_id': chat_id,
        'name': name,
        'location_id': location_row['location_id']
    })


def get_entity_id(conn: TConn, chat_id: int) -> int:
    """ Map chat_id from Telegram to a player entity
    """
    entity_row = conn.execute("""
        SELECT entity_id
        FROM entity
        WHERE chat_id = :chat_id
    """, {'chat_id': chat_id}).fetchone()
    if not entity_row:
        raise Exception("No such player!")
    return entity_row['entity_id']


def status(conn: TConn, entity_id: int) -> EntityStatus:
    """ Get info about the current location and player's inventory
    """
    entity_status_row = conn.execute("""
        SELECT 
            p.entity_id, p.chat_id, p.name, p.money,
            p.location_id, l.name as location_name
        FROM entity p
        JOIN location l ON l.location_id = p.location_id
        WHERE p.entity_id=:entity_id
    """, {'entity_id': entity_id}).fetchone()

    inventory_item_rows = conn.execute("""
        SELECT
            inventory_id, quantity, name
        FROM inventory
        JOIN item USING (item_id)
        WHERE entity_id = :entity_id
        AND quantity > 0
    """, {'entity_id': entity_id}).fetchall()

    inventory_items = [InventoryItem(
        **_, description='', price=0.0) for _ in inventory_item_rows]

    entity_status = EntityStatus(
        **entity_status_row, inventory=inventory_items)

    return entity_status

def update_name(conn: TConn, entity_id: int, name: str):
    """ Update a player's name
    """
    conn.execute("""
        UPDATE entity
        SET name = :name
        WHERE entity_id = :entity_id
    """, {'entity_id': entity_id, 'name': name})


def list_locations(conn: TConn) -> List[Location]:
    """ List all available locations
    """
    location_rows = conn.execute("""
        SELECT location_id, name
        FROM location
    """).fetchall()
    return [Location(**_) for _ in location_rows]


def list_players_in_location(conn: TConn, location_id: int) -> List[EntityStatus]:
    """ List all available locations
    """
    entity_id_rows = conn.execute("""
        SELECT entity_id
        FROM entity
        WHERE location_id = :location_id
        AND is_shopkeeper = 0
    """, {'location_id': location_id}).fetchall()
    return [status(conn, _['entity_id']) for _ in entity_id_rows]



def list_location_inventory(conn: TConn, location_id: int) -> List[InventoryItem]:
    """ Get list of items for sale in location, based on first shopkeeper in location
    """
    inventory_rows = conn.execute("""
        SELECT inv.inventory_id, it.name, it.description, inv.quantity, inv.price
        FROM entity shop
        JOIN inventory inv USING (entity_id)
        JOIN item it USING (item_id)
        WHERE shop.location_id = :location_id
        AND shop.is_shopkeeper = 1
    """, {'location_id': location_id}).fetchall()

    return [InventoryItem(**_) for _ in inventory_rows]


def go(conn: TConn, entity_id: int, location_id: int):
    """ Move an entity from one location to another,
    like moving a player into a shop
    """
    conn.execute("""
        UPDATE entity
        SET location_id = :location_id
        WHERE entity_id = :entity_id
    """, {
        'location_id': location_id,
        'entity_id': entity_id
    })


def buy(conn: TConn, entity_id: int, inventory_id: int, *, quantity: int = 1):
    """ Purchase an item for money
    Where the entity_id is the plyaer, and the inventory_id is the item bought.
    The shopkeeper is determinated from the inventory item's owner.
    """
    # validate there is stock
    inv_item = conn.execute("""
        SELECT item_id, quantity, price
        FROM inventory
        WHERE inventory_id = :inventory_id
    """, {'inventory_id': inventory_id}).fetchone()

    if inv_item['quantity'] < quantity:
        raise Exception("There isn't enough in stock")

    total_price = inv_item['price'] * quantity

    # validate the player can afford it
    player = status(conn, entity_id)
    if player.money < total_price:
        raise TelegramError("You don't have enough money")

    # subtract the item from the shopkeeper's inventory
    conn.execute("""
        UPDATE inventory
        SET quantity = quantity - :quantity_sold
        WHERE inventory_id = :inventory_id
    """, {
        'inventory_id': inventory_id,
        'quantity_sold': quantity
    })
    # subtract the price from the player
    conn.execute("""
        UPDATE entity
        SET money = money - :price
        WHERE entity_id = :entity_id
    """, {
        'entity_id': entity_id,
        'price': total_price
    })

    give_item(conn, entity_id, inv_item['item_id'], quantity)


def give_item(conn: TConn, entity_id: int, item_id: int, quantity: int):
    """ Add or subtract the quantity of an item an entity has
    Will create the item in their inventory if it does not exist.
    """

    # does the entity already have this item?
    existing_quantity = conn.execute("""
        SELECT quantity
        FROM inventory
        WHERE entity_id = :entity_id
        AND   item_id   = :item_id
    """, {
        'entity_id': entity_id,
        'item_id': item_id,
    }).fetchone()

    if not existing_quantity:
        # add the item
        conn.execute("""
            INSERT INTO inventory
            (entity_id, item_id, quantity)
            VALUES
            (:entity_id, :item_id, :quantity)
        """, {
            'entity_id': entity_id,
            'item_id': item_id,
            'quantity': quantity
        })

    else:
        # update the item
        conn.execute("""
            UPDATE inventory
            SET quantity = quantity + :quantity_sold
            WHERE entity_id = :entity_id
            AND   item_id   = :item_id
        """, {
            'entity_id': entity_id,
            'item_id': item_id,
            'quantity_sold': quantity
        })

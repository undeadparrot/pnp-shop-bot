# pnp-shop-bot

When running a pen-and-paper RPG campaign (like dnd) players can get stuck on shopping in the town, which could be handled outside of sessions. So here is a bot you can configure to let players move around town and shop, with item descriptions, inventories, stock and prices.

![](https://media.giphy.com/media/CIJsP7PsWvZM4/giphy.gif)

# example

```
/status
You are standing in the middle of 🏨 Tavern, with 99.0 gold in your pocket, and the following items in your backpack:
nothing

/where
🏨 Tavern /go_1
👨🏽‍🍳 Baker Barry /go_2
🛠 Old Ironworks /go_3

/go_3
⚔️ Short Sword - 50 gold /buy_2
 Suitable for most combat needs
⚔️ Dagger - 40 gold /buy_3
 Probably better in the kitchen than a fight

/buy_2
/status
You are standing in the middle of 🛠 Old Ironworks, with 49.0 gold in your pocket, and the following items in your backpack:
1x ⚔️ Short Sword
```

# what state must be tracked?

- where is the player? in which shop?

- how much money does a player have? 

- what is in their inventory?

- what is in a shop's inventory?

# entity types

### Entity

A unique player or shopkeeper. An entity can have inventory items.

### Item

A generic description of a product, for example a Torch.

### Inventory item

A reference to an item in a player or shop's inventory, with a chosen price and quantity. For example, a shop may have 47 Torches at $5 each.

### Location

A place like a shop or tavern. A location can sell things if it has a resident entity.

# what commands are needed?

### `/status`

Mention where the player currently is, their inventory and amount of money, and where they can go.

### `/name [text]`

Change the player's name.

### `/say [text]`

Send a message to other players in the same location (like the starting Tavern).

### `/where`

List places of interest where the player can `/go` to.

### `/go [location_id]`

Move a player between locations.

### `/buy [inventory_id]`

Transfer an item from a shopkeeper to a player, subtracing money from the player and some item quantity from the shopkeeper.

### `/list` 

List the items available from the entity resident at the player's current location. Only list items with quantity >0 and price not null. 

# how to run it

- `pip install .`
- `SQLITE3_DB=db.db pnp_shop_bot_initialize`
- `SQLITE3_DB=db.db TELEGRAM_TOKEN=XXX pnp_shop_bot`



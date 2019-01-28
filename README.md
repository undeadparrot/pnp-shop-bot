# pnp-shop-bot
Bot for handling player shopping in a town

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



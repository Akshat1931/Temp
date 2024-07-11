import discord
import random
import asyncio
import datetime
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Global variables to track battle status
battle_in_progress = False
space_battle_in_progress = False
pokemon_battle_in_progress = False
heroes_battle_in_progress = False
zombie_battle_in_progress = False

# Global variables to store the battle message and participants
battle_message = None
participants = set()

# Global leaderboard and currency system
leaderboard = {}
currency = {}

# Global shop inventory
shop_items = {
    "title": {"price": 200, "description": "Display a special title next to your name."},
    "badge": {"price": 100, "description": "Show a badge on your profile."},
}

# User cosmetics storage
user_titles = {}
user_badges = {}

# Global dictionary to track last claim date
last_claim = {}

# Global achievements storage
achievements = {
    "first_win": {"description": "Win your first battle.", "reward": 10},
    "tactician": {"description": "Win 10 battles.", "reward": 50},
    # Add more achievements as needed
}

user_achievements = {}

# Tic-Tac-Toe game storage
games = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    print(f'Guilds connected to: {[guild.name for guild in bot.guilds]}')
    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(f'Bot has access to channel: {channel.name} in guild: {guild.name}')

@bot.command(name="ping")
async def ping(ctx):
    dc1 = discord.Embed(
        title="Ping",
        description="Pong!",
        color=discord.Color.gold()
    )
    await ctx.reply(embed=dc1)

@bot.command(name="bhelp")
async def help(ctx):
    help_embed = discord.Embed(
        title="Bot Commands",
        description="List of available commands:",
        color=discord.Color.blue()
    )
    help_embed.add_field(name="!ping", value="Ping-pong test command.", inline=False)
    help_embed.add_field(name="!heroesbattle", value="Starts a heroes battle. React with 🦸‍♂️ to join.", inline=False)
    help_embed.add_field(name="!battle", value="Starts a Battle Royale. React with ⚔️ to join.", inline=False)
    help_embed.add_field(name="!spacebattle", value="Starts a Space Battle Royale. React with 🚀 to join.", inline=False)
    help_embed.add_field(name="!pokemonbattle", value="Starts a Pokémon Battle. React with ⚔️ to join.", inline=False)
    help_embed.add_field(name="!zombiebattle", value="Starts a Zombie Battle. React with ⚔️ to join.", inline=False)
    help_embed.add_field(name="!cancelbattle", value="Cancels the ongoing battle.", inline=False)
    help_embed.add_field(name="!leaderboard", value="Shows the current leaderboard.", inline=False)
    help_embed.add_field(name="!balance", value="Shows your current balance.", inline=False)
    help_embed.add_field(name="!shop", value="Displays the shop items.", inline=False)
    help_embed.add_field(name="!buy [item]", value="Buy an item from the shop.", inline=False)
    help_embed.add_field(name="!inventory", value="Shows your inventory.", inline=False)
    help_embed.add_field(name="!daily", value="Claim your daily reward of coins.", inline=False)
    help_embed.add_field(name="!tictactoe @opponent", value="Start a tic-tac-toe game with the mentioned opponent.", inline=False)
    help_embed.add_field(name="!move [1-9]", value="Make a move in the current tic-tac-toe game.", inline=False)
    help_embed.add_field(name="!achievements", value="Shows your current achievements.", inline=False)
    await ctx.send(embed=help_embed)


@bot.command(name="battle")
async def battle(ctx):
    global battle_message
    battle_message = await start_battle(ctx, "Battle Royale", "React to this message with ⚔️ to join the Battle Royale!")

@bot.command(name="spacebattle")
async def spacebattle(ctx):
    global battle_message
    battle_message = await start_battle(ctx, "Space Battle Royale", "React to this message with 🚀 to join the Space Battle Royale!", space=True)

@bot.command(name="heroesbattle")
async def heroesbattle(ctx):
    global battle_message
    battle_message = await start_battle(ctx, "Heroes Battle", "React to this message with 🦸‍♂️ to join the Heroes Battle!", heroes=True)

@bot.command(name="zombiebattle")
async def zombiebattle(ctx):
    global battle_message
    battle_message = await start_battle(ctx, "Zombie Battle", "React to this message with ⚔️ to join the Zombie Battle!", zombie=True)

@bot.command(name="pokemonbattle")
async def pokemonbattle(ctx):
    global battle_message
    battle_message = await start_battle(ctx, "Pokémon Battle", "React to this message with ⚔️ to join the Pokémon Battle!", pokemon=True)

@bot.command(name="cancelbattle")
async def cancelbattle(ctx):
    global battle_in_progress, space_battle_in_progress, pokemon_battle_in_progress, heroes_battle_in_progress, zombie_battle_in_progress
    if any([battle_in_progress, space_battle_in_progress, pokemon_battle_in_progress, heroes_battle_in_progress, zombie_battle_in_progress]):
        reset_battle_flags(space_battle_in_progress, pokemon_battle_in_progress, heroes_battle_in_progress, zombie_battle_in_progress)
        await ctx.send("The current battle has been canceled.")
    else:
        await ctx.send("There is no ongoing battle to cancel.")

@bot.command(name="leaderboard")
async def show_leaderboard(ctx):
    if not leaderboard:
        await ctx.send("The leaderboard is empty.")
        return
    
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    leaderboard_embed = discord.Embed(
        title="Leaderboard",
        description="\n".join([f"{idx+1}. {user}: {points} coins" for idx, (user, points) in enumerate(sorted_leaderboard)]),
        color=discord.Color.purple()
    )
    await ctx.send(embed=leaderboard_embed)

@bot.command(name="balance")
async def balance(ctx):
    user = ctx.author.mention
    bal = currency.get(user, 0)
    await ctx.send(f"{user}, you have {bal} coins.")

@bot.command(name="shop")
async def shop(ctx):
    shop_embed = discord.Embed(
        title="Shop Items",
        description="List of available items:",
        color=discord.Color.green()
    )
    for item, details in shop_items.items():
        shop_embed.add_field(name=item, value=f"Price: {details['price']} coins\nDescription: {details['description']}", inline=False)
    await ctx.send(embed=shop_embed)

@bot.command(name="buy")
async def buy(ctx, item: str):
    user = ctx.author.mention
    bal = currency.get(user, 0)

    if item not in shop_items:
        await ctx.send(f"{user}, the item '{item}' is not available in the shop.")
        return

    item_price = shop_items[item]["price"]
    if bal < item_price:
        await ctx.send(f"{user}, you don't have enough coins to buy '{item}'.")
        return

    currency[user] -= item_price
    if item == "title":
        user_titles[user] = "Special Title"
    elif item == "badge":
        user_badges[user] = "🏅"

    await ctx.send(f"{user}, you have successfully bought '{item}' for {item_price} coins.")

@bot.command(name="inventory")
async def inventory(ctx):
    user = ctx.author.mention
    title = user_titles.get(user, "No Title")
    badge = user_badges.get(user, "No Badge")
    await ctx.send(f"{user}, your inventory:\nTitle: {title}\nBadge: {badge}")

@bot.command(name="daily")
async def daily(ctx):
    user = ctx.author.mention
    today = datetime.datetime.now().date()
    if user in last_claim and last_claim[user] == today:
        await ctx.send(f"{user}, you have already claimed your daily reward today. Come back tomorrow!")
        return
    
    last_claim[user] = today
    reward = 20  # Reward amount can be adjusted
    currency[user] = currency.get(user, 0) + reward
    await ctx.send(f"{user}, you have claimed your daily reward of {reward} coins!")

@bot.command(name="tictactoe")
async def tictactoe(ctx, opponent: discord.Member):
    if opponent == ctx.author:
        await ctx.send("You can't play against yourself!")
        return

    board = [":white_large_square:"] * 9
    current_player = ctx.author
    games[ctx.channel.id] = {"board": board, "current_player": current_player, "opponent": opponent}
    
    board_display = "\n".join(["".join(board[i:i + 3]) for i in range(0, 9, 3)])
    await ctx.send(f"{ctx.author.mention} vs {opponent.mention}\n{board_display}\n{current_player.mention}'s turn! Use `!move [1-9]` to make a move.")

@bot.command(name="move")
async def move(ctx, position: int):
    if ctx.channel.id not in games:
        await ctx.send("There's no ongoing game in this channel. Start a game with `!tictactoe @opponent`.")
        return

    game = games[ctx.channel.id]
    if ctx.author != game["current_player"]:
        await ctx.send("It's not your turn!")
        return

    if not (1 <= position <= 9):
        await ctx.send("Invalid move. Choose a position from 1 to 9.")
        return

    pos_index = position - 1
    if game["board"][pos_index] != ":white_large_square:":
        await ctx.send("That position is already taken. Choose another one.")
        return

    game["board"][pos_index] = ":x:" if ctx.author == game["current_player"] else ":o:"
    game["current_player"] = game["opponent"] if ctx.author == game["current_player"] else ctx.author

    board_display = "\n".join(["".join(game["board"][i:i + 3]) for i in range(0, 9, 3)])
    await ctx.send(f"{board_display}\n{game['current_player'].mention}'s turn!")

    # Check for win or draw
    winner = check_winner(game["board"])
    if winner:
        await ctx.send(f"{winner.mention} wins the game!")
        del games[ctx.channel.id]
    elif ":white_large_square:" not in game["board"]:
        await ctx.send("It's a draw!")
        del games[ctx.channel.id]

def check_winner(board):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Horizontal
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Vertical
        [0, 4, 8], [2, 4, 6]  # Diagonal
    ]
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != ":white_large_square:":
            return board[combo[0]]
    return None

@bot.command(name="achievements")
async def show_achievements(ctx):
    user = ctx.author.mention
    if user not in user_achievements:
        await ctx.send(f"{user}, you have no achievements yet.")
        return
    
    achievement_embed = discord.Embed(
        title="Achievements",
        description="\n".join([f"{achieve} - {achievements[achieve]['description']}" for achieve in user_achievements[user]]),
        color=discord.Color.gold()
    )
    await ctx.send(embed=achievement_embed)

# Function to grant an achievement to a user
def grant_achievement(user, achievement):
    if user not in user_achievements:
        user_achievements[user] = set()
    
    if achievement not in user_achievements[user]:
        user_achievements[user].add(achievement)
        reward = achievements[achievement]["reward"]
        currency[user] = currency.get(user, 0) + reward
        return True
    
    return False

# Example command where you might grant an achievement
@bot.command(name="battle_win")
async def battle_win(ctx):
    # Replace with your actual logic to determine the winner
    participants = ["Player1", "Player2"]
    if participants:
        winner = participants[0]
        if grant_achievement(winner, "first_win"):
            await ctx.send(f"{winner}, you have earned the 'First Win' achievement and received {achievements['first_win']['reward']} coins!")
    else:
        await ctx.send("No participants found.")

async def start_battle(ctx, title, description, space=False, pokemon=False, heroes=False, zombie=False):
    global battle_in_progress, space_battle_in_progress, heroes_battle_in_progress, pokemon_battle_in_progress, zombie_battle_in_progress
    global battle_message, participants

    if zombie:
        if zombie_battle_in_progress:
            await ctx.send("A zombie battle is already in progress. Please wait until it ends.")
            return
        zombie_battle_in_progress = True
    elif pokemon:
        if pokemon_battle_in_progress:
            await ctx.send("A Pokémon battle is already in progress. Please wait until it ends.")
            return
        pokemon_battle_in_progress = True
    elif space:
        if space_battle_in_progress:
            await ctx.send("A space battle is already in progress. Please wait until it ends.")
            return
        space_battle_in_progress = True
    elif heroes:
        if heroes_battle_in_progress:
            await ctx.send("A heroes battle is already in progress. Please wait until it ends.")
            return
        heroes_battle_in_progress = True
    else:
        if battle_in_progress:
            await ctx.send("A battle is already in progress. Please wait until it ends.")
            return
        battle_in_progress = True

    participants = set()
    battle_embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.gold()
    )
    battle_message = await ctx.send(embed=battle_embed)
    reaction_emoji = '⚔️' if not space and not heroes and not pokemon and not zombie else '🚀' if space else '🦸‍♂️' if heroes else '⚔️'
    await battle_message.add_reaction(reaction_emoji)

    def check(reaction, user):
        return str(reaction.emoji) == reaction_emoji and user != bot.user

    await asyncio.sleep(30)  # Time window for joining the game

    if len(participants) < 2:
        await ctx.send("Not enough players joined the Battle Royale. At least 2 participants are required.")
        reset_battle_flags(space, pokemon, heroes, zombie)
        return

    # Embed for Participants
    participants_embed = discord.Embed(
    title=f"{title} Participants",
    description=(f"Number of participants: {len(participants)}\nParticipants:\n" + "\n".join([p.mention for p in participants])
                 if len(participants) < 15 else f"Number of participants: {len(participants)}\nParticipants: {len(participants)} people participated"),
    color=discord.Color.blue()
)

    await ctx.send(embed=participants_embed)
    
    await ctx.send(f"The {title} begins now!")

    # Define kill and self-kill messages for different battle types with emojis
    kill_messages, self_kill_messages = get_battle_messages(space, pokemon, heroes, zombie)

    participants = list(participants)

    while len(participants) > 1:
        await asyncio.sleep(random.randint(5, 15))  # Random delay between updates

        if len(participants) <= 1:
            break
        
        attacker = random.choice(participants)
        victim = random.choice([p for p in participants if p != attacker])
        
        if random.random() < 0.25:  # 25% chance to choose a self-kill message
            message = random.choice(self_kill_messages)
            self_kill_embed = discord.Embed(
                title="Self-Kill Incident",
                description=message.format(f"~~{victim.mention}~~"),
                color=discord.Color.red()
            )
            await ctx.send(embed=self_kill_embed)
            if random.random() < 0.15:
                revive_embed = discord.Embed(
                    title="Revive",
                    description=f"{victim.mention} got a second chance and is back in the game!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=revive_embed)
            else:
                participants.remove(victim)
        else:
            message = random.choice(kill_messages)
            kill_embed = discord.Embed(
                title="Battle Update",
                description=message.format(attacker.mention, f"~~{victim.mention}~~"),
                color=discord.Color.dark_red()
            )
            await ctx.send(embed=kill_embed)
            if random.random() < 0.15:
                revive_embed = discord.Embed(
                    title="Revive",
                    description=f"{victim.mention} got a second chance and is back in the game!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=revive_embed)
            else:
                participants.remove(victim)

    if participants:
        winner = participants[0]
        # Embed for Winner
        winner_embed = discord.Embed(
            title=f"{title} Winner",
            description=f"The winner of the {title} is {winner.mention}!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=winner_embed)

        # Update leaderboard and currency
        leaderboard[winner.mention] = leaderboard.get(winner.mention, 0) + 1
        currency[winner.mention] = currency.get(winner.mention, 0) + 50  # Winner gets 50 coins

        # Grant achievements
        if grant_achievement(winner.mention, "first_win"):
            await ctx.send(f"{winner.mention}, you have earned the 'First Win' achievement and received 10 coins!")

    reset_battle_flags(space, pokemon, heroes, zombie)

def get_battle_messages(space, pokemon, heroes, zombie):
    if zombie:
        kill_messages = [
            "{} smashed a zombie with a baseball bat! 🧟",
            "{} used a shotgun to blast a zombie's head off! 💥",
            "{} decapitated a zombie with a machete! ⚔️",
            "{} burned a zombie to ashes with a flamethrower! 🔥",
            "{} crushed a zombie's skull with a hammer! 🔨"
        ]

        self_kill_messages = [
            "{} accidentally shot themselves! 💀",
            "{} tripped and fell on their own knife! 🔪",
            "{} panicked and ran into a group of zombies! 😱",
            "{}'s flamethrower backfired and burned themselves! 🔥",
            "{}'s grenade exploded too close and injured themselves! 💥"
        ]
    elif pokemon:
        kill_messages = [
            "{}'s Pikachu used Thunderbolt on {}'s Charizard! ⚡",
            "{}'s Bulbasaur used Vine Whip on {}'s Squirtle! 🌿",
            "{}'s Charmander used Flamethrower on {}'s Caterpie! 🔥",
            "{}'s Jigglypuff sang {}'s Onix to sleep, then used Pound! 🎤",
            "{}'s Mewtwo used Psychic on {}'s Machamp! 🔮",
            "{}'s Gengar used Shadow Ball on {}'s Alakazam! 👻",
            "{}'s Eevee evolved and used Hyper Beam on {}'s Gyarados! 🌟",
            "{}'s Dragonite used Draco Meteor on {}'s Vulpix! 💫",
            "{}'s Blastoise used Hydro Pump on {}'s Geodude! 💧",
            "{}'s Snorlax used Body Slam on {}'s Pikachu! 💥"
        ]

        self_kill_messages = [
            "{}'s Magikarp flopped around uselessly and fainted! 🐟",
            "{}'s Ditto transformed into a rock and couldn't move! 🪨",
            "{}'s Metapod only used Harden and got knocked out! 🐛",
            "{}'s Psyduck got confused and hurt itself in its confusion! 🌀",
            "{}'s Wobbuffet kept using Counter at the wrong time! 🛡️",
            "{}'s Slowpoke forgot it was in a battle and wandered off! 🐌",
            "{}'s Jynx got too focused on its lovely kiss and fainted! 💋"
        ]
    elif space:
        kill_messages = [
            "{}'s spaceship blasted {}'s ship into pieces! 🚀",
            "{}'s laser cannon obliterated {}'s defenses! 🔫",
            "{} boarded {}'s ship and took control! 🏴‍☠️",
            "{}'s drone swarm overwhelmed {}'s ship! 🛸",
            "{}'s asteroid maneuver smashed {}'s ship! ☄️",
            "{}'s alien allies vaporized {}'s crew! 👽",
            "{}'s stealth ship ambushed {}'s vessel! 🌌"
        ]

        self_kill_messages = [
            "{}'s ship malfunctioned and exploded! 💥",
            "{}'s crew mutinied and took over the ship! 🛳️",
            "{}'s navigation system failed, crashing into an asteroid! 🌑",
            "{}'s ship got sucked into a black hole! 🕳️",
            "{}'s reactor core overheated and blew up! 🔥"
        ]
    elif heroes:
        kill_messages = [
            "{}'s super strength crushed {} in battle! 💪",
            "{}'s laser vision obliterated {}! 🔥",
            "{}'s invisibility cloak tricked {}! 🕵️",
            "{}'s mind control overpowered {}! 🧠",
            "{}'s speed blitzed {} into submission! ⚡",
            "{}'s magic spell zapped {} out of existence! ✨",
            "{}'s shield bash knocked {} out cold! 🛡️"
        ]

        self_kill_messages = [
            "{} tripped over their own cape and fell! 🦸",
            "{}'s power backfired and hurt themselves! 💥",
            "{} got distracted and was knocked out! 😵",
            "{}'s weapon malfunctioned, causing self-injury! 🔫"
        ]
    else:
        kill_messages = [
            "{} slayed {} with a mighty blow! ⚔️",
            "{} ambushed {} and struck them down! 🗡️",
            "{} outmaneuvered {} and delivered the final blow! 🏹",
            "{} unleashed a flurry of attacks on {}! 🌀",
            "{}'s strategy outsmarted {}! 🧠",
            "{} used a special skill to defeat {}! 🌟",
            "{}'s critical hit took {} by surprise! 🔥",
            "{}'s swift strike finished off {}! 💨",
            "{}'s powerful attack overwhelmed {}! 💥"
        ]

        self_kill_messages = [
            "{} accidentally fell on their own sword! ⚔️",
            "{} tripped and fell, knocking themselves out! 💀",
            "{}'s weapon backfired and injured themselves! 💥",
            "{} got lost and couldn't find their way back! 🧭",
            "{}'s trap caught themselves instead of the enemy! 🪤",
            "{}'s spell misfired and hit themselves! 🔮",
            "{} got distracted and accidentally hurt themselves! 😵"
        ]

    return kill_messages, self_kill_messages

def reset_battle_flags(space, pokemon, heroes, zombie):
    global battle_in_progress, space_battle_in_progress, heroes_battle_in_progress, pokemon_battle_in_progress, zombie_battle_in_progress
    if zombie:
        zombie_battle_in_progress = False
    elif pokemon:
        pokemon_battle_in_progress = False
    elif space:
        space_battle_in_progress = False
    elif heroes:
        heroes_battle_in_progress = False
    else:
        battle_in_progress = False

@bot.event
async def on_reaction_add(reaction, user):
    global participants
    if battle_message is not None and user != bot.user and reaction.message.id == battle_message.id:
        participants.add(user)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Sorry, I didn't understand that command. Type `!bhelp` to see the list of commands.")
    else:
        await ctx.send("An error occurred while processing the command.")
        raise error

bot.run("#")



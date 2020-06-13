# bot.py

import os
from dotenv import load_dotenv
import random
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!')

# TODO: replace movie list & interactions with a database
movie_list = {}

@bot.event
async def on_ready():
    print(
        f'{bot.user.name} is connected to Discord!'
    )


@bot.command(name='add', help='Add a movie to the movie list')
async def add(ctx, arg):
    
    # Query formatted username
    user = str(ctx.message.author.display_name)
    if user == 'None':
        user = str(ctx.message.author).split('#')[0]
    user = user.capitalize()

    add_response = f'Adding {arg} to the movie list! Thanks for the suggestion, {user}.'
    
    # Check for movie in list
    if not arg in movie_list.keys():
        movie_list[arg] = 1
    else:
        add_response = f'{arg} is already in the list!'

    await ctx.send(add_response)


@bot.command(name='list', help='Shows the current movie list')
async def list_movies(ctx):
    list_response = 'Current movie list...\n'

    # Format movie dictionary to multi line string
    for movie, score in movie_list.items():
        list_response += f'{movie}: {score}\n'

    await ctx.send(list_response)

    
@bot.command(name='remove', help='Remove movie from movie list')
async def remove(ctx, arg):
    
    # Query formatted username
    user = str(ctx.message.author.display_name)
    if user == 'None':
        user = str(ctx.message.author).split('#')[0]
    user = user.capitalize()

    remove_response = f'Removing {arg} from the movie list! With great power comes great responsibility, {user}.'
    
    # Check for movie in list
    if arg in movie_list.keys():
        movie_list.pop(arg)
    else:
        remove_response = f"{arg} isn't in the list, but nice try!"
        
    await ctx.send(remove_response)


@bot.command(name='pickmovie', help='Randomly select a movie from the list')
async def pickmovie(ctx):
    
    pick_response = f'Picking a movie from the list, drumroll please....\n\n'

    # Create weighted list
    selection_list = []
    for movie, score in movie_list.items():
        for i in range(int(score)):
            selection_list.append(movie)

    selection = random.choice(selection_list)

    pick_response += f"Tonight we'll be watching {selection}! Huzzah!"

    await ctx.send(pick_response)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Query formatted username
    author_name = str(message.author.nick)
    if author_name == 'None':
        author_name = str(message.author).split('#')[0]
    author_name = author_name.capitalize()

    # TODO: Break this into a separate file?
    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
        'Noice. Smort.',
        'Toight',
        f'{author_name} is an amazing human / genius',
        'Title of your sextape',
        f'{author_name}, with all due respect, I am gonna completely ignore everything you just said.',
        f'{author_name}. Good to see you. But if you’re here, who’s guarding Hades?'
    ]

    response = None
    
    # Message rules here!
    if message.content == '99!':
        response = random.choice(brooklyn_99_quotes)
    elif ('inquisition' or 'inquisitor' or 'inquisitive' or 'inquire' or 'inquiry') in message.content.lower():
        response = 'No one expects the Spanish Inquisition!'

    if response:
        await message.channel.send(response)

    await bot.process_commands(message)


@bot.event
async def on_error(event, *args, **kwargs):
    print('ERR')
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Command Didn\'t Work.')

if __name__ == "__main__":
    bot.run(TOKEN)

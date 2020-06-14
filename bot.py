# bot.py

import os
from dotenv import load_dotenv
import random
from discord.ext import commands
import psycopg2

# sql functions to facilitate bot commands
from sql_utils import addrecord, updaterecord, deleterecords, selectrecords

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

postgres_user = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')
postgres_hostname = os.getenv('POSTGRES_HOSTNAME')
postgres_database = os.getenv('DATABASE_NAME')
movie_table = os.getenv('MOVIE_TABLE_NAME')

# connect to postgres database
try:
    conn = psycopg2.connect(user=postgres_user,
                            password=postgres_password,
                            host=postgres_hostname,
                            port="5432",
                            database=postgres_database)

except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)

bot = commands.Bot(command_prefix='!')

# TODO: replace movie list & interactions with a database
movie_list = {}


@bot.event
async def on_ready():
    print(
        f'{bot.user.name} is connected to Discord!'
    )


@bot.command(name='add', help='Add a movie to the movie list')
async def add(ctx, *args):
    # Query formatted username
    user = parse_username(ctx.message.author)

    try:
        movie_name = parse_movie_name(args)
    except:
        err_message = f"Sorry {user}, I don't understand your request"
        await ctx.send(err_message)
        return

    add_response = f'Adding {movie_name} to the movie list! Thanks for the suggestion, {user}.'

    # Check for movie in list
    if not movie_name in movie_list.keys():
        movie_list[movie_name] = 1

        try:
            addrecord(
                conn=conn,
                table=movie_table,
                key='text',
                title=movie_name,
                submitter=ctx.message.author,
                votes=1
            )
        except Exception as e:
            print('Failed to write to sql')
            print(f'ERR {e}')

    else:
        add_response = f'{movie_name} is already in the list!'

    await ctx.send(add_response)


@bot.command(name='list', help='Shows the current movie list')
async def list_movies(ctx):
    list_response = 'Current movie list...\n'

    # Format movie dictionary to multi line string
    for movie, score in movie_list.items():
        list_response += f'{movie}: {score}\n'

    await ctx.send(list_response)


@bot.command(name='remove', help='Remove movie from movie list')
async def remove(ctx, *args):
    # Query formatted username
    user = parse_username(ctx.message.author)

    try:
        movie_name = parse_movie_name(args)
    except:
        err_message = f"Sorry {user}, I don't understand your request"
        await ctx.send(err_message)
        return

    remove_response = f'Removing {movie_name} from the movie list! Remember, with great power comes great responsibility, {user}.'

    # Check for movie in list
    if movie_name in movie_list.keys():
        # TODO: only use this if command user has proper roles on server like 'bot-wrangler'
        movie_list.pop(movie_name)
    else:
        remove_response = f"{movie_name} isn't in the list, but nice try!"

    await ctx.send(remove_response)


@bot.command(name='pickmovie', help='Randomly select a movie from the list')
async def pickmovie(ctx):
    pick_response = f'Picking a movie from the list, drumroll please....\n\n'

    # TODO: Need a voting systems
    # Create weighted list
    selection_list = []
    for movie, score in movie_list.items():
        for i in range(int(score)):
            selection_list.append(movie)

    selection = random.choice(selection_list)

    pick_response += f"Tonight we'll be watching {selection}! Huzzah!"

    await ctx.send(pick_response)


@bot.event
async def on_reaction_add(reaction, user):

    message = reaction.message

    # in case we ever have the bot react to things
    if user == bot.user:
        return

    # if the reacted message was a movie submission
    if '!add' in message.content:
        # isolate the arg (movie title)
        title = message.content.replace('!add ', '')
        if title in movie_list.keys:
            votes = movie_list.get(title)
            votes = votes + 1
            movie_list.update(title=votes)
            response = 'Thanks for Voting! {} now has {} Votes!'.format(title, votes)

        else:
            response = 'Looks like {} is not in the list anymore. Try another one!'.format(title)

        await message.channel.send(response)

    else:
        return  # remove this if we do anything else with reactions


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

def parse_username(author_obj):
    user = str(author_obj.display_name)
    if user == 'None':
        user = str(author_obj).split('#')[0]
    user = user.capitalize()

    return user

def parse_movie_name(arg_list):
    word_list = [x.capitalize() for x in arg_list]
    movie_name = ' '.join(word_list)
    return movie_name

if __name__ == "__main__":
    bot.run(TOKEN)


# TODO: need to close the postgres connection at some point? but no idea when that happenss by design...
#  only on program end?
"""
finally:
    #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

"""

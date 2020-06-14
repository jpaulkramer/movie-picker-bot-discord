# bot.py

import os
from dotenv import load_dotenv
import random
from discord.ext import commands
import psycopg2

# sql functions to facilitate bot commands
from sql_utils import add_movie, remove_movie, update_movie, get_movie_list

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

postgres_user = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')
postgres_hostname = os.getenv('POSTGRES_HOSTNAME')
postgres_database = os.getenv('DATABASE_NAME')
movie_table = os.getenv('MOVIE_TABLE_NAME')

bot = commands.Bot(command_prefix='!')

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
        title = parse_movie_name(args)
    except:
        err_message = f"Sorry {user}, I don't understand your request"
        await ctx.send(err_message)
        return

    movie_collection = get_movie_list()
    movie_dict = {movie['title']:movie for movie in movie_collection}

    add_response = f'Adding {title} to the movie list! Thanks for the suggestion, {user}.'

    # Check for movie in list
    if not title in movie_dict.keys():
        try:
            add_movie(
                key='text',
                title=title,
                submitter=ctx.message.author,
                votes=1
            )
        except Exception as e:
            print('Failed to write to sql')
            print(f'ERR {e}')

    else:
        user_full = str(ctx.message.author)
        voter_list = movie_dict[title]['voters'].split(',')
        if not user_full in voter_list:
            votes = movie_dict[title]['votes']
            new_voters = "'"+movie_dict[title]['voters']+f'{user_full},'+"'"
            new_votes = votes + 1
            add_response = f'That movie was already in our list, so we voted for it instead! {title} now has {new_votes} votes!'
            update_movie(title, 'votes', new_votes)
            update_movie(title, 'voters', new_voters)

        else:
            add_response = f'{title} is already on the list!'

    await ctx.send(add_response)

@bot.command(name='vote', help='Vote for a movie!')
async def vote(ctx, *args):
    user = parse_username(ctx.message.author)

    try:
        title = parse_movie_name(args)
    except:
        err_message = f"Sorry {user}, I don't understand your request"
        await ctx.send(err_message)
        return
        
    movie_collection = get_movie_list()
    movie_dict = {movie['title']:movie for movie in movie_collection}
    
    if title in movie_dict.keys(): 
        user_full = str(ctx.message.author)
        voter_list = movie_dict[title]['voters'].split(',')
        if not user_full in voter_list:
            votes = movie_dict[title]['votes']
            new_voters = "'"+movie_dict[title]['voters']+f'{user_full},'+"'"
            new_votes = votes + 1
            vote_response = f'Thanks for voting! {title} now has {new_votes} votes!'
            update_movie(title, 'votes', new_votes)
            update_movie(title, 'voters', new_voters)
        else:
            vote_response = f"Sorry {user}, you've already voted for {title}!"
    else:
        vote_response = f"Sorry {user}, {title} isn't on the list! Try to !add it instead"

    await ctx.send(vote_response)

@bot.command(name='list', help='Shows the current movie list')
async def list_movies(ctx):
    list_response = 'Current movie list...\n'

    movie_collection = get_movie_list()

    if len(movie_collection) == 0:
         list_response += 'Empty!\n'
    else:
        for i, movie in enumerate(movie_collection):
            list_response += f"#{i+1} - {movie['title']} ({movie['votes']} points)\n"

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

    # Pull table, format into simple list of titles
    movie_collection = get_movie_list()
    movie_list = [x['title'] for x in movie_collection]

    # Check for movie in list
    if movie_name in movie_list:
        remove_movie(movie_name)
    else:
        remove_response = f"{movie_name} isn't on the list, but nice try!"

    await ctx.send(remove_response)


@bot.command(name='pickmovie', help='Randomly select a movie from the list')
async def pickmovie(ctx):
    pick_response = f'Picking a movie from the list, drumroll please....\n\n'

    # Create weighted list
    
    movie_collection = get_movie_list()
    minimum_threshold = 3
    vote_weight = 2

    selection_list = []
    for movie in movie_collection:
        if int(movie['votes']) >= minimum_threshold:
            vote_score = int(movie['votes'])*vote_weight
            for i in range(vote_score):
                selection_list.append(movie['title'])

    selection = random.choice(selection_list)
    pick_response += f"Tonight we'll be watching {selection}! Huzzah!"
    remove_movie(selection)

    await ctx.send(pick_response)


@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    # in case we ever have the bot react to things
    if user == bot.user:
        return

    # if the reacted message was a movie submission
    if '!add' in message.content or '!vote' in message.content:
        movie_collection = get_movie_list()
        movie_dict = {movie['title']:movie for movie in movie_collection}

        # isolate the arg (movie title)
        title_args = message.content.replace('!add ','').replace('!vote','').split(' ')
        title = parse_movie_name(title_args)

        if title in movie_dict.keys():
            voter_list = movie_dict[title]['voters'].split(',')
            if not str(user) in voter_list:
                votes = movie_dict[title]['votes']
                new_voters = "'"+movie_dict[title]['voters']+f'{user},'+"'"
                new_votes = votes + 1
                response = 'Thanks for voting! {} now has {} votes!'.format(title, new_votes)
                update_movie(title, 'votes', new_votes)
                update_movie(title, 'voters', new_voters)
            else:
                response = f"Sorry {user}, you've already voted for {title}!"
                await message.channel.send(response)
                return

        else:
            response = 'Looks like {} is not on the list anymore. Try another one!'.format(title)

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

    # Call patterns & responses!
    response = None
    message_pattern = message.content.lower()
    easter_egg_list = [
        (['99!'], random.choice(brooklyn_99_quotes)),
        (['difficult','hard','challenging'], 'No no no, super easy, barely an inconvenience'),
        (['inquisition','inquisitor','inquisitive','inquiry','inquire'], 'No one expects the Spanish Inquisition!'),
        (['treasure'], 'Maybe the real treasure was the friends we made along the way'),
        (['pivot'],'https://media.giphy.com/media/3nfqWYzKrDHEI/giphy.gif'),
        (['worm','werm'],'**WERMS**\n\n*This message has been brought to you by Whermhwood Yacht Club, LLC*\n*A subsidiary of Werms Inc*'),
        (['boom','baby'],'https://media.giphy.com/media/11SkMd003FMgW4/giphy.gif')
    ]

    for call, response_str in easter_egg_list:
        if any(x in message_pattern for x in call):
            response = response_str

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
            raise ValueError('No bueno')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Command Didn\'t Work.')


# COMMON UTILITIES

def parse_username(author_obj):
    user = str(author_obj.display_name)
    if user == 'None':
        user = str(author_obj).split('#')[0]
    user = user.capitalize()

    return user

def parse_movie_name(arg_list):
    word_list = [x.lower().capitalize() for x in arg_list]
    movie_name = ' '.join(word_list)
    return movie_name


# MAIN
if __name__ == "__main__":
    bot.run(TOKEN)

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import random
from discord.ext import commands
import psycopg2
import traceback
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load ENV
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN_DEV')
GUILD = os.getenv('DISCORD_GUILD')

# Logging Handler
log_root = r'logs'
date = datetime.today().strftime('%Y-%m-%d')
log_format = logging.Formatter("%(asctime)s - %(name)s - %(funcName)s | %(levelname)s - %(lineno)s - %(message)s")
if not os.path.exists(log_root):
    os.makedirs(log_root)
log_file = os.path.join(log_root, f'{date}_movie-bot.log')

fh = logging.FileHandler(log_file, mode='a')
fh.setLevel(logging.DEBUG)
fh.setFormatter(log_format)
logger.addHandler(fh)

sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(log_format)
logger.addHandler(sh)

from sql_utils import add_movie, remove_movie, update_movie, get_movie_list

# START BOT!
bot = commands.Bot(command_prefix='!')
logger.debug('Bot initialized')

@bot.event
async def on_ready():
    logger.debug(f'{bot.user.name} is connected to Discord!')

# TODO: Add cleanup function

@bot.command(name='history', help='Get user voting history')
async def get_history(ctx):
    # TODO: Return user info 
    # what movies you've voted for
    # number of votes cast
    # number of movies suggested

    pass

@bot.command(name='info', help='Get movie info')
async def get_info(ctx):
    # TODO: Return movie info 
    # movie name
    # number of votes
    # who added it
    # who voted for it
    # when it was voted for last

    pass

@bot.command(name='add', help='Add a movie to the movie list')
async def add(ctx, *args):
    logger.debug('Parsing command - ADD')
    try:
        # Query formatted username
        user = parse_username(ctx.message.author)
        title = parse_movie_name(args)

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
                logger.debug('Failed to write to sql')
                logger.debug(f'ERR {e}')

        else:
            user_full = str(ctx.message.author)
            voter_list = movie_dict[title]['voters'].split(',')
            if not user_full in voter_list:
                title, new_votes = vote_for_movie(movie_dict[title], user_full)
                add_response = f'That movie was already on the list, so we voted for it instead! {title} now has {new_votes} votes!'

            else:
                add_response = f'{title} is already on the list!'

        await ctx.send(add_response)
        logger.debug('Completed command - ADD')

    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f'ADD Error - {e}')
        logger.error(f'Traceback - {trace}')

    return

@bot.command(name='vote', help='Vote for a movie!')
async def vote(ctx, *args):
    logger.debug('Parsing command - VOTE')
    try:
        user = parse_username(ctx.message.author)
        title = parse_movie_name(args)
            
        movie_collection = get_movie_list()
        movie_dict = {movie['title']:movie for movie in movie_collection}
        
        if title in movie_dict.keys(): 
            user_full = str(ctx.message.author)
            voter_list = movie_dict[title]['voters'].split(',')
            if not user_full in voter_list:
                title, new_votes = vote_for_movie(movie_dict[title], user_full)
                vote_response = f'Thanks for voting! {title} now has {new_votes} votes!'
            else:
                vote_response = f"Sorry {user}, you've already voted for {title}!"
        else:
            vote_response = f"Sorry {user}, {title} isn't on the list! Try to !add it instead"

        await ctx.send(vote_response)
        logger.debug('Completed command - VOTE')

    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f'VOTE Error - {e}')
        logger.error(f'Traceback - {trace}')
    
    return

@bot.command(name='list', help='Shows the current movie list')
async def list_movies(ctx):
    logger.debug('Parsing command - LIST')
    try:
        list_response = 'Current movie list...\n'
        logger.debug('Checking database')
        movie_collection = get_movie_list()
        
        if len(movie_collection) == 0:
            logger.debug('Empty list')
            list_response += 'Empty!\n'
        else:
            logger.debug('Compiling sorted list')
            movie_tup_list = []
            for movie in movie_collection:
                new_tup = (movie,movie['votes'])
                movie_tup_list.append(new_tup)
            movie_tup_list.sort(key=takeSecond, reverse=True)
            
            for i, movie_tup in enumerate(movie_tup_list):
                movie, votes = movie_tup
                new_line = f"#{i+1} - {movie['title']} ({votes} points)\n"
                line_limit = 2000
                if (len(list_response)+len(new_line)) >= line_limit:
                    await ctx.send(list_response)
                    list_response = 'Movie list, continued...\n'
                list_response += new_line

        await ctx.send(list_response)
        logger.debug('Completed command - LIST')

    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f'LIST Error - {e}')
        logger.error(f'Traceback - {trace}')

    return


@bot.command(name='remove', help='Remove movie from movie list')
async def remove(ctx, *args):
    logger.debug('Parsing command - REMOVE')
    try:
        # Query formatted username
        user = parse_username(ctx.message.author)
        movie_name = parse_movie_name(args)

        remove_response = f'Removing {movie_name} from the movie list! Remember, {user}, with great power comes great responsibility.'

        # Pull table, format into simple list of titles
        movie_collection = get_movie_list()
        movie_list = [x['title'] for x in movie_collection]

        # Check for movie in list
        if movie_name in movie_list:
            remove_movie(movie_name)
        else:
            remove_response = f"{movie_name} isn't on the list, but nice try!"

        await ctx.send(remove_response)
        logger.debug('Completed command - REMOVE')

    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f'REMOVE Error - {e}')
        logger.error(f'Traceback - {trace}')

    return


@bot.command(name='pickmovie', help='Randomly select a movie from the list')
async def pickmovie(ctx):
    logger.debug('Parsing command - PICK')
    try:
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
        # remove_movie(selection)

        await ctx.send(pick_response)
        logger.debug('Completed command - PICK')

    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f'PICK Error - {e}')
        logger.error(f'Traceback - {trace}')

    return


@bot.event
async def on_reaction_add(reaction, user):
    logger.debug('Parsing command - REACT')

    message = reaction.message
    # in case we ever have the bot react to things
    if user == bot.user:
        return

    # if the reacted message was a movie submission
    if '!add' in message.content or '!vote' in message.content:
        movie_collection = get_movie_list()
        movie_dict = {movie['title']:movie for movie in movie_collection}

        # isolate the arg (movie title)
        title_args = message.content.replace('!add ','').replace('!vote ','').split(' ')
        title = parse_movie_name(title_args)

        if title in movie_dict.keys():
            user_full = str(user)
            voter_list = movie_dict[title]['voters'].split(',')
            if not user_full in voter_list:
                title, new_votes = vote_for_movie(movie_dict[title], user_full)
                vote_response = f'Thanks for voting! {title} now has {new_votes} votes!'
            else:
                user = parse_username(user)
                vote_response = f"Sorry {user}, you've already voted for {title}!"
        else:
            vote_response = 'Looks like {} is not on the list anymore. Try another one!'.format(title)

        await message.channel.send(vote_response)
        logger.debug('Completed command - VOTE REACT')

    else:
        logger.debug('Completed command with no action- REACT')
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

    # Check for easter eggs
    for call, response_str in easter_egg_list:
        if any(x in message_pattern for x in call):
            response = response_str

    if response:
        logger.debug('Easter egg!')
        await message.channel.send(response)

    await bot.process_commands(message)

# ERR HANDLING

@bot.event
async def on_error(event, *args, **kwargs):
    try:
        logger.error(f'{event} - {args[0]}\n')
    except Exception as e:
        logger.error(f'unknown error - {e}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Command Didn\'t Work.')


# COMMON UTILITIES

def takeSecond(elem):
    return elem[1]

def parse_username(author_obj):
    try:
        user = str(author_obj.display_name)
    except:
        user = 'None'

    if user == 'None':
        user = str(author_obj).split('#')[0]
    user = user.capitalize()

    return user

def parse_movie_name(arg_list):
    word_list = [x.lower().capitalize() for x in arg_list]
    movie_name = ' '.join(word_list)

    # Sanitize inputs, remove apostrophe 
    movie_name = movie_name.replace("'","")
    return movie_name

def vote_for_movie(movie, user):
    timestamp = datetime.now().replace(microsecond=0).isoformat().replace(':','-')
    votes = movie['votes']
    new_voters = "'"+movie['voters']+f'{user},'+"'"
    timestamp = "'"+timestamp+"'"
    new_votes = votes + 1
    title = movie['title']

    update_movie(title, 'votes', new_votes)
    update_movie(title, 'voters', new_voters)
    update_movie(title, 'timestamp', timestamp)

    return title, new_votes

# MAIN
if __name__ == "__main__":
    bot.run(TOKEN)

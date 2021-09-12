from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
import asyncio
import requests
import typing as t
from datetime import datetime, timezone
from pathlib import Path
import logging
import re
import json

import discord
from discord.ext import commands, tasks

import httpx
import os
import pymongo
from dotenv import load_dotenv

from chairmanmao.filemanager import DoSpacesConfig, FileManager
from chairmanmao.api import Api
from chairmanmao.draw import DrawManager
from chairmanmao.fourchan import FourChanManager
from chairmanmao.types import Profile, UserId, Json, Role


intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='$', intents=intents)


load_dotenv()


################################################################################
# Logging
################################################################################


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stream = logging.StreamHandler()
streamformat = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
stream.setFormatter(streamformat)
logger.addHandler(stream)


@client.before_invoke
async def log(ctx):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    now_str = str(now)[:-6]
    author = member_to_username(ctx.author)
    command_name = ctx.command.name
    logger.info(f'{author}: {command_name}()')


################################################################################
# MongoDB
################################################################################


MONGODB_URL = os.getenv('MONGODB_URL', '')
MONGODB_DB = os.getenv('MONGODB_DB', '')

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
MEMBER_ID_KOTOBA = int(os.getenv('MEMBER_ID_KOTOBA', ''))

mongo_client = pymongo.MongoClient(MONGODB_URL)
db = mongo_client[MONGODB_DB]
api = Api.connect(MONGODB_URL, MONGODB_DB)


################################################################################
# Managers
################################################################################


do_spaces_config = DoSpacesConfig.from_environment()
file_manager = FileManager(do_spaces_config)
draw_manager = DrawManager(file_manager)
fourchan_manager = FourChanManager(file_manager)


################################################################################
# Commands
################################################################################


@client.command(name='socialcredit', help='See your social credit score.')
@commands.has_role('同志')
async def cmd_socialcredit(ctx, member: commands.MemberConverter = None):
    username = member_to_username(ctx.author)

    if member is not None:
        target_username = member_to_username(member)
    else:
        target_username = username

    credit = api.as_comrade(ctx.author.id).social_credit(member.id)
    await ctx.send(f'{target_username} has a credit score of {credit}.')


@client.command(name='hsk', help='See your HSK rank.')
@commands.has_role('同志')
async def cmd_hsk(ctx, member: commands.MemberConverter = None):
    if member is not None:
        target_member = member
    else:
        target_member = ctx.author

    target_username = member_to_username(target_member)
    hsk_level = api.as_chairman().get_hsk(target_member.id)

    if hsk_level is None:
        await ctx.send(f'{target_username} is unranked.')
    else:
        await ctx.send(f'{target_username} has reached HSK {hsk_level}.')


@client.command(name='stepdown', help="Remove 共产党员 role.")
@commands.has_role('共产党员')
async def  cmd_stepdown(ctx):
    api.as_party(ctx.author.id).stepdown()
    queue_member_update(ctx.author.id)
    await ctx.send(f'{ctx.author.display_name} has stepped down from the CCP.')


@client.command(name='promote')
@commands.has_role('共产党员')
@commands.is_owner()
async def  cmd_promote(ctx, member: commands.MemberConverter, flag: t.Optional[bool] = None):
    api.as_chairman().promote(member.id)
    queue_member_update(member.id)
    await ctx.send(f'{ctx.author.display_name} has been promoted to the CCP.')


@client.command(name='sync')
@commands.has_role('共产党员')
@commands.is_owner()
async def  cmd_sync(ctx, member: commands.MemberConverter):
    queue_member_update(member.id)
    await ctx.send('Sync complete')


@client.command(name='recognize', help="Remove 共产党员 role.")
@commands.has_role('共产党员')
async def cmd_recognize(ctx, member: commands.MemberConverter):
    message = ctx.message
    comrade_role = discord.utils.get(message.channel.guild.roles, name='同志')
    username = member_to_username(member)
    assert comrade_role not in member.roles, 'Member is already a 同志.'

    api.as_party(ctx.author.id).recognize(member.id, username)

    queue_member_update(member.id)
    await ctx.send(f'{ctx.author.display_name} has recognized Comrade {username}.')


@client.command(name='jail')
@commands.has_role('共产党员')
async def cmd_jail(ctx, member: commands.MemberConverter):
    api.as_party(ctx.author.id).jail(member.id)
    username = member_to_username(member)
    queue_member_update(member.id)
    await ctx.send(f'{ctx.author.display_name} has jailed Comrade {username}.')


@client.command(name='unjail')
@commands.has_role('共产党员')
async def cmd_unjail(ctx, member: commands.MemberConverter):
    api.as_party(ctx.author.id).unjail(member.id)
    username = member_to_username(member)
    queue_member_update(member.id)
    await ctx.send(f'{ctx.author.display_name} has unjailed Comrade {username}.')


@client.command(name='honor', help="Add social credit to a user.")
@commands.has_role('共产党员')
@commands.is_owner()
async def cmd_honor(ctx, member: commands.MemberConverter, credit: int):
    assert credit > 0

    username = member_to_username(ctx.author)
    target_username = member_to_username(member)
    new_credit = api.as_chairman().honor(member.id, credit)
    old_credit = new_credit - credit

    queue_member_update(member.id)
    await ctx.send(f'{target_username} has had their credit score increased from {old_credit} to {new_credit}.')


@client.command(name='dishonor', help="Remove social credit from a user.")
@commands.has_role('共产党员')
@commands.is_owner()
async def cmd_dishonor(ctx, member: commands.MemberConverter, credit: int):
    assert credit > 0

    username = member_to_username(ctx.author)
    target_username = member_to_username(member)
    new_credit = api.as_chairman().dishonor(member.id, credit)
    old_credit = new_credit + credit

    queue_member_update(member.id)
    await ctx.send(f'{target_username} has had their credit score decreased from {old_credit} to {new_credit}.')


@client.command(name='learner', help='Add or remove 中文学习者 role.')
@commands.has_role('同志')
async def cmd_learner(ctx, flag: bool = True):
    learner_role = discord.utils.get(ctx.guild.roles, name="中文学习者")

    api.as_comrade(ctx.author.id).set_learner(flag)
    queue_member_update(ctx.author.id)
    if flag:
        await ctx.send(f'{ctx.author.display_name} has been added to {learner_role.name}')
    else:
        await ctx.send(f'{ctx.author.display_name} has been removed from {learner_role.name}')


@client.command(name='quiz')
@commands.has_role("中文学习者")
async def cmd_quiz(ctx):
    hsk_level = api.as_chairman().get_hsk(ctx.author.id)

    if hsk_level is None:
        aiming_for = 1
    else:
        aiming_for = hsk_level + 1

    if hsk_level == 6:
        msg = 'You are at the max HSK level.'
    else:
        num_questions = SCORE_LIMIT_BY_DECK.get(f'hsk{aiming_for}')
        msg = f'For the next quiz, use:\n`k!quiz hsk{aiming_for} mmq=1 atl=10 {num_questions}`'

    await ctx.send(msg)


@client.command(name='name', help='Set your name.')
@commands.has_role('同志')
async def cmd_name(ctx, name: str):
    member = ctx.author
    username = member_to_username(member)

    try:
        api.as_comrade(member.id).set_name(name)
    except:
#        await ctx.send("Names are 32 character max.")
#        return
        raise

    profile = api.as_chairman().get_profile(member.id)
    assert profile is not None

    queue_member_update(member.id)
    await ctx.send(f"{username}'s nickname has been changed to {name}")


@client.command(name='hanzi', help='Show the count and list of all hanzi a user has taken.')
@commands.has_role('同志')
async def cmd_hanzi(ctx, member: commands.MemberConverter = None):
    if member is None:
        member = ctx.author

    username = member_to_username(ctx.author)
    target_username = member_to_username(member)

    hanzi = api.as_comrade(ctx.author.id).get_hanzis(member.id)
    hanzi_str = ' '.join(hanzi)
    num_hanzi = len(hanzi)
    await ctx.send(f'{target_username} has {num_hanzi} hanzi: {hanzi_str}')


@client.command(name='setname', help="Sets the name of another user.")
@commands.has_role('共产党员')
@commands.is_owner()
async def cmd_setname(ctx, member: commands.MemberConverter, name: str):
    target_username = member_to_username(member)

    try:
        api.as_chairman().set_name(member.id, name)
    except:
#        await ctx.send("Names are 32 character max.")
#        return
        raise

    profile = api.as_chairman().get_profile(member.id)
    assert profile is not None
    queue_member_update(member.id)
    await ctx.send(f"{target_username}'s nickname has been changed to {name}")


@client.command(name='setlearner')
@commands.has_role('共产党员')
@commands.is_owner()
async def cmd_setlearner(ctx, member: commands.MemberConverter, flag: bool = True):
    target_username = member_to_username(member)
    api.as_comrade(member.id).set_learner(flag)
    queue_member_update(member.id)
    await ctx.send(f"{target_username}'s learner status has been changed to {flag}")


@client.command(name='sethsk')
@commands.has_role('共产党员')
@commands.is_owner()
async def cmd_sethsk(ctx, member: commands.MemberConverter, hsk_level: t.Optional[int]):
    target_username = member_to_username(member)
    api.as_chairman().set_hsk(member.id, hsk_level)
    queue_member_update(member.id)
    await ctx.send(f"{target_username}'s HSK level has been changed to {hsk_level}")


@client.command(name='draw', help="Draw a simplified hanzi character.")
@commands.has_role('同志')
async def cmd_draw(ctx, chars: str, font: t.Optional[str] = None):
    if font is None:
        font = 'kuaile'

    for char in chars:
        assert is_hanzi(char)

    image_buffer = draw_manager.draw(font, chars)
    filename = 'hanzi_' + '_'.join('u' + hex(ord(char))[2:] for char in chars) + '.png'
    await ctx.channel.send(file=discord.File(fp=image_buffer, filename=filename))


@client.command(name='font')
@commands.has_role('同志')
@commands.cooldown(1, 5 * 60, type)
async def cmd_font(ctx, font_name: str):

    if font_name == 'list':
        font_names = draw_manager.get_font_names()
        await ctx.send(f"The available fonts are: " + ' '.join(font_names))
        return

    if not font_name.isidentifier():
        await ctx.send(f"Please name the font with no spaces, ASCII-only, beginning with a letter")
        return

    if len(ctx.message.attachments) != 1:
        await ctx.send(f"You didn't attach a font to your message")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.url.endswith('.ttf'):
        await ctx.send(f"Your font doesn't look like a TTF font.")
        return

    resp = requests.get(attachment.url)
    draw_manager.upload_font(ctx.author.id, font_name, BytesIO(resp.content))
    await ctx.send(f"Uploaded font: {font_name}.")


@client.command(name='yuan')
@commands.has_role('同志')
async def cmd_yuan(ctx):
    username = member_to_username(ctx.author)
    yuan = api.as_comrade(username).get_yuan()
    await ctx.send(f"{username} has {yuan} RNB.")


@client.command(name='leaderboard', help='Show the DMT leaderboard.')
@commands.has_role('同志')
@commands.cooldown(1, 5 * 60, commands.BucketType.guild)
async def cmd_leaderboard(ctx, member: commands.MemberConverter = None):
    lines = [
        "The DMT Leaderboard",
        "```",
    ]

    username = member_to_username(ctx.author)
    for entry in api.as_comrade(ctx.author.id).leaderboard():
        line = f'{entry.credit} ... {entry.display_name}'
        lines.append(discord.utils.remove_markdown(line))

    lines.append("```")

    await ctx.send('\n'.join(lines))


@client.command(name='mine', help='Mine a word.')
@commands.has_role('同志')
async def cmd_mine(ctx, word: str):

    username = member_to_username(ctx.author)
    api.as_comrade(ctx.author.id).mine(word)

    await ctx.send(f'{username} has mined: {word}')


@client.command(name='debug')
@commands.has_role("共产党员")
@commands.is_owner()
async def cmd_debug(ctx):
    breakpoint()


################################################################################
# Events
################################################################################


@client.event
async def on_message(message):
    if isinstance(message.channel, discord.channel.TextChannel):
        comrade_role = discord.utils.get(message.channel.guild.roles, name='同志')
        if comrade_role in message.author.roles:
            api.as_comrade(message.author.id).alert_activity()

            hanzis = hanzis_in(message.content)
            api.as_comrade(message.author.id).see_hanzis(hanzis)

    if message.author.bot and message.author.id == MEMBER_ID_KOTOBA:
        await handle_kotoba(message)

    await client.process_commands(message)


@dataclass
class QuizResults:
    user_id: UserId
    deck_name: str
    quiz_id: str


async def get_quiz_results(message: discord.Message) -> t.Optional[QuizResults]:
    fields = {}

    for embed in message.embeds:
        for field in embed.fields:
            fields[field.name] = field.value

    if 'Final Scores' in fields:
        final_score = fields['Final Scores']
        assert final_score.startswith('<@')
        assert '>' in final_score
        idx = final_score.index('>')
        user_id = int(final_score[2:idx])

        game_report = fields['Game Report']
        quiz_id = re.search(r'game_reports/([a-f0-9]+)\)', game_report).group(1)  # type: ignore

        url = f"https://kotobaweb.com/api/game_reports/{quiz_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            kotoba_json = response.json()

        if len(kotoba_json['decks']) != 1:
            return None

        deck = kotoba_json['decks'][0]

        deck_unique_id = deck['uniqueId']
        deck_start_index = deck.get('startIndex')
        deck_end_index = deck.get('endIndex')
        deck_mc = deck['mc']

        allowed_decks = {
            'bba20c1c-d145-4f1e-8d6b-1255f7b3e1fd': 'hsk1',
            '9ec40e85-c286-409a-9345-f904e642a517': 'hsk2',
            '3885e46e-c8c8-4f61-9f2e-4f3beafea7a5': 'hsk3',
            'e4b6a777-9bc2-46ed-825d-dabb5259273a': 'hsk4',
            'ebf64032-7959-4005-93c4-5276203c24ce': 'hsk5',
            'eb7a83ed-d18a-4ab0-92cc-73b13546280b': 'hsk6',
        }

        deck_name = allowed_decks.get(deck_unique_id)
        if deck_name is None:
            return None

        settings_json = kotoba_json['settings']
        if not allowable_settings(deck_name, settings_json):
            return None

        is_loaded = kotoba_json['isLoaded']

        assert is_loaded is False
        assert len(kotoba_json['participants']) == 1
        assert kotoba_json['participants'][0]['discordUser']['id'] == str(user_id)
        assert len(kotoba_json['scores']) == 1

        assert deck_start_index is None
        assert deck_end_index is None
        assert deck_mc is False

        question_count = len(kotoba_json['questions'])
        score = kotoba_json['scores'][0]['score']

        if score == question_count:
            hsk_level = int(deck_name[-1])

            old_hsk_level = api.as_chairman().get_hsk(user_id)

            if old_hsk_level is None or old_hsk_level < hsk_level:
                api.as_chairman().set_hsk(user_id, hsk_level)
                queue_member_update(user_id)

                return QuizResults(
                    user_id=user_id,
                    deck_name=deck_name,
                    quiz_id=quiz_id
                )

            else:
                return None
        else:
            return None

    else:
        return None


SCORE_LIMIT_BY_DECK = {
    'hsk1': 1,
    'hsk2': 1,
    'hsk3': 5,
    'hsk4': 5,
    'hsk5': 5,
    'hsk6': 7,
}


def allowable_settings(deck_name: str, settings_json: Json) -> bool:

    required_settings = {
        'shuffle': True,
        'scoreLimit': SCORE_LIMIT_BY_DECK[deck_name],
        'maxMissedQuestions': 1,
        'answerTimeLimitInMs': 10000,
#        "fontSize": 80,
        "fontColor": "rgb(0, 0, 0)",
        "backgroundColor": "rgb(255, 255, 255)",
        "font": "Noto Sans CJK",
    }

    for setting_name, required_value in required_settings.items():
        actual_value = settings_json[setting_name]
        if actual_value != required_value:
            print('bad setting:', setting_name, 'has value', actual_value, 'but needs to be', required_value)
            return False

    return True


async def handle_kotoba(message):
    quiz_results = await get_quiz_results(message)
    if quiz_results is not None:

        profile = api.as_chairman().get_profile(quiz_results.user_id)
        await message.channel.send(f'{profile.discord_username} has passed the {quiz_results.deck_name} quiz.')


def hanzis_in(text: str) -> t.List[str]:
    return [char for char in text if is_hanzi(char)]


def is_hanzi(char):
    '''
        https://blog.ceshine.net/post/cjk-unicode/#respective-unicode-blocks
    '''
    codepoint = ord(char)

    return (
        0x4E00 <= codepoint <= 0x9FFF or
        0x3400 <= codepoint <= 0x4DBF or
        0x20000 <= codepoint <= 0x2A6DF or
        0x2A700 <= codepoint <= 0x2B73F or
        0x2B740 <= codepoint <= 0x2B81F or
        0x2B820 <= codepoint <= 0x2CEAF or
        0xF900 <= codepoint <= 0xFAFF or
        0x2F800 <= codepoint <= 0x2FA1F
    )


@client.event
async def on_reaction_add(reaction, user):
    user_to_credit = reaction.message.author
    if user_to_credit != user:
        target_username = member_to_username(user_to_credit)
        credit = api.as_chairman().honor(user_to_credit.id, 1)
        queue_member_update(user_to_credit.id)
        logger.info(f'User reaction added to {user_to_credit}: {credit}')


@client.event
async def on_reaction_remove(reaction, user):
    user_to_credit = reaction.message.author
    if user_to_credit != user:
        target_username = member_to_username(user_to_credit)
        credit = api.as_chairman().dishonor(user_to_credit.id, 1)
        queue_member_update(user_to_credit.id)
        logger.info(f'User reaction removed from {user_to_credit}: {credit}')


@client.event
async def on_voice_state_update(member, before, after):
    guild = client.guilds[0]
    voice_role = discord.utils.get(guild.roles, name="在声音中")
    voice_channel = discord.utils.get(guild.voice_channels, name="🎤谈话室")
    if after.channel == voice_channel:
        await member.add_roles(voice_role)
    elif after.channel is None:
        await member.remove_roles(voice_role)


GUILD = None


def set_guild():
    global GUILD
    GUILD = client.guilds[0]


def get_guild():
    return GUILD


INVITES = {}


async def init_invites():
    invites = await get_guild().invites()
    for invite in invites:
        INVITES[invite.code] = invite


async def get_current_invite():
    old_invites = INVITES

    new_invites = {}
    for invite in await get_guild().invites():
        new_invites[invite.code] = invite

    for code, old_invite in old_invites.items():
        code = old_invite.code
        new_invite = new_invites[code]

        if old_invite.uses < new_invite.uses:
            old_invites[code] = new_invite
            return new_invite

    return None


@client.event
async def on_ready():
    logger.info('Ready.')
    set_guild()
    await init_invites()

    loop_dmtthread.start()
    loop_incremental_member_update.start()
    loop_full_member_update.start()


@client.event
async def on_member_join(member):
    guild = client.guilds[0]
    invite = await get_current_invite()
    logger.info(f'{member.name} joined with invite code {invite.code} from {member_to_username(invite.inviter)}')


################################################################################
# 4chan Threads
################################################################################

def thread_channel():
    guild = client.guilds[0]
    assert guild.name == 'Daily Mandarin Thread'

    for channel in guild.channels:
        if channel.name.startswith('🧵'):
            return channel

    raise Exception()


@tasks.loop(seconds=60)
async def loop_dmtthread():
    thread = await fourchan_manager.get_dmt_thread()
    if thread is not None:
        if not fourchan_manager.is_url_seen(thread.url):
            logger.info(f'Found DMT thread: {thread.url}')
            fourchan_manager.see_url(thread.url)
            channel = thread_channel()
            lines = [
                thread.title,
                thread.url,
            ]
            await channel.send('\n'.join(lines))


################################################################################
# Member Update Queue
################################################################################


member_update_queue = set()


def queue_member_update(user_id: UserId) -> None:
    member_update_queue.add(user_id)


def flush_member_update_queue() -> t.List[UserId]:
    user_ids = list(member_update_queue)
    member_update_queue.clear()
    return user_ids


################################################################################
# Member Update
################################################################################


@tasks.loop(seconds=1)
async def loop_incremental_member_update():
    guild = client.guilds[0]
    await incremental_member_update(guild)


@tasks.loop(hours=24)
async def loop_full_member_update():
    guild = client.guilds[0]
    logger.info('Starting full member update')
    await full_member_update(guild)
    logger.info('Full member update complete')


async def incremental_member_update(guild: discord.Guild) -> None:
    for user_id in flush_member_update_queue():
        profile = api.as_chairman().get_profile(user_id)
        did_update = await update_member_nick(guild, profile)
        if did_update:
            await asyncio.sleep(0.5)
        did_update = await update_member_roles(guild, profile)
        if did_update:
            await asyncio.sleep(0.5)


async def full_member_update(guild: discord.Guild) -> None:
    user_ids = api.as_chairman().list_users()
    for user_id in user_ids:
        profile = api.as_chairman().get_profile(user_id)
        did_update = await update_member_nick(guild, profile)
        if did_update:
            await asyncio.sleep(0.5)
        did_update = await update_member_roles(guild, profile)
        if did_update:
            await asyncio.sleep(0.5)


################################################################################
# Member Renaming
################################################################################


async def update_member_nick(guild: discord.Guild, profile: Profile) -> bool:
    '''
        Return if nick updated.
    '''
    member = profile_to_member(guild, profile)
    if member is None:
        return False

    if member.bot:
        return False

    username = member_to_username(member)
    if username == ADMIN_USERNAME:
        return False

    if profile.is_jailed():
        new_nick = add_label_to_nick(profile.display_name, "JAILED")
    else:
        label = f' [{profile.credit}]'

        hsk_level = profile.hsk_level()
        if hsk_level is not None:
            hsk_label = {
                1: '➀',
                2: '➁',
                3: '➂',
                4: '➃',
                5: '➄',
                6: '➅',
            }
            label += ' HSK' + hsk_label[hsk_level]

        if profile.is_learner():
            label += '✍'

        new_nick = add_label_to_nick(profile.display_name, label)

    if new_nick == member.nick:
        return False

    logger.info(f'Rename {member.nick} -> {new_nick}')
    await member.edit(nick=new_nick)
    return True


################################################################################
# Member Rolesetting
################################################################################


async def update_member_roles(guild: discord.Guild, profile: Profile) -> bool:
    '''
        Return if roles updated.
    '''
    member = profile_to_member(guild, profile)
    if member is None:
        return False

    current_roles = set(member.roles)

    roles_to_add = roles_for(guild, profile).difference(current_roles)
    roles_to_remove = nonroles_for(guild, profile).intersection(current_roles)

    if not roles_to_add and not roles_to_remove:
        return False

    await member.add_roles(*roles_to_add)
    await member.remove_roles(*roles_to_remove)

    added_roles = sorted(r.name for r in roles_to_add)
    removed_roles = sorted(r.name for r in roles_to_remove)
    logger.info(f'Updating roles: {member.nick}: add {added_roles}, remove {removed_roles}')
    return True


def roles_for(guild: discord.Guild, profile: Profile) -> t.Set[discord.Role]:
    comrade_role = discord.utils.get(guild.roles, name='同志')
    ccp_role     = discord.utils.get(guild.roles, name="共产党员")
    jailed_role  = discord.utils.get(guild.roles, name="JAILED")
    learner_role = discord.utils.get(guild.roles, name="中文学习者")
    hsk1         = discord.utils.get(guild.roles, name="HSK1")
    hsk2         = discord.utils.get(guild.roles, name="HSK2")
    hsk3         = discord.utils.get(guild.roles, name="HSK3")
    hsk4         = discord.utils.get(guild.roles, name="HSK4")
    hsk5         = discord.utils.get(guild.roles, name="HSK5")
    hsk6         = discord.utils.get(guild.roles, name="HSK6")

    if profile.is_jailed():
        return {jailed_role}
    else:
        roles = {comrade_role}

        if profile.is_party():
            roles.add(ccp_role)

        if profile.is_learner():
            roles.add(learner_role)

        dmt_hsk_role = profile.hsk_role()

        if dmt_hsk_role is not None:
            hsk_discord_role = {
                Role.Hsk1: hsk1,
                Role.Hsk2: hsk2,
                Role.Hsk3: hsk3,
                Role.Hsk4: hsk4,
                Role.Hsk5: hsk5,
                Role.Hsk6: hsk6,
            }[dmt_hsk_role]

            roles.add(hsk_discord_role)

        return roles


def nonroles_for(guild: discord.Guild, profile: Profile) -> t.Set[Role]:
    comrade_role = discord.utils.get(guild.roles, name='同志')
    ccp_role     = discord.utils.get(guild.roles, name="共产党员")
    jailed_role  = discord.utils.get(guild.roles, name="JAILED")
    learner_role = discord.utils.get(guild.roles, name="中文学习者")
    hsk1         = discord.utils.get(guild.roles, name="HSK1")
    hsk2         = discord.utils.get(guild.roles, name="HSK2")
    hsk3         = discord.utils.get(guild.roles, name="HSK3")
    hsk4         = discord.utils.get(guild.roles, name="HSK4")
    hsk5         = discord.utils.get(guild.roles, name="HSK5")
    hsk6         = discord.utils.get(guild.roles, name="HSK6")
    all_roles = {comrade_role, ccp_role, jailed_role, learner_role, hsk1, hsk2, hsk3, hsk4, hsk5, hsk6}
    return all_roles.difference(roles_for(guild, profile))


################################################################################
# Utils
################################################################################


def add_label_to_nick(display_name: str, label: str) -> str:
    cutoff = 32 - len(label)
    return display_name[:cutoff] + label


def profile_to_member(guild: discord.Guild, profile: Profile) -> t.Optional[discord.Member]:
    for member in client.guilds[0].members:
        if member.id == profile.user_id:
            return member
    return None


def member_to_username(member) -> str:
    return member.name + '#' + member.discriminator


def news_channel():
    guild = client.guilds[0]
    assert guild.name == 'Daily Mandarin Thread'

    for channel in guild.channels:
        if channel.name.startswith('🧵'):
            return channel

    raise Exception()

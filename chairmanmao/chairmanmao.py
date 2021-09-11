from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
import asyncio
import requests
import typing as t
from datetime import datetime, timezone
from pathlib import Path
import logging

import discord
from discord.ext import commands, tasks

import os
import pymongo
from dotenv import load_dotenv

from chairmanmao.filemanager import DoSpacesConfig, FileManager
from chairmanmao.api import Api
from chairmanmao.draw import DrawManager
from chairmanmao.fourchan import FourChanManager

if t.TYPE_CHECKING:
    from chairmanmao.types import Profile, UserId, Json


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


@client.command(name='stepdown', help="Remove 共产党员 role.")
@commands.has_role('共产党员')
async def  cmd_stepdown(ctx):
    ccp_role = discord.utils.get(ctx.guild.roles, name="共产党员")
    await ctx.author.remove_roles(ccp_role)
    await ctx.send(f'{ctx.author.display_name} has stepped down from the CCP.')


@client.command(name='recognize', help="Remove 共产党员 role.")
@commands.has_role('共产党员')
async def cmd_recognize(ctx, member: commands.MemberConverter):
    message = ctx.message
    comrade_role = discord.utils.get(message.channel.guild.roles, name='同志')
    username = member_to_username(member)
    assert comrade_role not in member.roles, 'Member is already a 同志.'

    api.as_party(ctx.author.id).recognize(member.id, username)

    await member.add_roles(comrade_role)
    await ctx.send(f'{ctx.author.display_name} has recognized Comrade {username}.')


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
    if flag:
        await ctx.author.add_roles(learner_role)
        await ctx.send(f'{ctx.author.display_name} has been added to {learner_role.name}')
    else:
        await ctx.author.remove_roles(learner_role)
        await ctx.send(f'{ctx.author.display_name} has been removed from {learner_role.name}')


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
    username = member_to_username(ctx.author)
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
    await ctx.send(f"{username}'s nickname has been changed to {name}")


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

    await client.process_commands(message)


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
        await asyncio.sleep(30)
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
    await incremental_member_update()


@tasks.loop(hours=24)
async def loop_full_member_update():
    await full_member_update()


async def incremental_member_update() -> None:
    for user_id in flush_member_update_queue():
        profile = api.as_chairman().get_profile(user_id)
        await update_member_nick(profile)
        await asyncio.sleep(1)


async def full_member_update() -> None:
    profiles = api.as_chairman().get_all_profiles()
    for profile in profiles:
        await update_member_nick(profile)
        await asyncio.sleep(1)


################################################################################
# Member Renaming
################################################################################


async def update_member_nick(profile: Profile) -> None:
    guild = client.guilds[0]
    member = profile_to_member(guild, profile)
    if member is None:
        return

    if member.bot:
        return

    username = member_to_username(member)
    if username == ADMIN_USERNAME:
        return

    credit_str = f' [{profile.credit}]'
    cutoff = 32 - len(credit_str)
    new_nick = profile.display_name[:cutoff] + credit_str

    if new_nick == member.nick:
        return

    logger.info(f'Rename {member.nick} -> {new_nick}')
    await member.edit(nick=new_nick)


################################################################################
# Utils
################################################################################


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

import asyncio
import requests
import typing as t
from datetime import datetime, timedelta
from pathlib import Path

import discord
from discord.ext import commands, tasks

import os
import pymongo
from dotenv import load_dotenv

from chairmanmao.profile import get_profile, set_profile_last_message, get_all_profiles
from chairmanmao.api import Api
from chairmanmao.draw import draw, get_font_names
from chairmanmao.fourchan import get_dmt_thread, is_url_seen, see_url
from chairmanmao.types import Profile


intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='$', intents=intents)


load_dotenv()


MONGODB_URL = os.getenv('MONGODB_URL', '')
MONGODB_DB = os.getenv('MONGODB_DB', '')

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
BOT_USERNAME = os.getenv('BOT_USERNAME', '')

mongo_client = pymongo.MongoClient(MONGODB_URL)
db = mongo_client[MONGODB_DB]
api = Api.connect(MONGODB_URL, MONGODB_DB)


@client.command(name='socialcredit', help='See your social credit score.')
@commands.has_role('同志')
async def cmd_socialcredit(ctx, member: commands.MemberConverter = None):
    print(f'{ctx.author.display_name}: cmd_socialcredit({member})')
    username = member_to_username(ctx.author)

    if member is not None:
        target_username = member_to_username(member)
    else:
        target_username = username

    credit = api.as_comrade(username).social_credit(target_username)
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
    await member.add_roles(comrade_role)
    await ctx.send(f'{ctx.author.display_name} has recognized Comrade {username}.')


@client.command(name='honor', help="Add social credit to a user.")
@commands.has_role('共产党员')
@commands.is_owner()
async def cmd_honor(ctx, member: commands.MemberConverter, credit: int):
    print(f'{ctx.author.display_name}: cmd_honor({member}, {credit})')
    assert credit > 0

    username = member_to_username(ctx.author)
    target_username = member_to_username(member)
    new_credit = api.as_chairman(username).honor(target_username, credit)
    old_credit = new_credit - credit

    await ctx.send(f'{target_username} has had their credit score increased from {old_credit} to {new_credit}.')


@client.command(name='dishonor', help="Remove social credit from a user.")
@commands.has_role('共产党员')
@commands.is_owner()
async def cmd_dishonor(ctx, member: commands.MemberConverter, credit: int):
    print(f'{ctx.author.display_name}: cmd_dishonor({member}, {credit})')
    assert credit > 0

    username = member_to_username(ctx.author)
    target_username = member_to_username(member)
    new_credit = api.as_chairman(username).dishonor(target_username, credit)
    old_credit = new_credit + credit

    await ctx.send(f'{target_username} has had their credit score decreased from {old_credit} to {new_credit}.')


@client.command(name='learner', help='Add or remove 中文学习者 role.')
@commands.has_role('同志')
async def cmd_learner(ctx, flag: bool = True):
    print(f'{ctx.author.display_name}: cmd_learner({flag})')
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
    print(f'{ctx.author.display_name}: cmd_name({name})')
    member = ctx.author
    username = member_to_username(member)

    try:
        api.as_comrade(username).set_name(name)
    except:
#        await ctx.send("Names are 32 character max.")
#        return
        raise

    profile = get_profile(db, username)
    assert profile is not None
    await update_member_nick(profile)
    await ctx.send(f"{username}'s nickname has been changed to {name}")


@client.command(name='hanzi', help='Show the count and list of all hanzi a user has taken.')
@commands.has_role('同志')
async def cmd_hanzi(ctx, member: commands.MemberConverter = None):
    if member is None:
        member = ctx.author

    username = member_to_username(ctx.author)
    target_username = member_to_username(member)

    hanzi = api.as_comrade(username).get_hanzis(target_username)
    hanzi_str = ' '.join(hanzi)
    num_hanzi = len(hanzi)
    await ctx.send(f'{target_username} has {num_hanzi} hanzi: {hanzi_str}')


@client.command(name='setname', help="Sets the name of another user.")
@commands.has_role('共产党员')
@commands.is_owner()
async def cmd_setname(ctx, member: commands.MemberConverter, name: str):
    print(f'{ctx.author.display_name}: cmd_setname({member.display_name}, {name})')
    username = member_to_username(ctx.author)
    target_username = member_to_username(member)

    try:
        api.as_chairman(username).set_name(target_username, name)
    except:
#        await ctx.send("Names are 32 character max.")
#        return
        raise

    profile = get_profile(db, target_username)
    assert profile is not None
    await update_member_nick(profile)
    await ctx.send(f"{username}'s nickname has been changed to {name}")


@client.command(name='draw', help="Draw a simplified hanzi character.")
@commands.has_role('同志')
async def cmd_draw(ctx, chars: str, font: t.Optional[str] = None):
    print(f'{ctx.author.display_name}: cmd_draw({chars})')
    for char in chars:
        assert is_hanzi(char)
    image_buffer = draw(chars, font)
    if image_buffer is not None:
        filename = 'hanzi_' + '_'.join('u' + hex(ord(char))[2:] for char in chars) + '.png'
        await ctx.channel.send(file=discord.File(fp=image_buffer, filename=filename))
    else:
        await ctx.send(f"I cannot render {chars} with this font.")


@client.command(name='font')
@commands.has_role('同志')
@commands.cooldown(1, 5 * 60, type)
async def cmd_font(ctx, font_name: str):
    print(f'{ctx.author.display_name}: cmd_font({font_name})')

    if font_name == 'list':
        font_names = get_font_names()
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
    font_dir = Path('fonts')
    filename = f'{ctx.author.id}_{font_name}.ttf'
    with open(font_dir / filename, 'wb') as outfile:
        outfile.write(resp.content)

    await ctx.send(f"Uploaded font: {font_name}.")


@client.command(name='yuan')
@commands.has_role('同志')
async def cmd_yuan(ctx):
    print(f'{ctx.author.display_name}: cmd_yuan()')
    username = member_to_username(ctx.author)
    yuan = api.as_comrade(username).get_yuan()
    await ctx.send(f"{username} has {yuan} RNB.")


@client.command(name='leaderboard', help='Show the DMT leaderboard.')
@commands.has_role('同志')
@commands.cooldown(1, 5 * 60, commands.BucketType.guild)
async def cmd_leaderboard(ctx, member: commands.MemberConverter = None):
    print(f'{ctx.author.display_name}: cmd_leaderboard()')
    lines = [
        "The DMT Leaderboard",
        "```",
    ]

    username = member_to_username(ctx.author)
    for entry in api.as_comrade(username).leaderboard():
        line = f'{entry.credit} ... {entry.display_name}'
        lines.append(discord.utils.remove_markdown(line))

    lines.append("```")

    await ctx.send('\n'.join(lines))


@client.command(name='mine', help='Mine a word.')
@commands.has_role('同志')
async def cmd_mine(ctx, word: str):
    print(f'{ctx.author.display_name}: cmd_mine({word})')

    username = member_to_username(ctx.author)
    api.as_comrade(username).mine(word)

    await ctx.send(f'{username} has mined: {word}')


@client.command(name='debug')
@commands.has_role("共产党员")
@commands.is_owner()
async def cmd_debug(ctx):
    print(f'{ctx.author.display_name}: cmd_debug()')
    breakpoint()


@client.event
async def on_message(message):
    if isinstance(message.channel, discord.channel.TextChannel):
        comrade_role = discord.utils.get(message.channel.guild.roles, name='同志')
        if comrade_role in message.author.roles:
            username = member_to_username(message.author)
            api.as_comrade(username).alert_activity()

            hanzis = hanzis_in(message.content)
            api.as_comrade(username).see_hanzis(hanzis)

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
        credit = api.as_chairman(BOT_USERNAME).honor(target_username, 1)
        print(f'User reaction added to {user_to_credit}: {credit}')


@client.event
async def on_reaction_remove(reaction, user):
    user_to_credit = reaction.message.author
    if user_to_credit != user:
        target_username = member_to_username(user_to_credit)
        credit = api.as_chairman(BOT_USERNAME).dishonor(target_username, 1)
        print(f'User reaction removed from {user_to_credit}: {credit}')


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
    set_guild()
    await init_invites()

    loop_dmtthread.start()
    loop_socialcreditrename.start()


@client.event
async def on_member_join(member):
    guild = client.guilds[0]
    invite = await get_current_invite()
    print(member.name, 'joined with invite code', invite.code, 'from', member_to_username(invite.inviter))


def member_to_username(member) -> str:
    return member.name + '#' + member.discriminator


def news_channel():
    guild = client.guilds[0]
    assert guild.name == 'Daily Mandarin Thread'

    for channel in guild.channels:
        if channel.name.startswith('🧵'):
            return channel

    raise Exception()


def thread_channel():
    guild = client.guilds[0]
    assert guild.name == 'Daily Mandarin Thread'

    for channel in guild.channels:
        if channel.name.startswith('🧵'):
            return channel

    raise Exception()


@tasks.loop(seconds=60)
async def loop_dmtthread():
    thread = await get_dmt_thread()
    if thread is not None:
        if not is_url_seen(thread.url):
            print('Found DMT thread:', thread.url)
            see_url(thread.url)
            channel = thread_channel()
            lines = [
                thread.title,
                thread.url,
            ]
            await channel.send('\n'.join(lines))


def profile_to_member(guild: discord.Guild, profile: Profile) -> t.Optional[discord.Member]:
    for member in client.guilds[0].members:
        if member_to_username(member) == profile.username:
            return member
    return None


async def update_member_nick(profile: Profile):
    guild = client.guilds[0]
    member = profile_to_member(guild, profile)
    if member is None:
        return

    username = member_to_username(member)
    if username == ADMIN_USERNAME:
        return

    credit_str = f' [{profile.credit}]'
    cutoff = 32 - len(credit_str)
    new_nick = profile.display_name[:cutoff] + credit_str

    if new_nick == member.nick:
        return

    if member.bot:
        return

    print('Updating nick:')
    print('Nick:', member.nick)
    print('Disp:', member.display_name)
    print('New: ', new_nick)
    print()
    await member.edit(nick=new_nick)
    await asyncio.sleep(1)


@tasks.loop(minutes=1)
async def loop_socialcreditrename():
    profiles = get_all_profiles(db)
    for profile in profiles:
        await update_member_nick(profile)

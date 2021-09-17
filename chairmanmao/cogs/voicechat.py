import typing as t

import discord
from discord.ext import commands, tasks

from chairmanmao.types import Profile


class VoiceChatCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('VoiceChatCog')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        constants = self.chairmanmao.constants()
        guild = constants.guild
        voice_role = discord.utils.get(guild.roles, name="在声音中")
        voice_channel = discord.utils.get(guild.voice_channels, name="🎤谈话室")
        if after.channel == voice_channel:
            await member.add_roles(voice_role)
        elif after.channel is None:
            await member.remove_roles(voice_role)
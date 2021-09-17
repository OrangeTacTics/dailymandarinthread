from __future__ import annotations
from dataclasses import dataclass

import discord

@dataclass
class DiscordConstants:
    guild: discord.Guild

    comrade_role: discord.Role
    ccp_role: discord.Role
    jailed_role: discord.Role
    learner_role: discord.Role
    hsk1_role: discord.Role
    hsk2_role: discord.Role
    hsk3_role: discord.Role
    hsk4_role: discord.Role
    hsk5_role: discord.Role
    hsk6_role: discord.Role

    thread_channel: discord.TextChannel

    @staticmethod
    def load(guild) -> DiscordConstants:
        return DiscordConstants(
            guild=guild,

            comrade_role=DiscordConstants._load_role(guild, '同志'),
            ccp_role=DiscordConstants._load_role(guild, "共产党员"),
            jailed_role=DiscordConstants._load_role(guild, "劳改"),
            learner_role=DiscordConstants._load_role(guild, "中文学习者"),
            hsk1_role=DiscordConstants._load_role(guild, "HSK1"),
            hsk2_role=DiscordConstants._load_role(guild, "HSK2"),
            hsk3_role=DiscordConstants._load_role(guild, "HSK3"),
            hsk4_role=DiscordConstants._load_role(guild, "HSK4"),
            hsk5_role=DiscordConstants._load_role(guild, "HSK5"),
            hsk6_role=DiscordConstants._load_role(guild, "HSK6"),

            thread_channel=DiscordConstants._load_channel(guild, "🧵"),
        )

    @staticmethod
    def _load_role(guild: discord.Guild, name: str) -> discord.Role:
        role = discord.utils.get(guild.roles, name=name)
        assert role is not None, f'Role {name} does not exist.'
        return role

    @staticmethod
    def _load_channel(guild: discord.Guild, prefix: str) -> discord.Channel:
        for channel in guild.channels:
            if channel.name.startswith(prefix):
                return channel
        return None

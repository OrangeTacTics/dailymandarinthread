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
    bumpers_role: discord.Role

    thread_channel: discord.TextChannel
    tiananmen_channel: discord.TextChannel
    commentators_channel: discord.TextChannel
    apologies_channel: discord.TextChannel
    news_channel: discord.TextChannel
    test_channel: discord.TextChannel
    exam_channel: discord.TextChannel
    learners_channel: discord.TextChannel
    rules_channel: discord.TextChannel

    mao_emoji: discord.Emoji
    dekinai_emoji: discord.Emoji
    diesofcringe_emoji: discord.Emoji

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
            bumpers_role=DiscordConstants._load_role(guild, "Bumpers"),

            news_channel=DiscordConstants._load_channel(guild, "📰"),
            rules_channel=DiscordConstants._load_channel(guild, "🈲"),
            thread_channel=DiscordConstants._load_channel(guild, "🧵"),
            commentators_channel=DiscordConstants._load_channel(guild, "🐉"),
            learners_channel=DiscordConstants._load_channel(guild, "✍"),
            test_channel=DiscordConstants._load_channel(guild, "🏫"),
            exam_channel=DiscordConstants._load_channel(guild, "🏯"),
            apologies_channel=DiscordConstants._load_channel(guild, "⛔"),
            tiananmen_channel=DiscordConstants._load_channel(guild, "🏯"),

            mao_emoji=DiscordConstants._load_emoji(guild, "mao"),
            dekinai_emoji=DiscordConstants._load_emoji(guild, "buneng2"),
            diesofcringe_emoji=DiscordConstants._load_emoji(guild, "diesofcringe"),
        )

    @staticmethod
    def _load_role(guild: discord.Guild, name: str) -> discord.Role:
        role = discord.utils.get(guild.roles, name=name)
        assert role is not None, f'Role {name} does not exist.'
        return role

    @staticmethod
    def _load_channel(guild: discord.Guild, prefix: str) -> discord.Channel:
        found_channel = None
        for channel in guild.channels:
            if channel.name.startswith(prefix):
                found_channel = channel
                break

        assert found_channel is not None, f'Channel {prefix} does not exist.'
        return found_channel

    @staticmethod
    def _load_emoji(guild: discord.Guild, name: str) -> discord.Emoji:
        emoji = discord.utils.get(guild.emojis, name=name)
        assert emoji is not None, f'Emoji {name} does not exist.'
        return emoji

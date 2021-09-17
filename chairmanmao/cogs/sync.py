import typing as t
import os
import asyncio

from chairmanmao.types import Profile, UserId, Json, Role

import discord
from discord.ext import commands, tasks


class SyncCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('SyncCog')
        guild = self.client.guilds[0]
        self.chairmanmao.load_constants(guild)

        self.loop_incremental_member_update.start()
        #self.loop_full_member_update.start()

    @tasks.loop(seconds=1)
    async def loop_incremental_member_update(self):
        await self.chairmanmao.incremental_member_update()

    @tasks.loop(hours=24)
    async def loop_full_member_update(self):
        self.chairmanmao.logger.info('Starting full member update')
        await self.chairmanmao.full_member_update()
        self.chairmanmao.logger.info('Full member update complete')

    @commands.command(name='sync')
    @commands.has_role('共产党员')
    @commands.is_owner()
    async def  cmd_sync(self, ctx, member: commands.MemberConverter):
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send('Sync complete')

    @commands.command(name='syncall')
    @commands.has_role('共产党员')
    @commands.is_owner()
    async def  cmd_syncall(self, ctx):
        self.chairmanmao.queue_member_update(member.id)
        await self.chairmanmao.full_member_update()
        await ctx.send('Sync complete')

    async def incremental_member_update(self) -> None:
        for user_id in self.chairmanmao.flush_member_update_queue():
            profile = self.chairmanmao.api.as_chairman().get_profile(user_id)
            did_update = await self.update_member_nick(profile)
            if did_update:
                await asyncio.sleep(0.5)
            did_update = await self.update_member_roles(profile)
            if did_update:
                await asyncio.sleep(0.5)

    async def full_member_update(self) -> None:
        user_ids = self.chairmanmao.api.as_chairman().list_users()
        for user_id in user_ids:
            profile = self.chairmanmao.api.as_chairman().get_profile(user_id)
            did_update = await self.update_member_nick(profile)
            if did_update:
                await asyncio.sleep(0.5)
            did_update = await self.update_member_roles(profile)
            if did_update:
                await asyncio.sleep(0.5)

    async def update_member_roles(self, profile: Profile) -> bool:
        '''
            Return if roles updated.
        '''
        member = self.profile_to_member(profile)
        if member is None:
            return False

        current_roles = set(member.roles)

        roles_to_add = self.roles_for(profile).difference(current_roles)
        roles_to_remove = self.nonroles_for(profile).intersection(current_roles)

        if not roles_to_add and not roles_to_remove:
            return False

        await member.add_roles(*roles_to_add)
        await member.remove_roles(*roles_to_remove)

        added_roles = sorted(r.name for r in roles_to_add)
        removed_roles = sorted(r.name for r in roles_to_remove)
        self.chairmanmao.logger.info(f'Updating roles: {member.nick}: add {added_roles}, remove {removed_roles}')
        return True

    def dmt_role_to_discord_role(self, dmt_role: Role) -> discord.Role:
        constants = self.constants()

        role_map = {
            Role.Comrade: constants.comrade_role,
            Role.Party: constants.ccp_role,
            Role.Learner: constants.learner_role,
            Role.Jailed: constants.jailed_role,
            Role.Hsk1: constants.hsk1_role,
            Role.Hsk2: constants.hsk2_role,
            Role.Hsk3: constants.hsk3_role,
            Role.Hsk4: constants.hsk4_role,
            Role.Hsk5: constants.hsk5_role,
            Role.Hsk6: constants.hsk6_role,
        }

    def roles_for(self, profile: Profile) -> t.Set[discord.Role]:
        constants = self.constants()

        if profile.is_jailed():
            return {constants.jailed_role}
        else:
            discord_roles = {self.dmt_role_to_discord_role(dmt_role) for dmt_role in profile.roles}
            return discord_roles

    def nonroles_for(self, profile: Profile) -> t.Set[Role]:
        constants = self.constants()

        all_roles = {
            constants.comrade_role,
            constants.ccp_role,
            constants.jailed_role,
            constants.learner_role,
            constants.hsk1_role,
            constants.hsk2_role,
            constants.hsk3_role,
            constants.hsk4_role,
            constants.hsk5_role,
            constants.hsk6_role,
        }
        return all_roles.difference(self.roles_for(profile))

    async def update_member_nick(self, profile: Profile) -> bool:
        '''
            Return if nick updated.
        '''
        member = self.profile_to_member(profile)
        if member is None:
            return False

        if member.bot:
            return False

        constants = self.constants()
        if member.id == constants.guild.owner.id:
            return False

        new_nick = profile.nick_for()

        if new_nick == member.nick:
            return False

        self.chairmanmao.logger.info(f'Rename {member.nick} -> {new_nick}')
        await member.edit(nick=new_nick)
        return True

    def profile_to_member(self,  profile: Profile) -> t.Optional[discord.Member]:
        constants = self.constants()
        for member in constants.guild.members:
            if member.id == profile.user_id:
                return member
        return None

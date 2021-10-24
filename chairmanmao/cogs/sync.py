import typing as t
import asyncio

from chairmanmao.types import Role
from chairmanmao.cogs import ChairmanMaoCog

import discord
from discord.ext import commands, tasks

from chairmanmao.api import SyncInfo


class SyncCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("SyncCog")
        guild = self.client.guilds[0]
        self.chairmanmao.load_constants(guild)

        self.loop_incremental_member_update.start()
        # self.loop_full_member_update.start()

    @tasks.loop(seconds=1)
    async def loop_incremental_member_update(self):
        await self.incremental_member_update()

    @tasks.loop(hours=24)
    async def loop_full_member_update(self):
        self.logger.info("Starting full member update")
        await self.full_member_update()
        self.logger.info("Full member update complete")

    @commands.command(name="sync")
    @commands.is_owner()
    async def cmd_sync(self, ctx, member: commands.MemberConverter):
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send("Sync complete")

    #    @commands.command(name='syncall')
    #    @commands.is_owner()
    #    async def cmd_syncall(self, ctx):
    #        await ctx.send('Sync starting')
    #        await self.full_member_update()
    #        await ctx.send('Sync complete')

    async def incremental_member_update(self) -> None:
        constants = self.chairmanmao.constants()
        for user_id in self.chairmanmao.flush_member_update_queue():
            if not await self.api.is_registered(user_id):
                user = discord.utils.get(constants.guild.members, id=user_id)
                assert user is not None
                username = self.chairmanmao.member_to_username(user)
                await self.api.register(user_id, username)

            sync_info = await self.api.get_sync_info(user_id)
            did_update = await self.update_member_nick(sync_info)
            if did_update:
                await asyncio.sleep(0.5)
            did_update = await self.update_member_roles(sync_info)
            if did_update:
                await asyncio.sleep(0.5)

    #    async def full_member_update(self) -> None:
    #        user_ids = await self.api.list_users()
    #        for user_id in user_ids:
    #            sync_info = await self.api.get_sync_info(user_id)
    #            did_update = await self.update_member_nick(sync_info)
    #            if did_update:
    #                await asyncio.sleep(0.5)
    #            did_update = await self.update_member_roles(sync_info)
    #            if did_update:
    #                await asyncio.sleep(0.5)

    async def update_member_roles(self, sync_info: SyncInfo) -> bool:
        """
        Return if roles updated.
        """
        member = self.sync_info_to_member(sync_info)
        if member is None:
            return False

        current_roles = set(member.roles)

        roles_to_add = self.roles_for(sync_info).difference(current_roles)
        roles_to_remove = self.nonroles_for(sync_info).intersection(current_roles)

        if not roles_to_add and not roles_to_remove:
            return False

        await member.add_roles(*roles_to_add)
        await member.remove_roles(*roles_to_remove)

        added_roles = sorted(r.name for r in roles_to_add)
        removed_roles = sorted(r.name for r in roles_to_remove)
        self.logger.info(f"Updating roles: {member.nick}: add {added_roles}, remove {removed_roles}")
        return True

    def dmt_role_to_discord_role(self, dmt_role: Role) -> discord.Role:
        constants = self.chairmanmao.constants()

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
        return role_map[dmt_role]

    def roles_for(self, sync_info: SyncInfo) -> t.Set[discord.Role]:
        constants = self.chairmanmao.constants()

        if Role.Jailed in sync_info.roles:
            return {constants.jailed_role}
        else:
            discord_roles = {self.dmt_role_to_discord_role(dmt_role) for dmt_role in sync_info.roles}
            if constants.comrade_role not in discord_roles:
                discord_roles.add(constants.comrade_role)
            return discord_roles

    def nonroles_for(self, sync_info: SyncInfo) -> t.Set[Role]:
        constants = self.chairmanmao.constants()

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
        return all_roles.difference(self.roles_for(sync_info))

    async def update_member_nick(self, sync_info: SyncInfo) -> bool:
        """
        Return if nick updated.
        """
        member = self.sync_info_to_member(sync_info)
        if member is None:
            return False

        if member.bot:
            return False

        constants = self.chairmanmao.constants()
        if member.id == constants.guild.owner.id:
            return False

        new_nick = nick_for(sync_info)

        if new_nick == member.nick:
            return False

        self.logger.info(f"Rename {member.nick} -> {new_nick}")
        await member.edit(nick=new_nick)
        return True

    def sync_info_to_member(self, sync_info: SyncInfo) -> t.Optional[discord.Member]:
        constants = self.chairmanmao.constants()
        for member in constants.guild.members:
            if member.id == sync_info.user_id:
                return member
        return None


def nick_for(sync_info: SyncInfo) -> str:
    if Role.Jailed in sync_info.roles:
        return _add_label_to_nick(sync_info.display_name, "【劳改】")

    else:
        label = f" [{sync_info.credit}]"

        hsk_level = sync_info.hsk_level
        if hsk_level is not None:
            hsk_label = {
                1: "➀",
                2: "➁",
                3: "➂",
                4: "➃",
                5: "➄",
                6: "➅",
            }
            label += " HSK" + hsk_label[hsk_level]

        if Role.Learner in sync_info.roles:
            label += "✍"

        return _add_label_to_nick(sync_info.display_name, label)


def _add_label_to_nick(display_name: str, label: str) -> str:
    cutoff = 32 - len(label)
    return display_name[:cutoff] + label

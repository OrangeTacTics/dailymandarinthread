from discord.ext import commands

from dmt_chairmanmao.cogs import ChairmanMaoCog


class InvitesCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("InvitesCog")


# INVITES = {}
#
#
# async def init_invites():
#    invites = await get_guild().invites()
#    for invite in invites:
#        INVITES[invite.code] = invite
#
#
# async def get_current_invite():
#    old_invites = INVITES
#
#    new_invites = {}
#    for invite in await get_guild().invites():
#        new_invites[invite.code] = invite
#
#    for code, old_invite in old_invites.items():
#        code = old_invite.code
#        new_invite = new_invites[code]
#
#        if old_invite.uses < new_invite.uses:
#            old_invites[code] = new_invite
#            return new_invite
#
#    return None

# @client.event
# async def on_member_join(member):
#    guild = client.guilds[0]
#    invite = await get_current_invite()
#    logger.info(f'{member.name} joined with invite code {invite.code} from {member_to_username(invite.inviter)}')
#
#
# @client.event
# async def on_invite_create(member):
#    await init_invites()
#
#
# @client.event
# async def on_invite_delete(member):
#    await init_invites()

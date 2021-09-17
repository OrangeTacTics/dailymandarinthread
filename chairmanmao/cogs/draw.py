from __future__ import annotations
import typing as t
from io import BytesIO

import discord
from discord.ext import commands

import requests

from chairmanmao.hanzi import is_hanzi
from chairmanmao.cogs import ChairmanMaoCog


class DrawCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('DrawCog')

    @commands.command(name='draw', help="Draw a simplified hanzi character.")
    @commands.has_role('同志')
    async def cmd_draw(self, ctx, chars: str, font: t.Optional[str] = None):
        if font is None:
            font = 'kuaile'

        for char in chars:
            assert is_hanzi(char)

        image_buffer = self.chairmanmao.draw_manager.draw(font, chars)
        filename = 'hanzi_' + '_'.join('u' + hex(ord(char))[2:] for char in chars) + '.png'
        await ctx.channel.send(file=discord.File(fp=image_buffer, filename=filename))


    @commands.command(name='font')
    @commands.has_role('同志')
    @commands.cooldown(1, 5 * 60, type)
    async def cmd_font(self, ctx, font_name: str):
        if font_name == 'list':
            font_names = self.chairmanmao.draw_manager.get_font_names()
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
        self.chairmanmao.draw_manager.upload_font(ctx.author.id, font_name, BytesIO(resp.content))
        await ctx.send(f"Uploaded font: {font_name}.")


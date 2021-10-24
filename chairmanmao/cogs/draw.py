from __future__ import annotations
import typing as t
from io import BytesIO
import asyncio

import discord
from discord.ext import commands

import requests

from chairmanmao.cogs import ChairmanMaoCog


class DrawCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("DrawCog")

    @commands.command(name="draw", help="Draw a simplified hanzi character.")
    @commands.has_role("同志")
    async def cmd_draw(self, ctx, chars: str, font: t.Optional[str] = None):
        if font is None:
            font = "kuaile"

        await self.chairmanmao.draw_manager.draw_to_channel(ctx.channel, font, chars)

    @commands.group(name="font")
    async def font(self, ctx):
        pass

    @font.command(name="list")
    @commands.has_role("同志")
    @commands.cooldown(1, 5 * 60, type)
    async def cmd_font_list(self, ctx):
        font_names = self.chairmanmao.draw_manager.get_font_names()
        for font_name in font_names:
            await self.demo_font(font_name, ctx.channel)
            await asyncio.sleep(0.5)
        return

    @font.command(name="upload")
    @commands.has_role("同志")
    @commands.cooldown(1, 5 * 60, type)
    async def cmd_font_upload(self, ctx, font_name: str):
        if not font_name.isidentifier():
            await ctx.send(f"Please name the font with no spaces, ASCII-only, beginning with a letter")
            return

        if len(ctx.message.attachments) != 1:
            await ctx.send(f"You didn't attach a font to your message")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.url.endswith(".ttf"):
            await ctx.send(f"Your font doesn't look like a TTF font.")
            return

        resp = requests.get(attachment.url)
        self.chairmanmao.draw_manager.upload_font(ctx.author.id, font_name, BytesIO(resp.content))
        await ctx.send(f"Uploaded font:")
        await self.demo_font(font_name, ctx.channel)

    async def demo_font(self, font_name: str, channel: discord.Messageable) -> None:
        text = "我爱中国"
        image_buffer = self.chairmanmao.draw_manager.draw(font_name, text)
        filename = "hanzi_" + "_".join("u" + hex(ord(char))[2:] for char in text) + ".png"
        await channel.send(f"{font_name}:", file=discord.File(fp=image_buffer, filename=filename))

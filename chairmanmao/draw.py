from __future__ import annotations
import typing as t
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from functools import lru_cache
from shutil import copyfileobj

import discord


if t.TYPE_CHECKING:
    from chairmanmao.filemanager import FileManager
    from chairmanmao.types import UserId


class DrawManager:
    def __init__(self, file_manager: FileManager) -> None:
        self.file_manager = file_manager

    def get_font_names(self) -> t.List[str]:
        return sorted(self.get_fonts().keys())

    def get_fonts(self) -> t.Dict[str, str]:
        results = {}

        filenames = self.file_manager.list('fonts')
        for filename in filenames:
            if not filename.endswith('.ttf'):
                continue

            if '_' not in filename:
                continue

            idx = filename.index('_')
            font = filename[idx + 1:]
            font = font[:-len('.ttf')]
            results[font] = filename

        return results

    @lru_cache(maxsize=10)
    def load_font(self, font_name: str, size: int) -> ImageFont:
        fonts = self.get_fonts()
        font_key = fonts[font_name]

        temp_filename = 'temp.tff'

        with open(temp_filename, 'wb') as outfile:
            infile = self.file_manager.download(font_key)
            copyfileobj(infile, outfile)

        return ImageFont.truetype(temp_filename, size)

    def upload_font(self, user_id: UserId, font_name: str, fp: t.BinaryIO) -> None:
        filename = f'fonts/{user_id}_{font_name}.ttf'
        self.file_manager.upload(filename, fp)

    def draw(self, font_name: str, text: str, *, size: int = 128, color=(255, 0, 0)) -> BytesIO:
        font = self.load_font(font_name, size)

        image = Image.new('RGBA', (size * len(text), size))
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), text, fill=color, font=font)

        img_buffer = BytesIO()
        image.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer

    async def draw_to_channel(self, channel: discord.abc.Messageable, font_name: str, text: str, *, size: int = 128, color=(255, 0, 0)) -> None:
        image_buffer = self.draw(font_name, text, size=size, color=color)
        filename = 'hanzi_' + '_'.join('u' + hex(ord(char))[2:] for char in text) + '.png'
        await channel.send(file=discord.File(fp=image_buffer, filename=filename))

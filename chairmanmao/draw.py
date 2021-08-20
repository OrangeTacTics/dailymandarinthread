import typing as t
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from pathlib import Path


FONTS = {
    'kuaile': ImageFont.truetype("fonts/ZCOOLKuaiLe-Regular.ttf",  128),
    'senty': ImageFont.truetype("fonts/HanyiSentyCandy.ttf",  128),
}


def get_font_names():
    font_names = set(FONTS.keys())

    font_dir = Path('fonts')
    for path in font_dir.iterdir():
        if path.name == 'ZCOOLKuaiLe-Regular.ttf' or path.name == 'HanyiSentyCandy.ttf':
            continue
        font_name = str(path.name)
        try:
            underscore_idx = font_name.index('_')
            font_name = font_name[underscore_idx+1:]
        except:
            pass
        dot_idx = font_name.index('.')
        font_name = font_name[:dot_idx]
        font_names.add(font_name)

    return sorted(font_names)




def get_font(name):
    if name in FONTS:
        return FONTS[name]

    font_dir = Path('fonts')
    for path in font_dir.iterdir():
        font_name = str(path.name)
        try:
            underscore_idx = font_name.index('_')
            font_name = font_name[underscore_idx+1:]
        except:
            pass
        dot_idx = font_name.index('.')
        font_name = font_name[:dot_idx]

        print(f'{name} vs {font_name}')
        if name == font_name:
            return ImageFont.truetype(str(path), 128)

    return FONTS[DEFAULT_FONT_NAME]


DEFAULT_FONT_NAME = 'kuaile'


def draw(chars: str, font_name: t.Optional[str] = None) -> t.Optional[BytesIO]:
    if font_name is None:
        font_name = DEFAULT_FONT_NAME

    font = get_font(font_name)

    image = Image.new('RGBA', (128 * len(chars), 128))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), chars, fill=(255, 0, 0), font=font)

    img_buffer = BytesIO()
    image.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    return img_buffer

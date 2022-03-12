use std::io::Cursor;

use image::{DynamicImage, Rgba};
use rusttype::{point, Font, Scale};

pub fn load_font(font_name: &str) -> Font {
    let path = format!("data/{}", font_name);
    let font_data = std::fs::read(path).unwrap();
    let font = Font::try_from_vec(font_data).unwrap();
    font
}

pub fn draw(text: &str) -> Vec<u8> {
    let font = load_font("ZCOOL_KuaiLe.ttf");

    // The font size to use
    let scale = Scale::uniform(128.0);

    // Use a dark red colour
    let colour = (255, 0, 0);

    let v_metrics = font.v_metrics(scale);

    // layout the glyphs in a line with 20 pixels padding
    let glyphs: Vec<_> = font
        .layout(&text, scale, point(0.0, v_metrics.ascent))
        .collect();

    // work out the layout size
    let glyphs_height = (v_metrics.ascent - v_metrics.descent).ceil() as u32;
    let glyphs_width = {
        let min_x = glyphs
            .first()
            .map(|g| g.pixel_bounding_box().unwrap().min.x)
            .unwrap();
        let max_x = glyphs
            .last()
            .map(|g| g.pixel_bounding_box().unwrap().max.x)
            .unwrap();
        (max_x - min_x) as u32
    };

    // Create a new rgba image with some padding
    let mut image = DynamicImage::new_rgba8(glyphs_width + 10, glyphs_height + 10).to_rgba8();

    // Loop through the glyphs in the text, positing each one on a line
    for glyph in glyphs {
        if let Some(bounding_box) = glyph.pixel_bounding_box() {
            // Draw the glyph into the image per-pixel by using the draw closure
            glyph.draw(|x, y, v| {
                image.put_pixel(
                    // Offset the position by the glyph bounding box
                    x + bounding_box.min.x as u32,
                    y + bounding_box.min.y as u32,
                    // Turn the coverage into an alpha value
                    Rgba([colour.0, colour.1, colour.2, (v * 255.0) as u8]),
                )
            });
        }
    }

    let mut result = Cursor::new(Vec::new());
    image.write_to(&mut result, image::ImageOutputFormat::Png).unwrap();
    result.into_inner()
}

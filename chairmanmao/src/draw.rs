use crate::Error;
use std::io::Cursor;

use image::{DynamicImage, Rgba};
use rusttype::{point, Font, Scale};

pub fn load_font(font_name: &str) -> Font {
    let font_dirname = std::path::Path::new(&std::env::var("DATA_DIR").unwrap()).join("fonts");
    let font_data = std::fs::read(font_dirname.join(font_name)).unwrap();
    let font = Font::try_from_vec(font_data).unwrap();
    font
}

pub fn draw(text: &str) -> Result<Vec<u8>, Error>  {
    let font = load_font("ZCOOL_KuaiLe.ttf");

    // Use a dark red colour
    let colour = (255, 0, 0);

    // The font size to use
    let scale = Scale::uniform(128.0);

    let v_metrics = font.v_metrics(scale);

    // layout the glyphs in a line with 20 pixels padding
    let glyphs: Vec<_> = font
        .layout(&text, scale, point(0.0, v_metrics.ascent))
        .collect();

    // work out the layout size
    let glyphs_height = (v_metrics.ascent - v_metrics.descent).ceil() as u32;

    let glyphs_width = {
        let min_x = glyphs
            .first().unwrap()
            .pixel_bounding_box()
            .unwrap()
            .min
            .x;

        let max_x = glyphs
            .last().unwrap()
            .pixel_bounding_box()
            .unwrap()
            .max
            .x;

        (max_x - min_x) as u32
    };

    // Create a new rgba image with some padding
    let (image_width, image_height) = (glyphs_width + 10, glyphs_height + 10);
    let mut image = DynamicImage::new_rgba8(image_width, image_height).to_rgba8();

    // Loop through the glyphs in the text, positing each one on a line
    for glyph in glyphs {
        if let Some(bounding_box) = glyph.pixel_bounding_box() {
            // Draw the glyph into the image per-pixel by using the draw closure
            glyph.draw(|x, y, v| {
                let px = x + bounding_box.min.x as u32;
                let py = y + bounding_box.min.y as u32;
                let pv = Rgba([colour.0, colour.1, colour.2, (v * 255.0) as u8]);

                if px < image_width && py < image_height {
                    image.put_pixel(px, py, pv);
                }
            });
        }
    }

    let mut result = Cursor::new(Vec::new());
    image.write_to(&mut result, image::ImageOutputFormat::Png)?;
    Ok(result.into_inner())
}

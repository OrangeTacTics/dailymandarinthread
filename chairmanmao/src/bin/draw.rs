use std::io::Write;


fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    let text: &str = args.get(1).map(|s| s.as_str()).unwrap_or("你好");
    let data = chairmanmao::draw::draw(text);
    let mut outfile = std::fs::File::create("out.png").unwrap();
    outfile.write_all(&data).unwrap();
}

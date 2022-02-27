fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    let text: &str = args.get(1).map(|s| s.as_str()).unwrap_or("你好");
    chairmanmao::draw::draw(text);
}

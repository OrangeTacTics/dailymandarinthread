pub mod draw;
pub mod exam;
pub mod discord;
pub mod api;
pub mod command_parser;
pub mod sync;
pub mod commands;

pub type Error = Box<dyn std::error::Error + Send + Sync>;

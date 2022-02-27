use std::error::Error;
use twilight_http::Client;
use clap::{Parser, Subcommand};
use twilight_model::id::Id;

#[derive(Parser, Debug)]
struct Cli {
    #[clap(subcommand)]
    command: CliCommand,
}

#[derive(Subcommand, Debug)]
enum CliCommand {
    ListUsers,
    ListRoles,
    ListEmojis,
    RenameUser { user_id: u64, nick: Option<String> },
}


#[tokio::main]
async fn main() -> Result<(), Box<dyn Error + Send + Sync>> {
    // Initialize the tracing subscriber.
    tracing_subscriber::fmt::init();
    let command = Cli::parse().command;

    match &command {
        CliCommand::ListUsers => list_users().await,
        CliCommand::ListRoles => list_roles().await,
        CliCommand::ListEmojis => list_emojis().await,
        CliCommand::RenameUser { user_id, nick } => rename_user(*user_id, nick.as_deref()).await,
    }
}

async fn list_users() -> Result<(), Box<dyn Error + Send + Sync>> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let mut members = client.guild_members(guild_id).limit(999)?.exec().await?.model().await?;

    members.sort_by(|member1, member2| {
        let joined_1 = member1.joined_at.as_micros();
        let joined_2 = member2.joined_at.as_micros();
        joined_1.cmp(&joined_2)
    });

    println!("Members:");
    for (i, member) in members.iter().enumerate() {
        let username = format!("{}#{:04}", member.user.name, member.user.discriminator);
        let nick = match member.nick.as_ref() {
            Some(n) => n,
            None => &member.user.name,
        };
        println!("   {:>6}    {:>20}    {:32}    {}", i, member.user.id, nick, username);
    }

    Ok(())
}

async fn list_roles() -> Result<(), Box<dyn Error + Send + Sync>> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let mut roles = client.roles(guild_id).exec().await?.model().await?;

    println!("Roles:");
    for role in roles.iter() {
        println!("    {}    {}", role.id.to_string(), role.name);
    }

    Ok(())
}

async fn list_emojis() -> Result<(), Box<dyn Error + Send + Sync>> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let mut emojis = client.emojis(guild_id).exec().await?.model().await?;

    println!("Emojis:");
    for emoji in emojis.iter() {
        let emoji_id = &emoji.id.to_string();
        let url = format!("https://cdn.discordapp.com/emojis/{emoji_id}.png");
        println!("    {}    {:30}    {}", emoji_id , emoji.name, url);
    }

    Ok(())
}


async fn rename_user(user_id: u64, nick: Option<&str>) -> Result<(), Box<dyn Error + Send + Sync>> {
    let user_id = Id::new(user_id);
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;


    client.update_guild_member(guild_id, user_id)
        .nick(nick.to_owned())?
        .exec().await?
        .model().await?;

    Ok(())
}

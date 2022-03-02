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
    ListNoRoleUsers,
    ListRoles,
    ListEmojis,
    ListChannels,
    ListConstants,
    RenameUser { user_id: u64, nick: Option<String> },
    ChannelHistory { channel_id: u64 },
}


#[tokio::main]
async fn main() -> Result<(), Box<dyn Error + Send + Sync>> {
    // Initialize the tracing subscriber.
    tracing_subscriber::fmt::init();
    let command = Cli::parse().command;

    match &command {
        CliCommand::ListUsers => list_users().await,
        CliCommand::ListNoRoleUsers => list_no_role_users().await,
        CliCommand::ListRoles => list_roles().await,
        CliCommand::ListEmojis => list_emojis().await,
        CliCommand::ListChannels => list_channels().await,
        CliCommand::ListConstants => list_constants().await,
        CliCommand::RenameUser { user_id, nick } => rename_user(*user_id, nick.as_deref()).await,
        CliCommand::ChannelHistory { channel_id } => channel_history(*channel_id).await,
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

async fn list_no_role_users() -> Result<(), Box<dyn Error + Send + Sync>> {
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

    println!("Members without roles:");
    for (i, member) in members.iter().enumerate() {
        if member.roles.is_empty() {
            let username = format!("{}#{:04}", member.user.name, member.user.discriminator);
            let nick = match member.nick.as_ref() {
                Some(n) => n,
                None => &member.user.name,
            };
            println!("   {:>6}    {:>20}    {:32}    {}", i, member.user.id, nick, username);
        }
    }

    Ok(())
}

async fn list_roles() -> Result<(), Box<dyn Error + Send + Sync>> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let roles = client.roles(guild_id).exec().await?.model().await?;

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

    let emojis = client.emojis(guild_id).exec().await?.model().await?;

    println!("Emojis:");
    for emoji in emojis.iter() {
        let emoji_id = &emoji.id.to_string();
        let url = format!("https://cdn.discordapp.com/emojis/{emoji_id}.png");
        println!("    {}    {:30}    {}", emoji_id , emoji.name, url);
    }

    Ok(())
}

async fn list_channels() -> Result<(), Box<dyn Error + Send + Sync>> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let channels = client.guild_channels(guild_id).exec().await?.model().await?;

    println!("Channels:");
    for channel in channels.iter() {
        println!("    {}    {}", channel.id() , channel.name());
    }

    Ok(())
}

async fn list_constants() -> Result<(), Box<dyn Error + Send + Sync>> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let constants = chairmanmao::discord::DiscordConstants::load(&client).await?;
    dbg!(constants);

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

async fn channel_history(channel_id: u64) -> Result<(), Box<dyn Error + Send + Sync>> {
    let channel_id = Id::new(channel_id);
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let mut messages = client.channel_messages(channel_id)
        .limit(100)?
        .exec().await?
        .model().await?;

    let mut num_messages_fetched = messages.len();

    while num_messages_fetched < 300 {
        if !messages.is_empty() {
            for message in messages.iter() {
                let author = format!(
                    "{}({}#{:04})",
                    message.author.id.to_string(),
                    message.author.name,
                    message.author.discriminator,
                );

                println!("    {}    {:50}    {:?}", message.id.to_string(), author, message.content);
            }

            let first_message_id = messages[0].id;
            messages = client.channel_messages(channel_id)
                .limit(100)?
                .before(first_message_id)
                .exec().await?
                .model().await?;

            num_messages_fetched += messages.len();
        } else {
            break;
        }
    }

    Ok(())
}

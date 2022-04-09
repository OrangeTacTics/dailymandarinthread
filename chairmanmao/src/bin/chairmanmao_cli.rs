use std::io::Write;
use chairmanmao::Error;
use twilight_http::Client;
use clap::{Parser, Subcommand};
use twilight_model::id::Id;
use chairmanmao::api::Api;

#[derive(Parser, Debug)]
struct Cli {
    #[clap(subcommand)]
    command: CliCommand,
}

#[derive(Subcommand, Debug)]
enum CliCommand {
    ListUsers,
    ListUnregisteredUsers,
    ListNoRoleUsers,
    ListRoles,
    ListEmojis,
    ListChannels,
    ListActiveThreads,
    ListConstants,
    RenameUser { user_id: u64, nick: Option<String> },
    ChannelHistory { channel_id: u64 },
    CreateCommands,
    DownloadEmojis,
    SendMessage { channel_id: u64, message: String },
}


#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize the tracing subscriber.
    tracing_subscriber::fmt::init();
    let command = Cli::parse().command;

    match &command {
        CliCommand::ListUsers => list_users().await,
        CliCommand::ListUnregisteredUsers => list_unregistered_users().await,
        CliCommand::ListNoRoleUsers => list_no_role_users().await,
        CliCommand::ListRoles => list_roles().await,
        CliCommand::ListEmojis => list_emojis().await,
        CliCommand::ListChannels => list_channels().await,
        CliCommand::ListActiveThreads => list_threads().await,
        CliCommand::ListConstants => list_constants().await,
        CliCommand::RenameUser { user_id, nick } => rename_user(*user_id, nick.as_deref()).await,
        CliCommand::ChannelHistory { channel_id } => channel_history(*channel_id).await,
        CliCommand::CreateCommands => create_commands().await,
        CliCommand::DownloadEmojis => download_emojis().await,
        CliCommand::SendMessage { channel_id, message } => send_message(*channel_id, message).await,
    }
}

async fn list_users() -> Result<(), Error> {
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

async fn list_unregistered_users() -> Result<(), Error> {
    let api = Api::new().await;
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

    println!("Members who are not registered:");
    for (i, member) in members.iter().enumerate() {
        let user_id = member.user.id;
        if !api.profile_exists(user_id.get()).await? {
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

async fn list_no_role_users() -> Result<(), Error> {
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

async fn list_roles() -> Result<(), Error> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let mut roles = client.roles(guild_id).exec().await?.model().await?;
    roles.sort_by(|role1, role2| {
        role2.position.cmp(&role1.position)
    });

    println!("Roles:");
    for role in roles.iter() {
        println!("    {}    {}", role.id.to_string(), role.name);
    }

    Ok(())
}

async fn list_emojis() -> Result<(), Error> {
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

async fn download_emojis() -> Result<(), Error> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let emojis = client.emojis(guild_id).exec().await?.model().await?;

    let dirname = std::path::Path::new("./data/emojis/");
    std::fs::create_dir_all(&dirname)?;

    println!("Emojis:");
    for emoji in emojis.iter() {
        let emoji_id = &emoji.id.to_string();
        let url = format!("https://cdn.discordapp.com/emojis/{emoji_id}.png");

        let body = reqwest::get(&url)
            .await?
            .bytes()
            .await?;


        let filename = dirname.join(&format!("{}_{}.png", emoji_id, emoji.name));
        let mut file = std::fs::File::create(&filename)?;
        file.write(&body)?;

        println!("    {}    {:30}    {}", emoji_id , emoji.name, filename.to_str().ok_or("")?);
    }

    Ok(())
}

async fn list_channels() -> Result<(), Error> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let channels = client.guild_channels(guild_id).exec().await?.model().await?;

    println!("Channels:");
    for channel in channels.iter() {
        println!("    {}    {}", channel.id , channel.name.as_ref().unwrap_or(&"".to_string()));
    }

    Ok(())
}

async fn list_threads() -> Result<(), Error> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let threads = client.active_threads(guild_id).exec().await?.model().await?;

    println!("Threads:");
    for thread in threads.threads.iter() {
        println!("    {}    {}", thread.id , thread.name.as_ref().unwrap_or(&"".to_string()));
    }

    Ok(())
}

async fn list_constants() -> Result<(), Error> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let constants = chairmanmao::discord::DiscordConstants::load(&client).await?;
    dbg!(constants);

    Ok(())
}

async fn rename_user(user_id: u64, nick: Option<&str>) -> Result<(), Error> {
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

async fn channel_history(channel_id: u64) -> Result<(), Error> {
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

async fn create_commands() -> Result<(), Error> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let constants = chairmanmao::discord::DiscordConstants::load(&client).await?;

    let application_id = {
        let response = client.current_user_application().exec().await?;
        response.model().await?.id
    };

    println!("Application ID: {application_id}");

    let interaction_client = client
        .interaction(application_id);

    let commands = chairmanmao::commands::create_commands(guild_id, &interaction_client, constants).await?;

    let command_list = interaction_client
        .set_guild_commands(
            guild_id,
            &commands.commands(),
        )
        .exec()
        .await?
        .models()
        .await?;

    interaction_client.set_command_permissions(
        guild_id,
        commands.command_id_permission().as_slice(),
    )
        .unwrap()
        .exec()
        .await?;

    println!("Commands:");
    for command in &command_list {
        println!("    {:20} {}", command.name, command.description);
    }


    Ok(())
}

async fn send_message(channel_id: u64, message: &str) -> Result<(), Error> {
    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    client.create_message(Id::new(channel_id))
        .content(message)?
        .exec().await?;

    Ok(())
}

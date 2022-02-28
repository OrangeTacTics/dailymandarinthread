use futures_util::StreamExt;
use std::{env, error::Error};
use twilight_gateway::{Intents, Shard};
use twilight_model::gateway::event::Event;
use twilight_http::Client;

use twilight_model::id::Id;
use twilight_model::id::marker::RoleMarker;
use twilight_model::guild::Role;

fn get_role_id(roles: &[Role], role_name: &str) -> Id<RoleMarker> {
    for role in roles {
        if role.name == role_name {
            return role.id;
        }
    }
    panic!("Role {} not found", &role_name);
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error + Send + Sync>> {
    // Initialize the tracing subscriber.
    tracing_subscriber::fmt::init();

    let intents =
        Intents::GUILD_MESSAGES |
        Intents::GUILD_MESSAGE_REACTIONS |
        Intents::DIRECT_MESSAGES |
        Intents::GUILD_VOICE_STATES |
        Intents::GUILDS |
        Intents::GUILD_MEMBERS;


    let token = env::var("DISCORD_TOKEN")?;
    let (shard, mut events) = Shard::new(token.clone(), intents);
    let client = Client::new(token);


    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let roles = client.roles(guild_id).exec().await?.model().await?;
    let comrade_role_id = get_role_id(&roles, "同志");

    shard.start().await?;
    println!("Created shard");

    while let Some(event) = events.next().await {
        match &event {
            Event::MessageCreate(e) => {
                let message = &e.0;
                let author = &message.author;
                let timestamp = message.timestamp.as_secs();
                println!("{}({}#{:04})    {}    {}", author.id.to_string(), author.name, author.discriminator, timestamp, message.content);
                dbg!(&message);
            },
            Event::GatewayHeartbeatAck => (),
            Event::MemberAdd(e) => {
                let member = &e.0;
                println!("Attempting to add role {} to user {} in guild {}", comrade_role_id, member.user.id, guild_id);
                client.add_guild_member_role(guild_id, member.user.id, comrade_role_id).exec().await?;
            },
            Event::ReactionAdd(e) => {
                let reaction = &e.0;
                let user = reaction.member.as_ref().map(|member| format!("{}#{:04}", member.user.name, member.user.discriminator));
                println!("Reaction Added {:?} {:?} to {:?}", user, reaction.emoji, reaction.message_id);
            },
            Event::ReactionRemove(e) => {
                let reaction = &e.0;
                let user = reaction.member.as_ref().map(|member| format!("{}#{:04}", member.user.name, member.user.discriminator));
                println!("Reaction Removed {:?} {:?} to {:?}", user, reaction.emoji, reaction.message_id);
            },
            _ => {
                println!("{:?}", event.kind());
                ()
            },
        }
    }

    Ok(())
}

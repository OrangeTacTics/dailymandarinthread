use futures_util::StreamExt;
use std::{env, error::Error};
use twilight_gateway::{Intents, Shard};
use twilight_model::gateway::event::Event;
use twilight_http::Client;
use chairmanmao::discord::DiscordConstants;

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
    let constants = DiscordConstants::load(&client).await?;

    shard.start().await?;
    println!("Connected: {:?}", &constants.guild.name);

    while let Some(event) = events.next().await {
        match &event {
            Event::MessageCreate(e) => {
                let message = &e.0;
                let author = &message.author;
                let timestamp = message.timestamp.as_secs();
                println!("{}({}#{:04})    {}    {}", author.id.to_string(), author.name, author.discriminator, timestamp, message.content);
            },
            Event::GatewayHeartbeatAck => (),
            Event::MemberAdd(e) => {
                let member = &e.0;
                println!("Attempting to add role {} to user {} in guild {}", constants.comrade_role.id, member.user.id, constants.guild.id);
                client.add_guild_member_role(constants.guild.id, member.user.id, constants.comrade_role.id).exec().await?;
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
        chairmanmao::cogs::welcome::on_event(&client, &event).await;
        chairmanmao::cogs::social_credit::on_event(&client, &event).await;
        chairmanmao::cogs::jail::on_event(&client, &event).await;
    }

    Ok(())
}

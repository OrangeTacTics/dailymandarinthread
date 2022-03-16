pub mod cogs;

use std::borrow::Borrow;
use tokio::sync::Mutex;
use std::sync::Arc;

use futures_util::StreamExt;
use std::{env, error::Error};
use twilight_gateway::{Intents, Shard};
use twilight_http::Client;
use chairmanmao::discord::DiscordConstants;
use twilight_gateway::shard::Events;
use twilight_model::gateway::event::Event;
use twilight_model::id::{Id, marker::UserMarker};

use chairmanmao::api::Api;

#[derive(Debug)]
pub enum PendingSync {
    UpdateNick(Id<UserMarker>),
}

#[derive(Debug, Clone)]
pub struct ChairmanMao {
    client: Arc<Client>,
    api: Api,
    constants: DiscordConstants,
    pending_syncs: Arc<Mutex<Vec<PendingSync>>>,
    shard_events: Arc<Mutex<Events>>,
}

impl ChairmanMao {
    pub async fn connect() -> Result<ChairmanMao, Box<dyn Error + Send + Sync>> {
        let intents =
            Intents::GUILD_MESSAGES |
            Intents::GUILD_MESSAGE_REACTIONS |
            Intents::DIRECT_MESSAGES |
            Intents::GUILD_VOICE_STATES |
            Intents::GUILDS |
            Intents::GUILD_MEMBERS;

        let token = env::var("DISCORD_TOKEN")?;

        let api = Api::new().await;

        let client = Arc::new(Client::new(token.clone()));
        let (shard, shard_events) = Shard::new(token, intents);

        shard.start().await?;

        let constants = DiscordConstants::load(&client).await?;

        Ok(ChairmanMao {
            api,
            client,
            constants,
            shard_events: Arc::new(Mutex::new(shard_events)),
            pending_syncs: Arc::new(Mutex::new(vec![])),
        })
    }

    pub fn client(&self) -> &Client {
        self.client.borrow()
    }

    pub fn api(&self) -> &Api {
        &self.api
    }

    pub fn constants(&self) -> &DiscordConstants {
        &self.constants
    }

    pub async fn next_event(&self) -> Option<Event> {
        self.shard_events.lock().await.next().await
    }

    pub async fn push_nick_change(&self, user_id: Id<UserMarker>) {
        let mut pending_syncs = self.pending_syncs.lock().await;
        let sync = PendingSync::UpdateNick(user_id);
        pending_syncs.push(sync);

    }

    pub async fn has_pending_syncs(&self) -> bool {
        let pending_syncs = self.pending_syncs.lock().await;
        pending_syncs.len() > 0
    }

    pub async fn pop_all_syncs(&self) -> Vec<PendingSync> {
        let mut pending_syncs = self.pending_syncs.lock().await;
        let mut result = Vec::new();
        std::mem::swap(&mut *pending_syncs, &mut result);
        result
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error + Send + Sync>> {
    let chairmanmao = ChairmanMao::connect().await?;

    let h1 = tokio::spawn(event_loop(chairmanmao.clone()));
    let h2 = tokio::spawn(sync_loop(chairmanmao));

    h2.await?;
    h1.await?;

    Ok(())
}

async fn event_loop(chairmanmao: ChairmanMao) {
    while let Some(event) = chairmanmao.next_event().await {
        let t = tokio::spawn(handle_event(chairmanmao.clone(), event));
        if let Err(e) = t.await {
            println!("Error: {:?}", e);
        }
    }
}

async fn handle_event(chairmanmao: ChairmanMao, event: Event) -> Result<(), Box<dyn Error + Send + Sync>> {
    match &event {
        Event::Ready(_e) => {
            let channel_id = chairmanmao.constants().tiananmen_channel.id();
            chairmanmao.client().create_message(channel_id)
                .content(&format!("<@{}> is online", chairmanmao.constants().bot_user.id)).unwrap()
                .exec()
                .await
                .unwrap();
        },
        Event::MessageCreate(e) => {
            let message = &e.0;
            let author = &message.author;
            let timestamp = message.timestamp.as_secs();
            println!("{}({}#{:04})    {}    {}", author.id.to_string(), author.name, author.discriminator, timestamp, message.content);
        },
        Event::GatewayHeartbeatAck => (),
        Event::MemberAdd(e) => {
            let member = &e.0;
            chairmanmao.push_nick_change(member.user.id).await;
//                println!("Attempting to add role {} to user {} in guild {}", constants.comrade_role.id, member.user.id, constants.guild.id);
//                chairmanmao.client().add_guild_member_role(constants.guild.id, member.user.id, constants.comrade_role.id).exec().await?;
        },
        Event::ReactionAdd(e) => {
            let reaction = &e.0;
            let user = reaction.member.as_ref().map(|member| format!("{}#{:04}", member.user.name, member.user.discriminator));
            println!("Reaction Added {:?} {:?} to {:?}", user, reaction.emoji, reaction.message_id);
            let message = chairmanmao.client().message(reaction.channel_id, reaction.message_id).exec().await?.model().await?;
            if reaction.user_id != message.author.id {
                println!("Honor by 1: {}", message.author.id.get());
                chairmanmao.api().honor(message.author.id.get(), 1).await?;
                chairmanmao.push_nick_change(message.author.id).await;
            }
        },
        Event::ReactionRemove(e) => {
            let reaction = &e.0;
            let user = reaction.member.as_ref().map(|member| format!("{}#{:04}", member.user.name, member.user.discriminator));
            println!("Reaction Removed {:?} {:?} to {:?}", user, reaction.emoji, reaction.message_id);
            let message = chairmanmao.client().message(reaction.channel_id, reaction.message_id).exec().await?.model().await?;
            if reaction.user_id != message.author.id {
                chairmanmao.api().honor(message.author.id.get(), -1).await?;
                chairmanmao.push_nick_change(message.author.id).await;
            }
        },
        _ => {
            println!("{:?}", event.kind());
            ()
        },
    }
    cogs::welcome::on_event(&chairmanmao.client(), &event).await;
    cogs::social_credit::on_event(&chairmanmao.client(), &event).await;
    cogs::jail::on_event(&chairmanmao, &event).await;

    Ok(())
}


async fn sync_loop(chairmanmao: ChairmanMao) {
    loop {
        let t = tokio::spawn(do_sync(chairmanmao.clone()));
        if let Err(e) = t.await {
            println!("ERROR: {:?}", e);
        }
        tokio::time::sleep(std::time::Duration::from_millis(100)).await;
    }
}

async fn do_sync(chairmanmao: ChairmanMao) -> Result<(), Box<dyn Error + Send + Sync>> {
    if chairmanmao.has_pending_syncs().await {
        println!("Has pending syncs:");
        for pending_sync in &chairmanmao.pop_all_syncs().await {
            println!("{:?}", pending_sync);
            match pending_sync {
                PendingSync::UpdateNick(user_id) => {
                    let guild_id = chairmanmao.constants().guild.id;
                    let nick: Option<String> = chairmanmao.api().get_nick(user_id.get()).await?;

                    chairmanmao.client().update_guild_member(guild_id, *user_id)
                        .nick(nick.as_deref())?
                        .exec()
                        .await?;
                    println!("Update user {} to {:?}", user_id.to_string(), nick);

                    // TODO: This is a hack to prevent rate-limiting.
                    tokio::time::sleep(std::time::Duration::from_millis(100)).await;
                },
            }
        }
    }
    Ok(())
}

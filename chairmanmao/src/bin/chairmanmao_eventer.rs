use std::borrow::Borrow;
use tokio::sync::Mutex;
use std::sync::Arc;

use futures_util::StreamExt;
use std::env;
use twilight_gateway::{Intents, Shard};
use twilight_http::Client;
use twilight_gateway::shard::Events;
use twilight_model::gateway::event::Event;

use chairmanmao::Error;


#[derive(Clone)]
pub struct ChairmanMao {
    client: Arc<Client>,
    shard_events: Arc<Mutex<Events>>,
    redis: Arc<Mutex<redis::Connection>>,
}

impl ChairmanMao {
    pub async fn connect() -> Result<ChairmanMao, Error> {
        let intents =
            Intents::DIRECT_MESSAGES |
            Intents::GUILDS |
            Intents::GUILD_MEMBERS |
            Intents::GUILD_MESSAGES |
            Intents::GUILD_MESSAGE_REACTIONS |
            Intents::GUILD_VOICE_STATES |
            Intents::MESSAGE_CONTENT;

        let token = env::var("DISCORD_TOKEN")?;

        let redis = Arc::new(Mutex::new(redis::Client::open("redis://127.0.0.1/")?.get_connection()?));

        let client = Arc::new(Client::new(token.clone()));
        let (shard, shard_events) = Shard::new(token, intents).await?;

        let shard_events = Arc::new(Mutex::new(shard_events));

        shard.start().await?;

        Ok(ChairmanMao {
            client,
            shard_events,
            redis,
        })
    }

    pub fn client(&self) -> &Client {
        self.client.borrow()
    }

    pub async fn next_event(&self) -> Option<Event> {
        self.shard_events.lock().await.next().await
    }
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    let chairmanmao = ChairmanMao::connect().await?;

    loop {
        if let Some(event) = chairmanmao.next_event().await {
            handle_event(&chairmanmao, event).await?;
        }
    }
}


async fn handle_event(chairmanmao: &ChairmanMao, event: Event) -> Result<(), Error> {
    match &event {
        Event::GatewayHeartbeatAck => (),
        _ => {
//            println!("{:?}", event.kind());
            if let Some(json_event) = serialize_to_json(&event)? {
                println!("{}", json_event);
                let mut redis = chairmanmao.redis.lock().await;
                redis::cmd("XADD")
                    .arg("events")
                    .arg("*")
                    .arg("type")
                    .arg(format!("{:?}", event.kind()))
                    .arg("payload")
                    .arg(json_event)
                    .query(&mut *redis)?;
            }
            ()
        },
    }

    Ok(())
}


fn serialize<T: serde::Serialize>(t: &T) -> Result<Option<String>, Error> {
    match serde_json::to_string(t) {
        Ok(ok) => Ok(Some(ok)),
        Err(err) => Err(Box::new(err)),
    }
}

fn serialize_to_json(event: &Event) -> Result<Option<String>, Error> {
    match event {
        Event::BanAdd(ban_add) => serialize(ban_add),
        Event::BanRemove(ban_remove) => serialize(ban_remove),
        Event::ChannelCreate(channel_create) => serialize(channel_create),
        Event::ChannelDelete(channel_delete) => serialize(channel_delete),
        Event::ChannelPinsUpdate(channel_pins_update) => serialize(channel_pins_update),
        Event::ChannelUpdate(channel_update) => serialize(channel_update),
        Event::CommandPermissionsUpdate(command_permissions_update) => serialize(command_permissions_update),
        Event::GuildCreate(guild_create) => serialize(guild_create),
        Event::GuildDelete(guild_delete) => serialize(guild_delete),
        Event::GuildEmojisUpdate(guild_emojis_update) => serialize(guild_emojis_update),
        Event::GuildScheduledEventCreate(guild_scheduled_event_create) => serialize(guild_scheduled_event_create),
        Event::GuildScheduledEventDelete(guild_scheduled_event_delete) => serialize(guild_scheduled_event_delete),
        Event::GuildScheduledEventUpdate(guild_scheduled_event_update) => serialize(guild_scheduled_event_update),
        Event::GuildScheduledEventUserAdd(guild_scheduled_event_user_add) => serialize(guild_scheduled_event_user_add),
        Event::GuildScheduledEventUserRemove(guild_scheduled_event_user_remove) => serialize(guild_scheduled_event_user_remove),
        Event::GuildStickersUpdate(guild_sticker_update) => serialize(guild_sticker_update),
        Event::GuildUpdate(guild_update) => serialize(guild_update),
        Event::InteractionCreate(interaction_create) => serialize(interaction_create),
        Event::InviteCreate(invite_create) => serialize(invite_create),
        Event::InviteDelete(invite_delete) => serialize(invite_delete),
        Event::MemberAdd(member_add) => serialize(member_add),
        Event::MemberRemove(member_remove) => serialize(member_remove),
        Event::MemberUpdate(member_update) => serialize(member_update),
        Event::MemberChunk(member_chunk) => serialize(member_chunk),
        Event::MessageCreate(message_create) => serialize(message_create),
        Event::MessageDelete(message_delete) => serialize(message_delete),
        Event::MessageDeleteBulk(message_delete_bulk) => serialize(message_delete_bulk),
        Event::MessageUpdate(message_update) => serialize(message_update),
        Event::PresenceUpdate(presence_update) => serialize(presence_update),
        Event::ReactionAdd(reaction_add) => serialize(reaction_add),
        Event::ReactionRemove(reaction_remove) => serialize(reaction_remove),
        Event::ReactionRemoveAll(reaction_remove_all) => serialize(reaction_remove_all),
        Event::ReactionRemoveEmoji(reaction_remove_emoji) => serialize(reaction_remove_emoji),
        Event::Ready(ready) => serialize(ready),
        Event::RoleCreate(role_create) => serialize(role_create),
        Event::RoleDelete(role_delete) => serialize(role_delete),
        Event::RoleUpdate(role_update) => serialize(role_update),
        Event::ThreadCreate(thread_create) => serialize(thread_create),
        Event::ThreadDelete(thread_delete) => serialize(thread_delete),
        Event::ThreadListSync(thread_list_sync) => serialize(thread_list_sync),
        Event::ThreadMemberUpdate(thread_member_update) => serialize(thread_member_update),
        Event::ThreadMembersUpdate(thread_members_update) => serialize(thread_members_update),
        Event::ThreadUpdate(thread_update) => serialize(thread_update),
        Event::TypingStart(typing_start) => serialize(typing_start),
        Event::UserUpdate(user_update) => serialize(user_update),
        Event::VoiceServerUpdate(voice_server_update) => serialize(voice_server_update),
        Event::VoiceStateUpdate(voice_state_update) => serialize(voice_state_update),

//        Event::GatewayHeartbeat(u64) =>
//        Event::GatewayHeartbeatAck =>
//        Event::GatewayHello(u64) =>
//        Event::GatewayInvalidateSession(bool) =>
//        Event::GatewayReconnect =>
//        Event::GiftCodeUpdate =>
//        Event::GuildIntegrationsUpdate(GuildIntegrationsUpdate) =>
//        Event::IntegrationCreate(Box<IntegrationCreate>
//        Event::IntegrationDelete(IntegrationDelete) =>
//        Event::IntegrationUpdate(Box<IntegrationUpdate>
//        Event::PresencesReplace =>
//        Event::Resumed =>
//        Event::ShardConnected(Connected) =>
//        Event::ShardConnecting(Connecting) =>
//        Event::ShardDisconnected(Disconnected) =>
//        Event::ShardIdentifying(Identifying) =>
//        Event::ShardReconnecting(Reconnecting) =>
//        Event::ShardPayload(Payload) =>
//        Event::ShardResuming(Resuming) =>
//        Event::StageInstanceCreate(StageInstanceCreate) =>
//        Event::StageInstanceDelete(StageInstanceDelete) =>
//        Event::StageInstanceUpdate(StageInstanceUpdate) =>
//        Event::UnavailableGuild(UnavailableGuild) =>
//        Event::WebhooksUpdate(WebhooksUpdate) =>

        _ => Ok(None),
    }
}

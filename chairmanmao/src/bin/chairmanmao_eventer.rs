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

    let h1 = tokio::spawn(event_loop(chairmanmao.clone()));
    h1.await?;

    Ok(())
}

async fn event_loop(chairmanmao: ChairmanMao) {
    loop {
        if let Some(event) = chairmanmao.next_event().await {
            handle_event(&chairmanmao, event).await.unwrap();
        }
    }
}

async fn handle_event(chairmanmao: &ChairmanMao, event: Event) -> Result<(), Error> {
    match &event {
        Event::GatewayHeartbeatAck => (),
        _ => {
//            println!("{:?}", event.kind());
            if let Some(json_event) = serialize_to_json(&event) {
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


fn serialize_to_json(event: &Event) -> Option<String> {
    match event {
        Event::BanAdd(ban_add) => Some(serde_json::to_string(ban_add).unwrap()),
        Event::BanRemove(ban_remove) => Some(serde_json::to_string(ban_remove).unwrap()),
        Event::ChannelCreate(channel_create) => Some(serde_json::to_string(channel_create).unwrap()),
        Event::ChannelDelete(channel_delete) => Some(serde_json::to_string(channel_delete).unwrap()),
        Event::ChannelPinsUpdate(channel_pins_update) => Some(serde_json::to_string(channel_pins_update).unwrap()),
        Event::ChannelUpdate(channel_update) => Some(serde_json::to_string(channel_update).unwrap()),
        Event::CommandPermissionsUpdate(command_permissions_update) => Some(serde_json::to_string(command_permissions_update).unwrap()),
//        Event::GatewayHeartbeat(u64) => Some(serde_json::to_string(.).unwrap()),
//        Event::GatewayHeartbeatAck => Some(serde_json::to_string(.).unwrap()),
//        Event::GatewayHello(u64) => Some(serde_json::to_string(.).unwrap()),
//        Event::GatewayInvalidateSession(bool) => Some(serde_json::to_string(.).unwrap()),
//        Event::GatewayReconnect => Some(serde_json::to_string(.).unwrap()),
//        Event::GiftCodeUpdate => Some(serde_json::to_string(.).unwrap()),
        Event::GuildCreate(guild_create) => Some(serde_json::to_string(guild_create).unwrap()),
        Event::GuildDelete(guild_delete) => Some(serde_json::to_string(guild_delete).unwrap()),
        Event::GuildEmojisUpdate(guild_emojis_update) => Some(serde_json::to_string(guild_emojis_update).unwrap()),
//        Event::GuildIntegrationsUpdate(GuildIntegrationsUpdate) => Some(serde_json::to_string(.).unwrap()),
        Event::GuildScheduledEventCreate(guild_scheduled_event_create) => Some(serde_json::to_string(guild_scheduled_event_create).unwrap()),
        Event::GuildScheduledEventDelete(guild_scheduled_event_delete) => Some(serde_json::to_string(guild_scheduled_event_delete).unwrap()),
        Event::GuildScheduledEventUpdate(guild_scheduled_event_update) => Some(serde_json::to_string(guild_scheduled_event_update).unwrap()),
        Event::GuildScheduledEventUserAdd(guild_scheduled_event_user_add) => Some(serde_json::to_string(guild_scheduled_event_user_add).unwrap()),
        Event::GuildScheduledEventUserRemove(guild_scheduled_event_user_remove) => Some(serde_json::to_string(guild_scheduled_event_user_remove).unwrap()),
        Event::GuildStickersUpdate(guild_sticker_update) => Some(serde_json::to_string(guild_sticker_update).unwrap()),
        Event::GuildUpdate(guild_update) => Some(serde_json::to_string(guild_update).unwrap()),
//        Event::IntegrationCreate(Box<IntegrationCreate>) => Some(serde_json::to_string(.).unwrap()),
//        Event::IntegrationDelete(IntegrationDelete) => Some(serde_json::to_string(.).unwrap()),
//        Event::IntegrationUpdate(Box<IntegrationUpdate>) => Some(serde_json::to_string(.).unwrap()),
        Event::InteractionCreate(interaction_create) => Some(serde_json::to_string(interaction_create).unwrap()),
        Event::InviteCreate(invite_create) => Some(serde_json::to_string(invite_create).unwrap()),
        Event::InviteDelete(invite_delete) => Some(serde_json::to_string(invite_delete).unwrap()),
        Event::MemberAdd(member_add) => Some(serde_json::to_string(member_add).unwrap()),
        Event::MemberRemove(member_remove) => Some(serde_json::to_string(member_remove).unwrap()),
        Event::MemberUpdate(member_update) => Some(serde_json::to_string(member_update).unwrap()),
        Event::MemberChunk(member_chunk) => Some(serde_json::to_string(member_chunk).unwrap()),
        Event::MessageCreate(message_create) => Some(serde_json::to_string(message_create).unwrap()),
        Event::MessageDelete(message_delete) => Some(serde_json::to_string(message_delete).unwrap()),
        Event::MessageDeleteBulk(message_delete_bulk) => Some(serde_json::to_string(message_delete_bulk).unwrap()),
        Event::MessageUpdate(message_update) => Some(serde_json::to_string(message_update).unwrap()),
        Event::PresenceUpdate(presence_update) => Some(serde_json::to_string(presence_update).unwrap()),
//        Event::PresencesReplace => Some(serde_json::to_string(.).unwrap()),
        Event::ReactionAdd(reaction_add) => Some(serde_json::to_string(reaction_add).unwrap()),
        Event::ReactionRemove(reaction_remove) => Some(serde_json::to_string(reaction_remove).unwrap()),
        Event::ReactionRemoveAll(reaction_remove_all) => Some(serde_json::to_string(reaction_remove_all).unwrap()),
        Event::ReactionRemoveEmoji(reaction_remove_emoji) => Some(serde_json::to_string(reaction_remove_emoji).unwrap()),
        Event::Ready(ready) => Some(serde_json::to_string(ready).unwrap()),
//        Event::Resumed => Some(serde_json::to_string(.).unwrap()),
        Event::RoleCreate(role_create) => Some(serde_json::to_string(role_create).unwrap()),
        Event::RoleDelete(role_delete) => Some(serde_json::to_string(role_delete).unwrap()),
        Event::RoleUpdate(role_update) => Some(serde_json::to_string(role_update).unwrap()),
//        Event::ShardConnected(Connected) => Some(serde_json::to_string(.).unwrap()),
//        Event::ShardConnecting(Connecting) => Some(serde_json::to_string(.).unwrap()),
//        Event::ShardDisconnected(Disconnected) => Some(serde_json::to_string(.).unwrap()),
//        Event::ShardIdentifying(Identifying) => Some(serde_json::to_string(.).unwrap()),
//        Event::ShardReconnecting(Reconnecting) => Some(serde_json::to_string(.).unwrap()),
//        Event::ShardPayload(Payload) => Some(serde_json::to_string(.).unwrap()),
//        Event::ShardResuming(Resuming) => Some(serde_json::to_string(.).unwrap()),
//        Event::StageInstanceCreate(StageInstanceCreate) => Some(serde_json::to_string(.).unwrap()),
//        Event::StageInstanceDelete(StageInstanceDelete) => Some(serde_json::to_string(.).unwrap()),
//        Event::StageInstanceUpdate(StageInstanceUpdate) => Some(serde_json::to_string(.).unwrap()),
        Event::ThreadCreate(thread_create) => Some(serde_json::to_string(thread_create).unwrap()),
        Event::ThreadDelete(thread_delete) => Some(serde_json::to_string(thread_delete).unwrap()),
        Event::ThreadListSync(thread_list_sync) => Some(serde_json::to_string(thread_list_sync).unwrap()),
        Event::ThreadMemberUpdate(thread_member_update) => Some(serde_json::to_string(thread_member_update).unwrap()),
        Event::ThreadMembersUpdate(thread_members_update) => Some(serde_json::to_string(thread_members_update).unwrap()),
        Event::ThreadUpdate(thread_update) => Some(serde_json::to_string(thread_update).unwrap()),
        Event::TypingStart(typing_start) => Some(serde_json::to_string(typing_start).unwrap()),
//        Event::UnavailableGuild(UnavailableGuild) => Some(serde_json::to_string(.).unwrap()),
        Event::UserUpdate(user_update) => Some(serde_json::to_string(user_update).unwrap()),
        Event::VoiceServerUpdate(voice_server_update) => Some(serde_json::to_string(voice_server_update).unwrap()),
        Event::VoiceStateUpdate(voice_state_update) => Some(serde_json::to_string(voice_state_update).unwrap()),
//        Event::WebhooksUpdate(WebhooksUpdate) => Some(serde_json::to_string(.).unwrap()),

        _ => None,
    }
}

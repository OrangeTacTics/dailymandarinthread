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


#[derive(Debug, Clone)]
pub struct ChairmanMao {
    client: Arc<Client>,
    shard_events: Arc<Mutex<Events>>,
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

        let client = Arc::new(Client::new(token.clone()));
        let (shard, shard_events) = Shard::new(token, intents).await?;

        shard.start().await?;

        Ok(ChairmanMao {
            client,
            shard_events: Arc::new(Mutex::new(shard_events)),
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
    while let Some(event) = chairmanmao.next_event().await {
        let t = tokio::spawn(handle_event(event));
        if let Err(e) = t.await {
            println!("Error: {:?}", e);
        }
    }
}

async fn handle_event(event: Event) -> Result<(), Error> {
    match &event {
        Event::GatewayHeartbeatAck => (),
        _ => {
            println!("{:?}", event.kind());
            println!();
            if let Some(json_event) = serialize_to_json(&event) {
                println!("{}", json_event);
            }
            println!();
            ()
        },
    }

    Ok(())
}


fn serialize_to_json(event: &Event) -> Option<String> {
    match event {
        Event::BanAdd(ban_add) => Some(serde_json::to_string_pretty(ban_add).unwrap()),
        Event::BanRemove(ban_remove) => Some(serde_json::to_string_pretty(ban_remove).unwrap()),
        Event::ChannelCreate(channel_create) => Some(serde_json::to_string_pretty(channel_create).unwrap()),
        Event::ChannelDelete(channel_delete) => Some(serde_json::to_string_pretty(channel_delete).unwrap()),
        Event::ChannelPinsUpdate(channel_pins_update) => Some(serde_json::to_string_pretty(channel_pins_update).unwrap()),
        Event::ChannelUpdate(channel_update) => Some(serde_json::to_string_pretty(channel_update).unwrap()),
        Event::CommandPermissionsUpdate(command_permissions_update) => Some(serde_json::to_string_pretty(command_permissions_update).unwrap()),
//        Event::GatewayHeartbeat(u64) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::GatewayHeartbeatAck => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::GatewayHello(u64) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::GatewayInvalidateSession(bool) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::GatewayReconnect => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::GiftCodeUpdate => Some(serde_json::to_string_pretty(.).unwrap()),
        Event::GuildCreate(guild_create) => Some(serde_json::to_string_pretty(guild_create).unwrap()),
        Event::GuildDelete(guild_delete) => Some(serde_json::to_string_pretty(guild_delete).unwrap()),
        Event::GuildEmojisUpdate(guild_emojis_update) => Some(serde_json::to_string_pretty(guild_emojis_update).unwrap()),
//        Event::GuildIntegrationsUpdate(GuildIntegrationsUpdate) => Some(serde_json::to_string_pretty(.).unwrap()),
        Event::GuildScheduledEventCreate(guild_scheduled_event_create) => Some(serde_json::to_string_pretty(guild_scheduled_event_create).unwrap()),
        Event::GuildScheduledEventDelete(guild_scheduled_event_delete) => Some(serde_json::to_string_pretty(guild_scheduled_event_delete).unwrap()),
        Event::GuildScheduledEventUpdate(guild_scheduled_event_update) => Some(serde_json::to_string_pretty(guild_scheduled_event_update).unwrap()),
        Event::GuildScheduledEventUserAdd(guild_scheduled_event_user_add) => Some(serde_json::to_string_pretty(guild_scheduled_event_user_add).unwrap()),
        Event::GuildScheduledEventUserRemove(guild_scheduled_event_user_remove) => Some(serde_json::to_string_pretty(guild_scheduled_event_user_remove).unwrap()),
        Event::GuildStickersUpdate(guild_sticker_update) => Some(serde_json::to_string_pretty(guild_sticker_update).unwrap()),
        Event::GuildUpdate(guild_update) => Some(serde_json::to_string_pretty(guild_update).unwrap()),
//        Event::IntegrationCreate(Box<IntegrationCreate>) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::IntegrationDelete(IntegrationDelete) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::IntegrationUpdate(Box<IntegrationUpdate>) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::InteractionCreate(InteractionCreate) => Some(serde_json::to_string_pretty(.).unwrap()),
        Event::InviteCreate(invite_create) => Some(serde_json::to_string_pretty(invite_create).unwrap()),
        Event::InviteDelete(invite_delete) => Some(serde_json::to_string_pretty(invite_delete).unwrap()),
        Event::MemberAdd(member_add) => Some(serde_json::to_string_pretty(member_add).unwrap()),
        Event::MemberRemove(member_remove) => Some(serde_json::to_string_pretty(member_remove).unwrap()),
        Event::MemberUpdate(member_update) => Some(serde_json::to_string_pretty(member_update).unwrap()),
        Event::MemberChunk(member_chunk) => Some(serde_json::to_string_pretty(member_chunk).unwrap()),
        Event::MessageCreate(message_create) => Some(serde_json::to_string_pretty(message_create).unwrap()),
        Event::MessageDelete(message_delete) => Some(serde_json::to_string_pretty(message_delete).unwrap()),
        Event::MessageDeleteBulk(message_delete_bulk) => Some(serde_json::to_string_pretty(message_delete_bulk).unwrap()),
        Event::MessageUpdate(message_update) => Some(serde_json::to_string_pretty(message_update).unwrap()),
        Event::PresenceUpdate(presence_update) => Some(serde_json::to_string_pretty(presence_update).unwrap()),
//        Event::PresencesReplace => Some(serde_json::to_string_pretty(.).unwrap()),
        Event::ReactionAdd(reaction_add) => Some(serde_json::to_string_pretty(reaction_add).unwrap()),
        Event::ReactionRemove(reaction_remove) => Some(serde_json::to_string_pretty(reaction_remove).unwrap()),
        Event::ReactionRemoveAll(reaction_remove_all) => Some(serde_json::to_string_pretty(reaction_remove_all).unwrap()),
        Event::ReactionRemoveEmoji(reaction_remove_emoji) => Some(serde_json::to_string_pretty(reaction_remove_emoji).unwrap()),
        Event::Ready(ready) => Some(serde_json::to_string_pretty(ready).unwrap()),
//        Event::Resumed => Some(serde_json::to_string_pretty(.).unwrap()),
        Event::RoleCreate(role_create) => Some(serde_json::to_string_pretty(role_create).unwrap()),
        Event::RoleDelete(role_delete) => Some(serde_json::to_string_pretty(role_delete).unwrap()),
        Event::RoleUpdate(role_update) => Some(serde_json::to_string_pretty(role_update).unwrap()),
//        Event::ShardConnected(Connected) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::ShardConnecting(Connecting) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::ShardDisconnected(Disconnected) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::ShardIdentifying(Identifying) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::ShardReconnecting(Reconnecting) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::ShardPayload(Payload) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::ShardResuming(Resuming) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::StageInstanceCreate(StageInstanceCreate) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::StageInstanceDelete(StageInstanceDelete) => Some(serde_json::to_string_pretty(.).unwrap()),
//        Event::StageInstanceUpdate(StageInstanceUpdate) => Some(serde_json::to_string_pretty(.).unwrap()),
        Event::ThreadCreate(thread_create) => Some(serde_json::to_string_pretty(thread_create).unwrap()),
        Event::ThreadDelete(thread_delete) => Some(serde_json::to_string_pretty(thread_delete).unwrap()),
        Event::ThreadListSync(thread_list_sync) => Some(serde_json::to_string_pretty(thread_list_sync).unwrap()),
        Event::ThreadMemberUpdate(thread_member_update) => Some(serde_json::to_string_pretty(thread_member_update).unwrap()),
        Event::ThreadMembersUpdate(thread_members_update) => Some(serde_json::to_string_pretty(thread_members_update).unwrap()),
        Event::ThreadUpdate(thread_update) => Some(serde_json::to_string_pretty(thread_update).unwrap()),
        Event::TypingStart(typing_start) => Some(serde_json::to_string_pretty(typing_start).unwrap()),
//        Event::UnavailableGuild(UnavailableGuild) => Some(serde_json::to_string_pretty(.).unwrap()),
        Event::UserUpdate(user_update) => Some(serde_json::to_string_pretty(user_update).unwrap()),
        Event::VoiceServerUpdate(voice_server_update) => Some(serde_json::to_string_pretty(voice_server_update).unwrap()),
        Event::VoiceStateUpdate(voice_state_update) => Some(serde_json::to_string_pretty(voice_state_update).unwrap()),
//        Event::WebhooksUpdate(WebhooksUpdate) => Some(serde_json::to_string_pretty(.).unwrap()),

        _ => None,
    }
}

pub mod draw;
pub mod exam;
pub mod discord;
pub mod api;
pub mod command_parser;
pub mod sync;
pub mod commands;

pub type Error = Box<dyn std::error::Error + Send + Sync>;


#[derive(Clone)]
pub enum DiscordEvent {
    MemberAdd { user_id: u64 },
    ReactionAdd { emoji: Emoji, user_id: u64, author_id: u64 },
    ReactionRemove { emoji: Emoji, user_id: u64, author_id: u64 },
    NameChange { user_id: u64, name: String },
    ToggleTag { user_id: u64, tag: String },
}

#[derive(Clone)]
pub enum Emoji {
    Custom(u64),
    Unicode(String),
}

#[derive(Clone)]
pub enum DiscordCommand {
    UpdateNick { user_id: u64, nick: Option<String> },
    UpdateRoles { user_id: u64, roles: Vec<u64> },
    AckInteraction { interaction_id: Id<InteractionMarker>, interaction_token: String, message: String },
}

use twilight_http::Client;
use twilight_util::builder::InteractionResponseDataBuilder;
use twilight_model::http::interaction::InteractionResponseType::ChannelMessageWithSource;
use twilight_model::http::interaction::InteractionResponse;
use twilight_model::channel::message::MessageFlags;
use twilight_model::id::{Id, marker::RoleMarker, marker::InteractionMarker};

use async_trait::async_trait;
#[async_trait]
trait DiscordPortal {
    async fn next_event(&self) -> DiscordEvent;
    async fn update_nick(&self, user_id: u64, nick: Option<&str>);
    async fn update_roles(&self, user_id: u64, roles: &[u64]);
    async fn member_roles(&self, user_id: u64) -> Vec<u64>;
    async fn ack_interaction(&self, interaction_id: Id<InteractionMarker>, interaction_token: String, message: String);
}


pub async fn send_discord_command(
    client: &Client,
    constants: &discord::DiscordConstants,
    command: DiscordCommand,
) -> Result<(), Error> {
    match command {
        DiscordCommand::UpdateNick { user_id, nick } => {
            let nick: Option<&str> = nick.as_ref().map(|s| s.as_str());
            client.update_guild_member(constants.guild.id, Id::new(user_id))
                .nick(nick)?
                .exec()
                .await?;
        },
        DiscordCommand::UpdateRoles { user_id, roles } => {
            let roles: Vec<Id<RoleMarker>> = roles.into_iter().map(|role_id| Id::new(role_id)).collect();
            client.update_guild_member(constants.guild.id, Id::new(user_id))
                .roles(&roles)
                .exec()
                .await?;
        },
        DiscordCommand::AckInteraction { interaction_id, interaction_token, message } => {
            let interaction_client = client.interaction(constants.application_id);
            let interaction_response_data = InteractionResponseDataBuilder::new()
                .content(message)
                .flags(MessageFlags::EPHEMERAL)
                .build();

            let interaction_response = &InteractionResponse {
                kind: ChannelMessageWithSource,
                data: Some(interaction_response_data),
            };

            interaction_client.create_response(
                interaction_id,
                &interaction_token,
                interaction_response,
            )
                .exec()
                .await?;
        },
    }
    Ok(())
}

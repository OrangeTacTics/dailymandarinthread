use twilight_model::gateway::event::Event;
use twilight_model::http::interaction::InteractionResponse;
use twilight_http::Client;
use twilight_model::application::interaction::Interaction;
use twilight_model::http::interaction::InteractionResponseType::ChannelMessageWithSource;
use twilight_model::channel::message::MessageFlags;
use twilight_model::application::interaction::ApplicationCommand;
use twilight_model::http::interaction::InteractionResponseData;
use twilight_model::application::interaction::application_command::CommandOptionValue;
use twilight_model::id::{Id, marker::UserMarker};
use twilight_util::builder::InteractionResponseDataBuilder;

use crate::ChairmanMao;
use crate::Error;
use super::cog::Cog;

pub struct SyncCog;

impl Cog for SyncCog {
    fn on_event(&mut self, chairmanmao: &ChairmanMao, event: &Event) {
        tokio::spawn(on_event(chairmanmao.clone(), event.clone()));
    }
}

pub async fn on_event(chairmanmao: ChairmanMao, event: Event) -> Result<(), Error> {
    match event {
        Event::InteractionCreate(payload) => {
            let interaction: &Interaction = &payload.0;

            match interaction {
                Interaction::ApplicationCommand(app_command) => {
                    let command_name = &app_command.data.name;

                    match command_name.as_ref() {
                        "sync" => {
                            let user_id = match get_option_value(&app_command, "syncee") {
                                None => None,
                                Some(CommandOptionValue::User(user_id)) => Some(*user_id),
                                _ => unreachable!(),
                            };

                            cmd_sync(chairmanmao.clone(), &app_command, user_id).await?;
                        },
                        _ => (),
                    }

                },
                _ => (),
            }
        },
        _ => (),
    }

    Ok(())
}

async fn cmd_sync(
    chairmanmao: ChairmanMao,
    app_command: &ApplicationCommand,
    user_id: Option<Id<UserMarker>>,
) -> Result<(), Error> {
    let user_ids: Vec<Id<UserMarker>> = match user_id {
        Some(user_id) => vec![user_id],
        None => {
            let members = chairmanmao
                .client()
                .guild_members(chairmanmao.constants().guild.id)
                .limit(999)?
                .exec().await?
                .model().await?;

//            dbg!(members.len());

            members.iter().map(|member| member.user.id).collect()
        },
    };

    for user_id in &user_ids {
        chairmanmao.push_nick_change(*user_id).await;
        chairmanmao.push_role_change(*user_id).await;
    }

    let callback_data = InteractionResponseDataBuilder::new()
        .content("Synced".to_string())
        .flags(MessageFlags::EPHEMERAL)
        .build();

    send_response(chairmanmao.client(), app_command, callback_data).await;

    Ok(())
}

async fn send_response(client: &Client, application_command: &ApplicationCommand, callback_data: InteractionResponseData) {
    let application_id = {
        let response = client.current_user_application().exec().await.unwrap();
        response.model().await.unwrap().id
    };
    let interaction_client = client.interaction(application_id);

    let interaction_id = &application_command.id;
    let interaction_token = &application_command.token;

    let callback_data = &InteractionResponse {
        kind: ChannelMessageWithSource,
        data: Some(callback_data),
    };

    interaction_client.create_response(
        *interaction_id,
        interaction_token,
        callback_data,
    )
        .exec()
        .await.unwrap();
}

fn get_option_value<'a>(
    app_command: &'a ApplicationCommand,
    option_name: &str,
) -> Option<&'a CommandOptionValue> {
    for option in &app_command.data.options {
        if option.name == option_name {
            return Some(&option.value);
        }
    }
    None
}

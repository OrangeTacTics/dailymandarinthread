use twilight_model::gateway::event::Event;
use twilight_model::http::interaction::InteractionResponse;
use twilight_http::Client;
use twilight_model::application::interaction::Interaction;
use twilight_model::http::interaction::InteractionResponseType::ChannelMessageWithSource;
use twilight_model::channel::message::MessageFlags;
use twilight_model::application::interaction::ApplicationCommand;
use twilight_model::http::interaction::InteractionResponseData;
use twilight_model::application::interaction::application_command::CommandOptionValue;
use twilight_util::builder::InteractionResponseDataBuilder;
use twilight_model::id::Id;
use twilight_model::id::marker::UserMarker;

use crate::ChairmanMao;
use crate::Error;
use super::cog::Cog;

pub struct TagCog;

impl Cog for TagCog {
    fn on_event(&mut self, chairmanmao: &ChairmanMao, event: &Event) {
        tokio::spawn(on_event(chairmanmao.clone(), event.clone()));
    }
}

pub async fn on_event(chairmanmao: ChairmanMao, event: Event) -> Result<(), Error> {
    match event {
        Event::InteractionCreate(payload) => {
            let interaction: &Interaction = &payload.0;

            match interaction {
                Interaction::Ping(ping) => {
                    dbg!(ping);
                },
                Interaction::ApplicationCommand(app_command) => {
                    let command_name = &app_command.data.name;

                    match command_name.as_ref() {
                        "tag" => {
                            let user_id: Id<UserMarker> = get_user(&app_command);
                            let tag: Option<&str> = get_tag(&app_command);

                            if let Some(tag) = tag {
                                let tags = chairmanmao.api().toggle_tag(user_id.get(), tag).await?;

                                let callback_data = InteractionResponseDataBuilder::new()
                                    .content(format!("Tags: {tags:?}"))
                                    .flags(MessageFlags::EPHEMERAL)
                                    .build();

                                send_response(chairmanmao.client(), app_command, callback_data).await;
                            } else {
                                let tags = chairmanmao.api().get_roles(user_id.get()).await?;
                                let callback_data = InteractionResponseDataBuilder::new()
                                    .content(format!("Tags: {tags:?}"))
                                    .flags(MessageFlags::EPHEMERAL)
                                    .build();

                                send_response(chairmanmao.client(), app_command, callback_data).await;
                            }
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

fn get_user(app_command: &ApplicationCommand) -> Id<UserMarker> {
    for option in &app_command.data.options {
        if option.name == "user" {
            if let CommandOptionValue::User(user_id) = &option.value {
                return *user_id;
            }
        }
    }
    unreachable!()
}

fn get_tag(app_command: &ApplicationCommand) -> Option<&str> {
    for option in &app_command.data.options {
        if option.name == "tag" {
            if let CommandOptionValue::String(value) = &option.value {
                return Some(&value);
            }
        }
    }
    None
}

use twilight_model::gateway::event::Event;
use twilight_model::http::interaction::InteractionResponse;
use twilight_http::Client;
use twilight_model::application::interaction::Interaction;
use twilight_model::http::interaction::InteractionResponseType::ChannelMessageWithSource;
use twilight_model::channel::message::MessageFlags;
use twilight_model::application::interaction::ApplicationCommand;
use twilight_model::http::interaction::InteractionResponseData;
use twilight_util::builder::InteractionResponseDataBuilder;

use crate::ChairmanMao;
use crate::Error;
use super::cog::Cog;

pub struct JailCog;

impl Cog for JailCog {
    fn on_event(&mut self, chairmanmao: &ChairmanMao, event: &Event) {
        tokio::spawn(on_event(chairmanmao.clone(), event.clone()));
    }
}

pub async fn on_event(chairmanmao: ChairmanMao, event: Event) -> Result<(), Error> {
    let client = chairmanmao.client();
    match event {
        Event::InteractionCreate(payload) => {
            let interaction: &Interaction = &payload.0;

            match interaction {
                Interaction::ApplicationCommand(app_command) => {
                    let command_name = &app_command.data.name;

                    match command_name.as_ref() {
                        "jail" => {
                            let callback_data = InteractionResponseDataBuilder::new()
                                .content("Callback message".to_string())
                                .flags(MessageFlags::EPHEMERAL)
                                .build();

                            send_response(client, app_command, callback_data).await;
                        },
                        _command_name => (),
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

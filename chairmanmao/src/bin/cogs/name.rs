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

use crate::ChairmanMao;
use crate::Error;
use super::cog::Cog;

pub struct NameCog;

impl Cog for NameCog {
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

                    println!("Command: {}", command_name);
                    match command_name.as_ref() {
                        "name" => {
                            let user_id = app_command.member.as_ref().unwrap().user.as_ref().unwrap().id.into();
                            let new_display_name = get_name(&app_command);
                            cmd_name(chairmanmao.clone(), app_command, user_id, new_display_name).await;
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

async fn cmd_name(
    chairmanmao: ChairmanMao,
    app_command: &ApplicationCommand,
    user_id: u64,
    new_display_name: Option<&str>,
) {
    chairmanmao.api().set_display_name(
        user_id,
        new_display_name.map(|n| n.to_string()),
    ).await.unwrap();

    let callback_data = InteractionResponseDataBuilder::new()
        .content(format!("Your name has been changed to: {:?}", &new_display_name))
        .flags(MessageFlags::EPHEMERAL)
        .build();

    send_response(chairmanmao.client(), app_command, callback_data).await;
    chairmanmao.push_nick_change(Id::new(user_id)).await;
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

fn get_name(app_command: &ApplicationCommand) -> Option<&str> {
    for option in &app_command.data.options {
        if option.name == "name" {
            if let CommandOptionValue::String(value) = &option.value {
                return Some(&value);
            }
        }
    }
    None
}

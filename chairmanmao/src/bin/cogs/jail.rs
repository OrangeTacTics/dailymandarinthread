use twilight_model::gateway::event::Event;
use twilight_http::Client;
use twilight_model::application::interaction::Interaction;
use twilight_util::builder::CallbackDataBuilder;
use twilight_model::application::callback::InteractionResponse::ChannelMessageWithSource;
use twilight_model::channel::message::MessageFlags;
use twilight_model::application::interaction::ApplicationCommand;
use twilight_model::application::callback::CallbackData;
use twilight_model::application::interaction::application_command::CommandOptionValue;
use twilight_model::id::{Id, marker::UserMarker};

use crate::ChairmanMao;
use crate::Error;


pub async fn on_event(chairmanmao: &ChairmanMao, event: &Event) -> Result<(), Error> {
    let client = chairmanmao.client();
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
                        "jail" => {
                            let callback_data = CallbackDataBuilder::new()
                                .content("Callback message".to_string())
                                .flags(MessageFlags::EPHEMERAL)
                                .build();

                            send_response(client, app_command, callback_data).await;
                        },
                        "sync" => {
                            // let user_id = app_command.member.as_ref().unwrap().user.as_ref().unwrap().id.into();
                            let user_id = match get_option_value(&app_command, "syncee") {
                                None => None,
                                Some(CommandOptionValue::User(user_id)) => Some(*user_id),
                                _ => unreachable!(),
                            };

                            cmd_sync(chairmanmao.clone(), &app_command, user_id).await?;
                        }
                        "name" => {
                            let user_id = app_command.member.as_ref().unwrap().user.as_ref().unwrap().id.into();
                            let new_display_name = get_name(&app_command);
                            cmd_name(chairmanmao.clone(), app_command, user_id, new_display_name).await;
                        },
                        command_name => {
                            let callback_data = CallbackDataBuilder::new()
                                .content(format!("Not implemented: {command_name}"))
                                .flags(MessageFlags::EPHEMERAL)
                                .build();

                            send_response(client, app_command, callback_data).await;
                        },
                    }

                },
                Interaction::ApplicationCommandAutocomplete(app_command_autocomplete) => {
                    dbg!(app_command_autocomplete);
                },
                Interaction::MessageComponent(message_component_interaction) => {
                    dbg!(message_component_interaction);
                },
                e => {
                    dbg!(e);
                },
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

            members.iter().map(|member| member.user.id).collect()
        },
    };

    for user_id in &user_ids {
        chairmanmao.push_nick_change(*user_id).await;
        chairmanmao.push_role_change(*user_id).await;
    }

    let callback_data = CallbackDataBuilder::new()
        .content("Synced".to_string())
        .flags(MessageFlags::EPHEMERAL)
        .build();

    send_response(chairmanmao.client(), app_command, callback_data).await;

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

    let callback_data = CallbackDataBuilder::new()
        .content(format!("Your name has been changed to: {:?}", &new_display_name))
        .flags(MessageFlags::EPHEMERAL)
        .build();

    send_response(chairmanmao.client(), app_command, callback_data).await;
    chairmanmao.push_nick_change(Id::new(user_id)).await;
}

async fn send_response(client: &Client, application_command: &ApplicationCommand, callback_data: CallbackData) {
    let application_id = {
        let response = client.current_user_application().exec().await.unwrap();
        response.model().await.unwrap().id
    };
    let interaction_client = client.interaction(application_id);

    let interaction_id = &application_command.id;
    let interaction_token = &application_command.token;

    let callback_data = &ChannelMessageWithSource(callback_data);
    interaction_client.interaction_callback(
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

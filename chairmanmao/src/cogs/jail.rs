use twilight_model::gateway::event::Event;
use twilight_http::Client;
use twilight_model::application::interaction::Interaction;
use twilight_util::builder::CallbackDataBuilder;
use twilight_model::application::callback::InteractionResponse::ChannelMessageWithSource;
use twilight_model::channel::message::MessageFlags;
use twilight_model::application::interaction::ApplicationCommand;
use twilight_model::application::callback::CallbackData;


pub async fn on_event(client: &Client, event: &Event) {
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

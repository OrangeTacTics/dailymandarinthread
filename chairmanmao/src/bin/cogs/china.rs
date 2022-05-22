use twilight_model::gateway::event::Event;
use twilight_http::Client;
use twilight_http::request::channel::reaction::RequestReactionType;

pub async fn on_event(client: &Client, event: &Event) {
    match event {
        Event::MessageCreate(payload) => {
            let message = &payload.0;

            let lowercase_content = message.content.to_lowercase();

            if lowercase_content.contains("china") ||
                lowercase_content.contains("chinese") {

                let reaction_type = RequestReactionType::Unicode { name: "🇨🇳" };

                client.create_reaction(
                    message.channel_id,
                    message.id,
                    &reaction_type,
                )
                    .exec()
                    .await
                    .unwrap();
            }
        },
        _ => (),
    }
}


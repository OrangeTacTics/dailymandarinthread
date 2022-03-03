use twilight_model::gateway::event::Event;
use twilight_http::Client;
use twilight_model::id::{Id};
use twilight_model::id::marker::{UserMarker};
use twilight_model::channel::PrivateChannel;

pub async fn on_event(client: &Client, event: &Event) {
    match event {
        Event::MessageCreate(payload) => {
            let message = &payload.0;
            if message.content.starts_with("~welcome") {
                println!("WELCOME!");
                send_welcome(client, message.author.id).await;
            }
        },
        Event::MemberAdd(payload) => {
            let member = &payload.0;
            dbg!(&member);
        },
        _ => (),
    }
}


pub async fn send_welcome(client: &Client, user_id: Id<UserMarker>) {
    let welcome_text = &include_str!("../../data/welcome.md");

    let channel_result = client.create_private_channel(user_id).exec().await;

    match channel_result {
        Err(err) => {
            dbg!(err);
            return;
        }
        Ok(channel) => {
            let channel: PrivateChannel = channel.model().await.unwrap();
            client.create_message(channel.id)
                .content(welcome_text).unwrap()
                .exec()
                .await
                .unwrap();
        },
    }
}

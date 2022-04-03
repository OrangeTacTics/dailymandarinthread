use twilight_model::gateway::event::Event;
use twilight_http::Client;
use twilight_model::id::{Id};
use twilight_model::id::marker::{UserMarker};
use twilight_model::channel::Channel;
use chairmanmao::api::Api;

pub async fn on_event(_client: &Client, event: &Event) {
    match event {
        Event::MessageCreate(_payload) => {
            //let message = &payload.0;
            ()
        },
        Event::MemberAdd(payload) => {
            let member = &payload.0;
            println!("{}     {}", member.user.id, member.user.name);
            let api = Api::new().await;
            api.register(member.user.id.get()).await.unwrap();
        },
        _ => (),
    }
}


pub async fn send_welcome(client: &Client, user_id: Id<UserMarker>) {
    let welcome_text = &include_str!("../../../data/welcome.md");

    let channel_result = client.create_private_channel(user_id).exec().await;

    match channel_result {
        Err(err) => {
            dbg!(err);
            return;
        }
        Ok(channel) => {
            let channel: Channel = channel.model().await.unwrap();
            client.create_message(channel.id)
                .content(welcome_text).unwrap()
                .exec()
                .await
                .unwrap();
        },
    }
}

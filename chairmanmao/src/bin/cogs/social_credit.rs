use twilight_model::gateway::event::Event;
use twilight_http::Client;

pub async fn on_event(client: &Client, event: &Event) {
    match event {
        Event::ReactionAdd(payload) => {
            let reaction = &payload.0;

            let channel_id = reaction.channel_id;
            let message_id = reaction.message_id;

            let message = client.message(channel_id, message_id).exec().await.unwrap().model().await.unwrap();

            let from_user_id = reaction.user_id;
            let to_user_id = message.author.id;
            if from_user_id != to_user_id {
                println!("REACTION ADD {} -> {} {:?}", from_user_id, to_user_id, reaction.emoji);
            }
        },
        Event::ReactionRemove(payload) => {
            let reaction = &payload.0;

            let channel_id = reaction.channel_id;
            let message_id = reaction.message_id;

            let message = client.message(channel_id, message_id).exec().await.unwrap().model().await.unwrap();

            let from_user_id = reaction.user_id;
            let to_user_id = message.author.id;
            if from_user_id != to_user_id {
                println!("REACTION REMOVE {} -> {} {:?}", from_user_id, to_user_id, reaction.emoji);
            }
        },
        _ => (),
    }
}

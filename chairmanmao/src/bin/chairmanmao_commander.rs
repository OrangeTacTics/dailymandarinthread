//use std::borrow::Borrow;
//use tokio::sync::Mutex;
//use std::sync::Arc;
//use std::collections::HashSet;

use redis;
use twilight_http;
use serde_json;
use serde::{Serialize, Deserialize};

use std::env;
//use chairmanmao::discord::DiscordConstants;
use twilight_model::id::Id;
use twilight_http::request::channel::reaction::RequestReactionType;

use chairmanmao::Error;

#[tokio::main]
async fn main() -> Result<(), Error> {
    let token = env::var("DISCORD_TOKEN")?;

    let client = twilight_http::Client::new(token);
    let redis = redis::Client::open("redis://127.0.0.1/")?.get_connection()?;

    let h1 = tokio::spawn(listen_loop(redis, client));
    h1.await?;

    Ok(())
}


#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type")]
enum Command {
    CreateMessage {
        channel_id: u64,
        content: Option<String>,
        reply: Option<u64>,
    },
    DeleteMessage {
        channel_id: u64,
        message_id: u64,
    },
    CreateReaction {
        channel_id: u64,
        message_id: u64,
        emoji: Emoji,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type")]
enum Emoji {
    Unicode {
        emoji: String,
    },
    Custom {
        id: u64,
    },
}



async fn listen_loop(mut redis: redis::Connection, client: twilight_http::Client) {
    loop {
        let (_list_name, cmd): (String, String) = redis::cmd("BLPOP").arg("commands").arg("0").query(&mut redis).unwrap();
        match serde_json::from_str::<Command>(&cmd) {
            Ok(cmd) => {
                dbg!(&cmd);
                if let Err(err) = handle_command(&client, cmd).await {
                    eprintln!("ERROR: {:?}", &err);
                }
            },
            Err(err) => {
                eprintln!("ERROR: {:?}", &err);
            },
        }
    }
}

async fn handle_command(client: &twilight_http::Client, command: Command) -> Result<(), Error> {
    match command {
        Command::CreateMessage { channel_id, content, reply } => {
            let mut req = client.create_message(Id::new(channel_id));

            let content_str: String = if let Some(content_str) = &content {
                content_str.to_owned()
            } else {
                "".to_owned()
            };

            if content.is_some() {
                req = req.content(&content_str)?;
            }

            if let Some(reply_id) = &reply {
                req = req.reply(Id::new(*reply_id));
            }

            req.exec().await?;
        },
        Command::DeleteMessage { channel_id, message_id } => {
            let req = client.delete_message(
                Id::new(channel_id),
                Id::new(message_id),
            );
            req.exec().await?;
        },
        Command::CreateReaction { channel_id, message_id, emoji } => {
            let emoji = match &emoji {
                Emoji::Unicode { emoji } => RequestReactionType::Unicode { name: &emoji },
                Emoji::Custom { id } => RequestReactionType::Custom { id: Id::new(*id), name: None },
            };

            let req = client.create_reaction(
                Id::new(channel_id),
                Id::new(message_id),
                &emoji,
            );
            req.exec().await?;
        },
    }

    Ok(())
}

//async fn do_sync(chairmanmao: ChairmanMao) -> Result<(), Error> {
//    if chairmanmao.has_pending_syncs().await {
//        println!("Has pending syncs:");
//        for pending_sync in &chairmanmao.pop_all_syncs().await {
//            println!("{:?}", pending_sync);
//
//            let constants = chairmanmao.constants();
//            let guild_id = constants.guild.id;
//
//            match pending_sync {
//                PendingSync::UpdateNick(user_id) => {
//                    let nick: String = chairmanmao::sync::get_nick(
//                        chairmanmao.api(),
//                        chairmanmao.client(),
//                        *user_id,
//                    ).await?;
//
//                    chairmanmao.client().update_guild_member(guild_id, *user_id)
//                        .nick(Some(&nick))?
//                        .exec()
//                        .await?;
//                    println!("Update user {} to {:?}", user_id.to_string(), nick);
//                },
//                PendingSync::UpdateRoles(user_id) => {
//                    let member = chairmanmao.client().guild_member(guild_id, *user_id)
//                        .exec()
//                        .await?
//                        .model()
//                        .await?;
//
//                    let tags = chairmanmao.api().get_tags(user_id.get()).await?;
//
//                    let old_roles: HashSet<Id<RoleMarker>> = member.roles.iter().cloned().collect();
//                    let mut new_roles = old_roles.clone();
//
//                    remove_chairmanmao_managed_roles(&chairmanmao, &mut new_roles);
//
//                    new_roles.insert(constants.comrade_role.id);
//
//                    if tags.contains(&"Party".to_string()) {
//                        new_roles.insert(constants.party_role.id);
//                    }
//
//                    if tags.contains(&"Bumpers".to_string()) {
//                        new_roles.insert(constants.bumpers_role.id);
//                    }
//
//                    if tags.contains(&"Learner".to_string()) {
//                        new_roles.insert(constants.learner_role.id);
//                    }
//
//                    if tags.contains(&"Art".to_string()) {
//                        new_roles.insert(constants.art_role.id);
//                    }
//
//                    if tags.contains(&"Jailed".to_string()) {
//                        new_roles.clear();
//                        new_roles.insert(constants.jailed_role.id);
//                    }
//
//                    println!("Update roles for {}:  {:?} => {:?}", user_id.get(), &old_roles, &new_roles);
//
//                    let roles: Vec<Id<RoleMarker>> = new_roles.into_iter().collect();
//                    chairmanmao.client().update_guild_member(guild_id, *user_id)
//                        .roles(&roles)
//                        .exec()
//                        .await?;
//                },
//            }
//
//            // TODO: This is a hack to prevent rate-limiting.
//            tokio::time::sleep(std::time::Duration::from_millis(100)).await;
//        }
//    }
//    Ok(())
//}
//
//fn remove_chairmanmao_managed_roles(chairmanmao: &ChairmanMao, roles: &mut HashSet<Id<RoleMarker>>) {
//    let constants = chairmanmao.constants();
//
//    let chairmanmao_managed_roles = &[
//        constants.comrade_role.id,
//        constants.party_role.id,
//        constants.jailed_role.id,
//        constants.bumpers_role.id,
//        constants.learner_role.id,
//        constants.art_role.id,
//    ];
//
//    for role_id in chairmanmao_managed_roles {
//        roles.remove(&role_id);
//    }
//}

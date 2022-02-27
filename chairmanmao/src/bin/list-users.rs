use std::error::Error;
use twilight_http::Client;
use twilight_model::id::Id;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error + Send + Sync>> {
    // Initialize the tracing subscriber.
    tracing_subscriber::fmt::init();

    let token = std::env::var("DISCORD_TOKEN")?.to_owned();
    let client = Client::new(token);

    let guilds = client.current_user_guilds().exec().await?.model().await?;
    let guild_id = guilds[0].id;

    let mut members = client.guild_members(guild_id).limit(999)?.exec().await?.model().await?;

    members.sort_by(|member1, member2| {
        let joined_1 = member1.joined_at.as_micros();
        let joined_2 = member2.joined_at.as_micros();
        joined_1.cmp(&joined_2)
    });

    println!("Members:");
    for (i, member) in members.iter().enumerate() {
        let username = format!("{}#{:04}", member.user.name, member.user.discriminator);
        let nick = match member.nick.as_ref() {
            Some(n) => n,
            None => &member.user.name,
        };
        println!("   {:>6}    {:>20}    {:32}    {}", i, member.user.id, nick, username);
    }

    Ok(())
}

use std::error::Error;
use twilight_http::Client;
use twilight_model::guild::{Role, Emoji};
use twilight_model::user::{CurrentUser, CurrentUserGuild};
use twilight_model::channel::GuildChannel;


#[derive(Debug, Clone)]
pub struct DiscordConstants {
    pub guild: CurrentUserGuild,
    pub bot_user: CurrentUser,

    // ROLES
    pub comrade_role: Role,
    pub party_role: Role,
    pub jailed_role: Role,
    pub learner_role: Role,
    pub bumpers_role: Role,

    // CHANNELS
    // NEWS
//    pub news_channel: GuildChannel,
//    pub rules_channel: GuildChannel,
    // GENERAL
    pub general_channel: GuildChannel,
//    pub exam_channel: GuildChannel,
//    pub learners_channel: GuildChannel,
//    pub apologies_channel: GuildChannel,
//    pub voice_channel: GuildChannel,
    // SPECIAL
//    pub party_channel: GuildChannel,
//    pub art_channel: GuildChannel,
//    pub bump_channel: GuildChannel,
    pub tiananmen_channel: GuildChannel,

    // EMOJIS
    pub mao_emoji: Emoji,
}

impl DiscordConstants {
    pub async fn load(client: &Client) -> Result<DiscordConstants, Box<dyn Error + Send + Sync>> {
        let guilds = client.current_user_guilds().exec().await?.model().await?;
        let guild = guilds[0].clone();
        let guild_id = guild.id;

        let bot_user = client.current_user().exec().await?.model().await?;
        let roles = client.roles(guild_id).exec().await?.model().await?;
        let channels = client.guild_channels(guild_id).exec().await?.model().await?;
        let emojis = client.emojis(guild_id).exec().await?.model().await?;

        let comrade_role = find_role(&roles, "同志")?;
        let party_role = find_role(&roles, "共产党员")?;
        let jailed_role = find_role(&roles, "劳改")?;
        let learner_role = find_role(&roles, "中文学习者")?;
        let bumpers_role = find_role(&roles, "Bumpers")?;

//        let news_channel = find_channel(&channels, "📰")?;
//        let rules_channel = find_channel(&channels, "🈲")?;
//        let thread_channel = find_channel(&channels, "🧵")?;
        let general_channel = find_channel(&channels, "🐉")?;
//        let learners_channel = find_channel(&channels, "✍")?;
//        let exam_channel = find_channel(&channels, "🏫")?;
//        let apologies_channel = find_channel(&channels, "⛔")?;
        let tiananmen_channel = find_channel(&channels, "🏯")?;
//        let bump_channel = find_channel(&channels, "✊")?;

        let mao_emoji = find_emoji(&emojis, "mao")?;
//        let eek_emoji = find_emoji(&guild.emojis, "eek");
//        let dekinai_emoji = find_emoji(&guild.emojis, "buneng");
//        let dekinai2_emoji = find_emoji(&guild.emojis, "buneng2");
//        let diesofcringe_emoji = find_emoji(&guild.emojis, "diesofcringe");
//        let rightist_emoji = find_emoji(&guild.emojis, "rightist");
//        let refold_emoji = find_emoji(&guild.emojis, "refold");

        Ok(DiscordConstants {
            guild,
            bot_user,

            comrade_role,
            party_role,
            jailed_role,
            learner_role,
            bumpers_role,

//            news_channel,
//            rules_channel,
//            thread_channel,
            general_channel,
//            learners_channel,
//            exam_channel,
//            apologies_channel,
            tiananmen_channel,
//            bump_channel,

            mao_emoji,
        })
    }
}

fn find_role(roles: &[Role], name: &str) -> Result<Role, Box<dyn Error + Send + Sync>> {
    for role in roles.iter() {
        if role.name.contains(name) {
            return Ok(role.clone());
        }
    }
    Err(format!("Role not found: {}", name).into())
}

fn find_channel(channels: &[GuildChannel], name: &str) -> Result<GuildChannel, Box<dyn Error + Send + Sync>> {
    for channel in channels {
        if channel.name().contains(name) {
            return Ok(channel.clone());
        }
    }
    Err(format!("Channel not found: {}", name).into())
}

fn find_emoji(emojis: &[Emoji], name: &str) -> Result<Emoji, Box<dyn Error + Send + Sync>> {
    for emoji in emojis {
        if emoji.name.contains(name) {
            return Ok(emoji.clone());
        }
    }
    Err(format!("Emoji not found: {}", name).into())
}

use std::error::Error;
use twilight_http::Client;
use twilight_model::guild::{Role, Emoji};
use twilight_model::user::{CurrentUser, CurrentUserGuild};
use twilight_model::channel::GuildChannel;
use twilight_model::id::{Id, marker::GuildMarker};


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
    pub news_channel: GuildChannel,
    pub rules_channel: GuildChannel,
    // GENERAL
    pub general_channel: GuildChannel,
    pub exam_channel: GuildChannel,
    pub learners_channel: GuildChannel,
    pub apologies_channel: GuildChannel,
    //pub voice_channel: GuildChannel,
    // SPECIAL
    pub party_channel: GuildChannel,
    pub art_channel: GuildChannel,
    pub bump_channel: GuildChannel,
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

        let comrade_role = find_role(&client, guild_id, &roles, "同志").await?;
        let party_role = find_role(&client, guild_id, &roles, "共产党员").await?;
        let jailed_role = find_role(&client, guild_id, &roles, "劳改").await?;
        let learner_role = find_role(&client, guild_id, &roles, "中文学习者").await?;
        let bumpers_role = find_role(&client, guild_id, &roles, "Bumpers").await?;

        let news_channel = find_channel(&client, guild_id, &channels, "📰人民日报").await?;
        let rules_channel = find_channel(&client, guild_id, &channels, "🈲规则").await?;
//        let thread_channel = find_channel(&client, guild_id, &channels, "🧵dmt").await?;
        let general_channel = find_channel(&client, guild_id, &channels, "🐉网络评论员").await?;
        let learners_channel = find_channel(&client, guild_id, &channels, "✍学习中文").await?;
        let exam_channel = find_channel(&client, guild_id, &channels, "🏫考试").await?;
        let apologies_channel = find_channel(&client, guild_id, &channels, "⛔批斗大会").await?;
        let tiananmen_channel = find_channel(&client, guild_id, &channels, "🏯天安门").await?;
        let bump_channel = find_channel(&client, guild_id, &channels, "✊bump").await?;
        let art_channel = find_channel(&client, guild_id, &channels, "🎨艺术").await?;
        let party_channel = find_channel(&client, guild_id, &channels, "🟥共产党").await?;

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

            news_channel,
            rules_channel,
            //thread_channel,
            general_channel,
            learners_channel,
            exam_channel,
            apologies_channel,
            tiananmen_channel,
            bump_channel,
            art_channel,
            party_channel,

            mao_emoji,
        })
    }

    pub fn get_role_by_name(&self, role_name: &str) -> Option<&Role> {
        println!("Looking up role: {:?}", role_name);

        let roles_by_name: std::collections::HashMap<&str, &Role> = vec![
            ("Comrade", &self.comrade_role),
            ("Party", &self.party_role),
            ("Jailed", &self.jailed_role),
        ].iter().cloned().collect();

        if let Some(role) = roles_by_name.get(role_name) {
            println!("Found shortname role: {:?}", role);
            return Some(role);
        }

        let roles = vec![
            &self.comrade_role,
            &self.party_role,
            &self.jailed_role,
            &self.learner_role,
            &self.bumpers_role,
        ];

        for role in &roles {
            if role.name == role_name {
                println!("Found role: {:?}", role);
                return Some(&role);
            }
        }
        println!("Found no matching role...");
        None
    }
}

async fn find_role(
    client: &Client,
    guild_id: Id<GuildMarker>,
    roles: &[Role],
    name: &str,
) -> Result<Role, Box<dyn Error + Send + Sync>> {
    for role in roles.iter() {
        if role.name.contains(name) {
            return Ok(role.clone());
        }
    }

    println!("Creating role {name}");
    let role = client
        .create_role(guild_id)
        .color(0xFF0000)
        .name(name)
        .exec()
        .await?
        .model()
        .await?;

    Ok(role)
}

async fn find_channel(
    client: &Client,
    guild_id: Id<GuildMarker>,
    channels: &[GuildChannel],
    name: &str,
) -> Result<GuildChannel, Box<dyn Error + Send + Sync>> {
    for channel in channels {
        if channel.name().contains(name) {
            return Ok(channel.clone());
        }
    }

    println!("Creating channel {name}");
    let channel = client
        .create_guild_channel(guild_id, name)?
        .exec()
        .await?
        .model()
        .await?;

    Ok(channel)
}

fn find_emoji(emojis: &[Emoji], name: &str) -> Result<Emoji, Box<dyn Error + Send + Sync>> {
    for emoji in emojis {
        if emoji.name.contains(name) {
            return Ok(emoji.clone());
        }
    }
    Err(format!("Emoji not found: {}", name).into())
}

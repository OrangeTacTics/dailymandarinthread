use crate::api::{Api, Profile};
use crate::Error;
use twilight_http::Client;
use twilight_model::id::Id;
use twilight_model::id::marker::UserMarker;

pub async fn get_nick(
    api: &Api,
    client: &Client,
    user_id: Id<UserMarker>,
) -> Result<String, Error> {
    let profile = api.profile(user_id.get()).await?;
    let nick = nick_base(client, &profile).await?;

    let suffix = suffix(&profile).await?;

    let len_display_name = nick.chars().collect::<Vec<char>>().len();
    let len_suffix = suffix.chars().collect::<Vec<char>>().len();
    let chars_to_keep = (len_display_name + len_suffix).min(32) - len_suffix;

    let display_name_trimmed = nick.chars().take(chars_to_keep).collect::<String>();

    Ok(format!("{}{}", display_name_trimmed, suffix))
}

async fn nick_base(
    client: &Client,
    profile: &Profile,
) -> Result<String, Error> {
    if let Some(display_name) = profile.display_name.as_ref().or(profile.discord_username.as_ref()) {
        Ok(display_name.clone())
    } else {
        let user = client.user(Id::new(profile.user_id))
            .exec()
            .await?
            .model()
            .await?;

//        Ok(format!("{}#{}", user.name, user.discriminator))
        Ok(format!("{}", user.name))
    }
}

async fn suffix(
    profile: &Profile,
) -> Result<String, Error> {
    let maru = [
        "➀ ",
        "➁ " ,
        "➂ ",
        "➃",
        "➄ ",
        "➅ ",
    ];

    let hsk_str = if let Some(n) = profile.hsk_level {
        maru[n as usize - 1]
    } else {
        ""
    };

    Ok(format!(" {}[{}]", hsk_str, profile.credit))
}

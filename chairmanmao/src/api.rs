use std::collections::HashSet;
use crate::Error;
use serde::{Serialize, Deserialize};

use mongodb::{Client, options::ClientOptions, Database, Collection};
use mongodb::bson::{doc, oid::ObjectId, DateTime, Bson};

type ApiResult<T> = Result<T, Error>;

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Profile {
    pub _id: ObjectId,
    pub user_id: u64,
    pub discord_username: Option<String>,
    pub created: DateTime,
    pub last_seen: DateTime,
    pub roles: Vec<String>,
    pub display_name: Option<String>,
    pub credit: u32,
    pub yuan: u32,
    pub hanzi: Vec<String>,
    pub mined_words: Vec<String>,
    pub defected: bool,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct DictEntry {
    pub _id: ObjectId,
    pub simplified: String,
    pub traditional: String,
    pub pinyin: String,
    pub meanings: Vec<String>,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct ServerSettings {
    pub _id: ObjectId,
    pub last_bump: DateTime,
    pub exams_disabled: bool,
    pub admin_username: String,
    pub bot_username: String,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Exam {
    pub _id: ObjectId,
    pub name: String,
    pub num_questions: u32,
    pub max_wrong: u32,
    pub timelimit: u32,
    pub hsk_level: u32,
    pub deck: Vec<Card>,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Card {
    pub question: String,
    pub valid_answers: Vec<String>,
    pub meaning: String,
}

impl ServerSettings {
    pub fn new() -> Self {
        ServerSettings {
            _id: ObjectId::new(),
            last_bump: DateTime::now(),
            exams_disabled: false,
            admin_username: "".into(),
            bot_username: "".into(),
        }
    }
}

impl Profile {
    pub fn add_role(&mut self, role: &str) {
        let mut roles: HashSet<String> = self.roles.iter().cloned().collect();
        roles.insert(role.to_string());
        self.roles = roles.into_iter().collect();
        self.roles.sort();
    }

    pub fn remove_role(&mut self, role: &str) {
        let mut roles: HashSet<String> = self.roles.iter().cloned().collect();
        roles.remove(role);
        self.roles = roles.into_iter().collect();
        self.roles.sort();
    }
}

#[derive(Clone, Debug)]
pub struct Api {
    pub client: Client,
    pub db: Database,
    pub profiles_collection: Collection<Profile>,
    pub serversettings_collection: Collection<ServerSettings>,
    pub dictentries_collection: Collection<DictEntry>,
    pub exams_collection: Collection<Exam>,
}


impl Api {
    pub async fn new() -> Api {
        let mongodb_uri = std::env::var("MONGODB_URI").expect("MONGODB_URI not defined in envrionment");
        let mongodb_db = std::env::var("MONGODB_DB").expect("MONGODB_DB not defined in envrionment");

        let client_options = ClientOptions::parse(mongodb_uri).await.unwrap();
        let client = Client::with_options(client_options).unwrap();
        let db = client.database(&mongodb_db);

        let profiles_collection = db.collection::<Profile>("Profiles");
        let serversettings_collection = db.collection::<ServerSettings>("ServerSettings");
        let exams_collection = db.collection::<Exam>("Exams");
        let dictentries_collection = db.collection::<DictEntry>("DictEntries");

        Api {
            client,
            db,
            profiles_collection,
            serversettings_collection,
            dictentries_collection,
            exams_collection,
        }
    }

    pub async fn register(
        &self,
        user_id: u64,
    ) -> ApiResult<Profile> {
        let now = DateTime::now();

        let profile = Profile {
            _id: ObjectId::new(),
            user_id,
            discord_username: None,
            created: now,
            last_seen: now,
            roles: Vec::new(),
            display_name: None,
            credit: 1000,
            yuan: 0,
            hanzi: Vec::new(),
            mined_words: Vec::new(),
            defected: false,
        };

        let query = doc! { "user_id": Bson::Int64(user_id as i64) };
        if let Some(_profile) = self.profiles_collection.find_one(query, None).await? {
            return Err(format!("Profile already exists with user_id: {user_id}").into());
        }

        self.profiles_collection.insert_one(&profile, None).await?;

        Ok(profile)
    }

    pub async fn serversettings (&self) -> ApiResult<ServerSettings> {
        let serversettings = self.serversettings_collection.find_one(None, None).await?;
        match serversettings {
            None => Ok(ServerSettings::new()),
            Some(serversettings) => Ok(serversettings),
        }
    }

    pub async fn profile(&self, user_id: u64) -> ApiResult<Option<Profile>> {
        let profile = self.profiles_collection.find_one(doc! { "user_id": Bson::Int64(user_id as i64) }, None).await?;
        Ok(profile)
    }

    async fn set_profile(&self, user_id: u64, profile: Profile) -> ApiResult<()> {
        self.profiles_collection.replace_one(doc! { "user_id": Bson::Int64(user_id as i64) }, profile, None).await?;
        Ok(())
    }

    async fn update_profile(
        &self,
        user_id: u64,
        update: impl FnOnce(&mut Profile),
    ) -> ApiResult<Profile> {

        let profile = self.profile(user_id).await?;
        match profile {
            None => return Err(format!("Profile does not exist with user_id: {user_id}").into()),
            Some(mut profile) => {
                update(&mut profile);
                self.set_profile(user_id, profile.clone()).await?;
                Ok(profile)
            },
        }
    }

    pub async fn hsk(
        &self,
        user_id: u64,
    ) -> ApiResult<Option<u8>> {
        if let Some(profile) = self.profile(user_id).await? {
            if profile.roles.contains(&"Hsk6".to_string()) {
                Ok(Some(6))
            } else if profile.roles.contains(&"Hsk5".to_string()) {
                Ok(Some(5))
            } else if profile.roles.contains(&"Hsk4".to_string()) {
                Ok(Some(4))
            } else if profile.roles.contains(&"Hsk3".to_string()) {
                Ok(Some(3))
            } else if profile.roles.contains(&"Hsk2".to_string()) {
                Ok(Some(2))
            } else if profile.roles.contains(&"Hsk1".to_string()) {
                Ok(Some(1))
            } else {
                Ok(None)
            }
        } else {
            Ok(None)
        }
    }

    pub async fn set_hsk(
        &self,
        user_id: u64,
        hsk: Option<u8>,
    ) -> ApiResult<Profile> {
        let hsk_role = hsk.map(|n| format!("Hsk{n}"));

        self.update_profile(
            user_id,
            |profile| {
                profile.remove_role("Hsk1");
                profile.remove_role("Hsk2");
                profile.remove_role("Hsk3");
                profile.remove_role("Hsk4");
                profile.remove_role("Hsk5");
                profile.remove_role("Hsk6");
                if let Some(hsk_role) = hsk_role {
                    profile.add_role(&hsk_role);
                }
            },
        ).await
    }

    pub async fn jail(
        &self,
        user_id: u64,
    ) -> ApiResult<Profile> {
        self.update_profile(
            user_id,
            |profile| {
                profile.add_role("Jailed");
            },
        ).await
    }

    pub async fn unjail(
        &self,
        user_id: u64,
    ) -> ApiResult<Profile> {
        self.update_profile(
            user_id,
            |profile| {
                profile.remove_role("Jailed");
            },
        ).await
    }

    pub async fn honor(
        &self,
        user_id: u64,
        amount: i32,
    ) -> ApiResult<Profile> {
        self.update_profile(
            user_id,
            |profile| {
                profile.credit = (profile.credit as i32 + amount).max(0) as u32;
            },
        ).await
    }

    pub async fn set_display_name(
        &self,
        user_id: u64,
        display_name: Option<String>,
    ) -> ApiResult<Profile> {
        self.update_profile(
            user_id,
            |profile| {
                profile.display_name = display_name.into();
            },
        ).await
    }

    pub async fn get_nick(
        &self,
        user_id: u64,
    ) -> ApiResult<Option<String>> {
        match self.profile(user_id).await? {
            None => Ok(None),
            Some(profile) => {
                let display_name = profile.display_name.unwrap_or_else(|| profile.discord_username.unwrap_or_else(|| "unknown".to_string()));

                let suffix = format!(" [{}]", profile.credit);

                let len_display_name = display_name.chars().collect::<Vec<char>>().len();
                let len_suffix = suffix.chars().collect::<Vec<char>>().len();
                let chars_to_keep = (len_display_name + len_suffix).min(32) - len_suffix;

                let display_name_trimmed = display_name.chars().take(chars_to_keep).collect::<String>();

                let nick = format!("{}{}", display_name_trimmed, suffix);
                Ok(Some(nick))
            },
        }
    }

    pub async fn get_roles(
        &self,
        user_id: u64,
    ) -> ApiResult<Vec<String>> {
        match self.profile(user_id).await? {
            None => Ok(Vec::new()),
            Some(profile) => {
                let mut roles = profile.roles.clone();
                roles.push("Comrade".to_string());
                if roles.contains(&"Jailed".to_string()) {
                    Ok(vec!["Jailed".to_string()])
                } else {
                    Ok(roles)
                }
            },
        }
    }
}

#[tokio::test]
async fn test_jail_unjail() -> ApiResult<()> {
    let api = Api::new().await;

    let user_id = 883529933480144958;

    api.jail(user_id).await.unwrap();
    let profile = api.profile(user_id).await.unwrap().unwrap();
    assert!(profile.roles.contains(&"Jailed".to_string()));

    api.unjail(user_id).await.unwrap();
    let profile = api.profile(user_id).await.unwrap().unwrap();
    assert!(!profile.roles.contains(&"Jailed".to_string()));

    api.set_hsk(user_id, Some(4)).await.unwrap();
    let hsk = api.hsk(user_id).await.unwrap();
    assert_eq!(hsk, Some(4));

    api.set_hsk(user_id, None).await.unwrap();
    let hsk = api.hsk(user_id).await.unwrap();
    assert_eq!(hsk, None);

    Ok(())
}

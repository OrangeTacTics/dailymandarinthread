use std::collections::HashSet;
use std::error::Error;
use serde::{Serialize, Deserialize};

use mongodb::{Client, options::ClientOptions, Database, Collection};
use mongodb::bson::{doc, oid::ObjectId, DateTime, Bson};

type ApiResult<T> = Result<T, Box<dyn Error + Sync + Send>>;

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

#[derive(Clone)]
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
        let client_options = ClientOptions::parse("mongodb://localhost:27017/").await.unwrap();
        let client = Client::with_options(client_options).unwrap();
        let db = client.database("DailyMandarinThread");

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

    Ok(())
}

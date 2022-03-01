use std::error::Error;
use serde::{Serialize, Deserialize};

use mongodb::{Client, options::ClientOptions, Database, Collection};
use mongodb::bson::{doc, oid::ObjectId, DateTime, Bson};

type ApiResult<T> = Result<T, Box<dyn Error + Sync + Send>>;

#[derive(Serialize, Deserialize, Debug)]
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


#[derive(Serialize, Deserialize, Debug)]
pub struct DictEntry {
    pub _id: ObjectId,
    pub simplified: String,
    pub traditional: String,
    pub pinyin: String,
    pub meanings: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ServerSettings {
    pub _id: ObjectId,
    pub last_bump: DateTime,
    pub exams_disabled: bool,
    pub admin_username: String,
    pub bot_username: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Exam {
    pub _id: ObjectId,
    pub name: String,
    pub num_questions: u32,
    pub max_wrong: u32,
    pub timelimit: u32,
    pub hsk_level: u32,
    pub deck: Vec<Card>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Card {
    pub question: String,
    pub valid_answers: Vec<String>,
    pub meaning: String,
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

        for collection_name in db.list_collection_names(None).await.unwrap() {
            println!("{}", collection_name);
        }

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

    pub async fn profile(
        &self,
        user_id: u64,
    ) -> ApiResult<Option<Profile>> {
        dbg!(&user_id);
        let profile = self.profiles_collection.find_one(doc! { "user_id": Bson::Int64(user_id as i64) }, None).await?;
        Ok(profile)
    }
/*
    pub fn jail(
        &self,
        to_user_id: u64,
    ) -> ApiResult<Profile> {}

    pub fn unjail(
        &self,
        to_user_id: UserId,
    ) {}

    pub fn honor(
        &self,
        to_user_id: UserId,
        amount: i32,
    ) {}

    pub fn dishonor(
        &self,
        to_user_id: UserId,
        amount: i32,
    ) {}
*/
}

#[tokio::test]
async fn foo() -> ApiResult<()> {
    println!("*****************************");
    let api = Api::new().await;
    println!("*****************************");
//    api.register(1234).await?;
//    dbg!(api.profile(1234).await.unwrap());

    Ok(())
}



/*
        let mut conn = self.conn();
        let key = format!("profile:{}", user_id);

        let result: bool = conn.keys(&key)?;
        if result {
            return Err(format!("User {} already registered.", user_id).into());
        }

        let profile = Profile {
            user_id,
            display_name: None,
            credit: 1000,
            hsk: 0,
            party: false,
            jailed: false,
        };
        let val = serde_json::to_string(&profile).unwrap();
        conn.set(key, val)?;
        Ok(profile)
*/

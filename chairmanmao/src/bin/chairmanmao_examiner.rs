use std::sync::Arc;
use tokio::sync::Mutex;
use chairmanmao::exam::{Examiner, Exam, TickResult};
use twilight_embed_builder::{EmbedBuilder, EmbedFieldBuilder};
use futures_util::StreamExt;
use std::error::Error;
use twilight_gateway::{Intents, Shard};
use twilight_model::gateway::event::Event;
use twilight_model::channel::message::Message;
use twilight_http::Client;
use clap::Parser;
use twilight_model::id::Id;
use twilight_model::id::marker::{ChannelMarker, UserMarker};

const MILLIS_PER_TICK: usize = 100;


#[derive(Parser, Debug)]
struct Cli {
    channel_ids: Vec<String>,
}

struct State {
    active_exams: Vec<ActiveExam>,
}

type StateLock = Arc<Mutex<State>>;

impl State {
    fn new() -> StateLock {
        Arc::new(Mutex::new(State {
            active_exams: Vec::new(),
        }))
    }

    fn is_channel_busy(&self, channel_id: Id<ChannelMarker>) -> bool {
        for active_exam in self.active_exams.iter() {
            if active_exam.channel_id == channel_id {
                return true;
            }
        }
        false
    }

    fn is_user_busy(&self, user_id: Id<UserMarker>) -> bool {
        for active_exam in self.active_exams.iter() {
            if active_exam.user_id == user_id {
                return true;
            }
        }
        false
    }

    fn active_exam_for(
        &mut self,
        channel_id: Id<ChannelMarker>,
        user_id: Id<UserMarker>,
    ) -> Option<&mut ActiveExam> {
        for active_exam in self.active_exams.iter_mut() {
            if active_exam.channel_id == channel_id && active_exam.user_id == user_id {
                return Some(active_exam);
            }
        }
        None
    }

    fn remove_active_exam(
        &mut self,
        user_id: Id<UserMarker>,
    ) {
        let mut active_exams: Vec<ActiveExam> = Vec::new();
        for active_exam in &self.active_exams {
            if active_exam.user_id != user_id {
                active_exams.push(active_exam.clone());
            }
        }
        self.active_exams = active_exams;
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error + Send + Sync>> {
    // Initialize the tracing subscriber.
    tracing_subscriber::fmt::init();
    let args = Cli::parse();

    let channel_ids: Vec<Id<ChannelMarker>> = args.channel_ids.iter().map(|id| Id::new(id.parse().unwrap())).collect();
    run_examiner(&channel_ids).await?;

    Ok(())
}

async fn run_examiner(channel_ids: &[Id<ChannelMarker>]) -> Result<(), Box<dyn Error + Send + Sync>> {
    let intents =
        Intents::GUILD_MESSAGES |
        Intents::GUILD_MESSAGE_REACTIONS |
        Intents::DIRECT_MESSAGES |
        Intents::GUILD_VOICE_STATES |
        Intents::GUILDS |
        Intents::GUILD_MEMBERS;

    let state = State::new();

    let token = std::env::var("DISCORD_TOKEN")?;
    let (shard, mut events) = Shard::new(token.clone(), intents);
    let client = Arc::new(Client::new(token));
    shard.start().await?;

    tokio::spawn(tick_loop(client.clone(), state.clone()));

    while let Some(event) = events.next().await {
        match &event {
            Event::MessageCreate(e) => {
                let message = &e.0;
                if channel_ids.contains(&message.channel_id) {
                    let author = &message.author;
                    if !author.bot {
                        handle_message(state.clone(), client.clone(), &message).await?;
                    }
                }
            },
            _ => (),
        }
    }

    Ok(())
}

async fn handle_message(
    state_lock: StateLock,
    client: Arc<Client>,
    message: &Message,
) -> Result<(), Box<dyn Error + Send + Sync>> {
    if message.content.starts_with("!exam ") {
        handle_exam_command(state_lock, client.clone(), message).await;
    } else {
        let mut state = state_lock.lock().await;
        if let Some(active_exam) = state.active_exam_for(message.channel_id, message.author.id) {
            if let Some((question, answer)) = &active_exam.examiner.answer(&message.content) {
                client.create_message(active_exam.channel_id)
                    .content(&format!("{:?}\n{} {:?} {}", answer, question.question, question.valid_answers, question.meaning))?
                    .exec()
                    .await?;
            }
        }
    }

    Ok(())
}

async fn handle_exam_command(
    state_lock: StateLock,
    _client: Arc<Client>,
    message: &Message,
) {
    if message.content == "!exam start" {
        let mut state = state_lock.lock().await;
        let channel_busy_str = format!("{}", state.is_channel_busy(message.channel_id));
        let user_busy_str = format!("{}", state.is_user_busy(message.author.id));

        println!("chan busy: {channel_busy_str}");
        println!("user busy: {user_busy_str}");

        if state.is_channel_busy(message.channel_id) || state.is_user_busy(message.author.id) {
            println!("Can't start exam");
        } else {
            println!("Starting new exam!");
            let seed = 1;
            let exam = chairmanmao::exam::loader::load_exam("hsk1");
            let examiner = chairmanmao::exam::Examiner::make(&exam, MILLIS_PER_TICK, seed);

            state.active_exams.push(ActiveExam {
                user_id: message.author.id,
                channel_id: message.channel_id,
                examiner,
                exam,
                seed,
            });
        }
    } else if message.content == "!exam quit" {
        let mut state = state_lock.lock().await;
        if state.is_user_busy(message.author.id) {
            println!("Stopping exam!");

            let active_exam = state.active_exam_for(message.channel_id, message.author.id).unwrap();
            active_exam.examiner.give_up();
        } else {
            println!("No exam in progress?");
        }
    }
}


async fn tick_loop(client: Arc<Client>, state_lock: StateLock) -> Result<(), Box<dyn Error + Send + Sync>> {
    loop {
//        println!("TICK");
        let mut state = state_lock.lock().await;

        let mut remove_user_id: Option<Id<UserMarker>> = None;

        for active_exam in state.active_exams.iter_mut() {
            let examiner = &mut active_exam.examiner;

            match examiner.tick() {
                TickResult::Nothing => (),
                TickResult::Timeout => {
                    println!("Timeout");

                    client.create_message(active_exam.channel_id)
                        .content("Timeout")?
                        .exec()
                        .await?;
                },
                TickResult::NextQuestion(question) => {
                    println!("{}", &question.question);

                    client.create_message(active_exam.channel_id)
                        .content(&question.question)?
                        .exec()
                        .await?;
                },
                TickResult::Pause => (),
                TickResult::Finished(exam_score) => {
                    client.create_message(active_exam.channel_id)
                        .content(&format!("{:?}", exam_score))?
                        .exec()
                        .await?;
                    remove_user_id = Some(active_exam.user_id.clone());
                },
            }

        }

        if let Some(user_id) = remove_user_id {
            state.remove_active_exam(user_id);
        }

        let milli_interval = (MILLIS_PER_TICK as f64) as u64;
        tokio::time::sleep(std::time::Duration::from_millis(milli_interval)).await;
    }
}

#[derive(Clone)]
pub struct ActiveExam {
    pub user_id: Id<UserMarker>,
    pub channel_id: Id<ChannelMarker>,
    pub examiner: Examiner,
    pub exam: Exam,
    pub seed: u64,
}

/*

    let channel_busy_str = format!("{}", state.is_channel_busy(message.channel_id));
    let user_busy_str = format!("{}", state.is_user_busy(message.author.id));
    let embed = EmbedBuilder::new()
        .description("Here's a list of reasons why Mao is the best chairman:")
        .field(EmbedFieldBuilder::new("Channel Busy?", channel_busy_str).inline())
        .field(EmbedFieldBuilder::new("User Busy?", user_busy_str).inline())
        .build()?;

    let timestamp = message.timestamp.as_secs();

    client.create_message(message.channel_id)
        .content("Hello")?
        .embeds(&[embed])?
        .exec()
        .await?;
*/

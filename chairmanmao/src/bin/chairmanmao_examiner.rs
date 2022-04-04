use std::sync::Arc;
use tokio::sync::Mutex;
use chairmanmao::exam::{TickResult, active_exam::ActiveExam};
use futures_util::StreamExt;
use chairmanmao::Error;
use twilight_gateway::{Intents, Shard};
use twilight_model::gateway::event::Event;
use twilight_model::channel::message::Message;
use twilight_http::Client;
use clap::Parser;
use twilight_model::id::Id;
use twilight_model::id::marker::{ChannelMarker, UserMarker};
use chairmanmao::discord::DiscordConstants;
use twilight_model::application::interaction::Interaction;
use twilight_model::application::interaction::application_command::CommandOptionValue;
use twilight_model::application::interaction::ApplicationCommand;
use twilight_util::builder::InteractionResponseDataBuilder;
use twilight_model::http::interaction::InteractionResponse;
use twilight_model::http::interaction::InteractionResponseType;
use twilight_model::channel::message::MessageFlags;
use chairmanmao::api::Api;
use chairmanmao::exam::message;

const MILLIS_PER_TICK: usize = 100;


#[derive(Parser, Debug)]
struct Cli {
    channel_ids: Vec<String>,
}

struct State {
    allowed_channels: Vec<Id<ChannelMarker>>,
    active_exams: Vec<ActiveExam>,
}

type StateLock = Arc<Mutex<State>>;

impl State {
    fn new(allowed_channels: Vec<Id<ChannelMarker>>) -> StateLock {
        Arc::new(Mutex::new(State {
            allowed_channels,
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
async fn main() -> Result<(), Error> {
    let args = Cli::parse();
    let mut channel_ids: Vec<Id<ChannelMarker>> = args.channel_ids
        .iter()
        .map(|id| Id::new(id.parse().unwrap()))
        .collect();

    let intents =
        Intents::DIRECT_MESSAGES |
        Intents::GUILDS |
        Intents::GUILD_MEMBERS |
        Intents::GUILD_MESSAGES |
        Intents::GUILD_MESSAGE_REACTIONS |
        Intents::GUILD_VOICE_STATES |
        Intents::MESSAGE_CONTENT;

    let token = std::env::var("DISCORD_TOKEN")?;
    let (shard, mut events) = Shard::new(token.clone(), intents);
    let client = Arc::new(Client::new(token));
    shard.start().await?;
    println!("Running");

    let constants = DiscordConstants::load(&client).await?;
    channel_ids.push(constants.exam_channel.id);


    let api = Api::new().await;
    let state = State::new(channel_ids.clone());

    tokio::spawn(tick_loop(api.clone(), client.clone(), state.clone()));

    while let Some(event) = events.next().await {
        match &event {
            Event::MessageCreate(e) => {
                let message = &e.0;
                if channel_ids.contains(&message.channel_id) {
                    let author = &message.author;
                    if !author.bot {
                        handle_message(api.clone(), state.clone(), client.clone(), &message).await?;
                    }
                }
            },
            Event::InteractionCreate(e) => {
                let interaction: &Interaction = &e.0;

                if let Interaction::ApplicationCommand(application_command) = interaction {
                    let application_id = application_command.application_id;
                    let interaction_client = client.interaction(application_id);
                    let interaction_id = &application_command.id;
                    let interaction_token = &application_command.token;

                    let interaction_response_data = InteractionResponseDataBuilder::new()
                        .content("Starting exam".to_string())
                        .flags(MessageFlags::EPHEMERAL)
                        .build();

                    let callback_data = &InteractionResponse {
                        kind: InteractionResponseType::ChannelMessageWithSource,
                        data: Some(interaction_response_data),
                    };

                    interaction_client.create_response(
                        *interaction_id,
                        interaction_token,
                        callback_data,
                    )
                        .exec()
                        .await.unwrap();

                    if let Some(exam_command) = parse_exam_command(application_command) {
                        handle_exam_command(api.clone(), state.clone(), client.clone(), &exam_command).await?;
                    }
                }
            },
            _ => (),
        }
    }

    Ok(())
}

async fn handle_message(
    api: Api,
    state_lock: StateLock,
    client: Arc<Client>,
    message: &Message,
) -> Result<(), Error> {
    if message.content.starts_with("!exam ") {
        if let Some(exam_command) = message_to_exam_command(message) {
            handle_exam_command(api, state_lock, client.clone(), &exam_command).await?;
        }
    } else {
        let mut state = state_lock.lock().await;
        if let Some(active_exam) = state.active_exam_for(message.channel_id, message.author.id) {
            if let Some((question, answer)) = &active_exam.examiner.answer(&message.content) {
                message::show_answer(&client, &active_exam, &question, &answer).await?
            }
        }
    }

    Ok(())
}

async fn handle_exam_command(
    api: Api,
    state_lock: StateLock,
    client: Arc<Client>,
    exam_command: &ExamCommand,
) -> Result<(), Error> {
    match exam_command {
        ExamCommand::Start { channel_id, exam, user_id }=> {
            let mut state = state_lock.lock().await;
            let exam = if let Some(specified_exam) = exam {
                specified_exam
            } else {
                let hsk = api.hsk(user_id.get()).await?;
                next_exam(hsk).unwrap_or("hsk6")
            };
            exam_start(&mut state, client, *channel_id, *user_id, exam).await?;
        },
        ExamCommand::Quit { user_id, channel_id } => {
            let mut state = state_lock.lock().await;
            exam_stop(&mut state, client, *channel_id, *user_id).await?;
        },
    }

    Ok(())
}

fn next_exam(hsk: Option<u8>) -> Option<&'static str> {
    match hsk {
        None => Some("hsk1"),
        Some(1) => Some("hsk2"),
        Some(2) => Some("hsk3"),
        Some(3) => Some("hsk4"),
        Some(4) => Some("hsk5"),
        Some(5) => Some("hsk6"),
        Some(6) => None,
        Some(_) => None,
    }
}

async fn exam_start(
    state: &mut State,
    client: Arc<Client>,
    channel_id: Id<ChannelMarker>,
    user_id: Id<UserMarker>,
    exam_name: &str,
) -> Result<(), Error> {
    if !state.allowed_channels.contains(&channel_id) {
        println!("Can't start exam. This is not a valid channel.");
    } else if state.is_channel_busy(channel_id) {
        println!("Can't start exam in channel {channel_id}. Channel is already busy.");
    } else if state.is_user_busy(user_id) {
        println!("Can't start exam for user {user_id}. User is already busy.");
    } else {
        let seed = 1;
        let exam = chairmanmao::exam::loader::load_exam(exam_name);
        let examiner = chairmanmao::exam::Examiner::make(&exam, MILLIS_PER_TICK, seed);

        let active_exam = ActiveExam {
            user_id,
            channel_id,
            examiner,
            exam,
            seed,
        };
        message::exam_start(&client, &active_exam).await.unwrap();
        state.active_exams.push(active_exam);
    }

    Ok(())
}

async fn exam_stop(
    state: &mut State,
    _client: Arc<Client>,
    channel_id: Id<ChannelMarker>,
    user_id: Id<UserMarker>,
) -> Result<(), Error> {
    if state.is_user_busy(user_id) {
        let active_exam = state.active_exam_for(channel_id, user_id).unwrap();
        active_exam.examiner.give_up();
    }

    Ok(())
}

async fn tick_loop(_api: Api, client: Arc<Client>, state_lock: StateLock) -> Result<(), Error> {
    loop {
        let mut state = state_lock.lock().await;

        let mut remove_user_id: Option<Id<UserMarker>> = None;

        for active_exam in state.active_exams.iter_mut() {
            let examiner = &mut active_exam.examiner;

            match examiner.tick() {
                TickResult::Nothing => (),
                TickResult::Pause => (),
                TickResult::Timeout => {
                    let question = &examiner.current_question().clone();
                    message::timeout(&client, active_exam, &question).await?;
                },
                TickResult::NextQuestion(question) => {
                    message::pose_question(&client, active_exam, &question).await?;
                },
                TickResult::Finished(exam_score) => {
                    remove_user_id = Some(active_exam.user_id.clone());
                    message::exam_end(&client, &active_exam, exam_score).await.unwrap();
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

#[derive(Debug)]
enum ExamCommand {
    Start {
        user_id: Id<UserMarker>,
        channel_id: Id<ChannelMarker>,
        exam: Option<String>,
    },
    Quit {
        user_id: Id<UserMarker>,
        channel_id: Id<ChannelMarker>,
    },
}

fn parse_exam_command(application_command: &ApplicationCommand) -> Option<ExamCommand> {
    match application_command.data.name.as_str() {
        "exam" => {
            let subcommand = &application_command.data.options[0];
            let subcommand_name = &subcommand.name;
            let user_id = application_command.member.as_ref().unwrap().user.as_ref().unwrap().id;
            let channel_id = application_command.channel_id;

            match subcommand_name.as_str() {
                "start" => {
                    if let CommandOptionValue::SubCommand(subcommand_options) = &subcommand.value {
                        let exam = if subcommand_options.is_empty() {
                             None
                        } else if let CommandOptionValue::String(exam) = &subcommand_options[0].value {
                            Some(exam.clone())
                        } else {
                            panic!("Command option 'exam' should be a string.");
                        };
                        Some(ExamCommand::Start {
                            user_id,
                            channel_id,
                            exam,
                        })
                    } else {
                        None
                    }
                },
                "quit" => {
                    Some(ExamCommand::Quit {
                        user_id,
                        channel_id,
                    })
                },
                name => panic!("Unexpected exam subcommand: {name}"),
            }
        },
        _name => None,
    }
}

fn message_to_exam_command(message: &Message) -> Option<ExamCommand> {
    let user_id = message.author.id;
    let channel_id = message.channel_id;

    if message.content == "!exam start" {
        Some(ExamCommand::Start { exam: None, user_id, channel_id })
    } else if message.content == "!exam quit" {
        Some(ExamCommand::Quit { user_id, channel_id })
    } else {
        None
    }
}

use crate::discord::DiscordConstants;
use twilight_http::client::InteractionClient;

use twilight_model::application::command::Command;
use twilight_model::application::command::CommandOption;
use twilight_model::application::command::OptionsCommandOptionData;

use twilight_model::application::command::{
    NumberCommandOptionData,
    BaseCommandOptionData,
    CommandOptionChoice,
    ChoiceCommandOptionData,
};

use twilight_model::application::command::permissions::{
    CommandPermissions,
    CommandPermissionsType,
};


use twilight_model::id::Id;
use twilight_model::id::marker::GuildMarker;
use twilight_model::id::marker::CommandMarker;


use crate::Error;


pub struct Commands(Vec<(Command, Vec<CommandPermissions>)>);

impl Commands {
    pub fn find(&self, name: &str) -> Option<(Command, Vec<CommandPermissions>)> {
        for (command, permissions) in &self.0 {
            if &command.name == name {
                return Some((command.clone(), permissions.to_vec()));
            }
        }
        None
    }

    pub fn commands(&self) -> Vec<Command> {
        self.0.iter().map(|(command, _permissions)| command.clone()).collect()
    }

    pub fn command_id_permission(&self) -> Vec<(Id<CommandMarker>, CommandPermissions)> {
        let mut result = vec![];
        for (command, permissions) in &self.0 {
            for permission in permissions.iter() {
                result.push((command.id.unwrap(), permission.clone()));
            }
        }
        result
    }
}

pub async fn create_commands<'a>(
    guild_id: Id<GuildMarker>,
    interaction_client: &InteractionClient<'a>,
    constants: DiscordConstants,
) -> Result<Commands, Error> {
    let jail_command = interaction_client
        .create_guild_command(guild_id)
        .user("jail")?
        .default_permission(false)
        .exec()
        .await?
        .model()
        .await?;

    let jail_permissions = vec![CommandPermissions { id: CommandPermissionsType::Role(constants.party_role.id), permission: true}];

    let honor_command = interaction_client
        .create_guild_command(guild_id)
        .chat_input("honor", "Honor a user.")?
        .default_permission(false)
        .command_options(
            &[
                CommandOption::User(
                    BaseCommandOptionData {
                        name: "honoree".to_string(),
                        description: "User to be honored".to_string(),
                        required: true,
                    },
                ),
                CommandOption::Integer(
                    NumberCommandOptionData {
                        autocomplete: false,
                        choices: vec![
                            CommandOptionChoice::Int{name: "1".into(), value: 1},
                            CommandOptionChoice::Int{name: "5".into(), value: 5},
                            CommandOptionChoice::Int{name: "10".into(), value: 10},
                            CommandOptionChoice::Int{name: "25".into(), value: 25},
                        ],
                        description: "Amount of social credit to honor".into(),
                        max_value: None,
                        min_value: None,
                        name: "amount".into(),
                        required: false,
                    },
                ),
            ],
        )?
        .exec()
        .await?
        .model()
        .await?;

    let honor_permissions = vec![CommandPermissions { id: CommandPermissionsType::Role(constants.party_role.id), permission: true}];

    let dishonor_command = interaction_client
        .create_guild_command(guild_id)
        .chat_input("dishonor", "Dishonor a user.")?
        .default_permission(false)
        .command_options(
            &[
                CommandOption::User(
                    BaseCommandOptionData {
                        name: "dishonoree".to_string(),
                        description: "User to be dishonored".to_string(),
                        required: true,
                    },
                ),
                CommandOption::Integer(
                    NumberCommandOptionData {
                        autocomplete: false,
                        choices: vec![
                            CommandOptionChoice::Int{name: "1".into(), value: 1},
                            CommandOptionChoice::Int{name: "5".into(), value: 5},
                            CommandOptionChoice::Int{name: "10".into(), value: 10},
                            CommandOptionChoice::Int{name: "25".into(), value: 25},
                        ],
                        description: "Amount of social credit to dishonor".into(),
                        max_value: None,
                        min_value: None,
                        name: "amount".into(),
                        required: false,
                    },
                ),
            ],
        )?
        .exec()
        .await?
        .model()
        .await?;

    let dishonor_permissions = vec![CommandPermissions { id: CommandPermissionsType::Role(constants.party_role.id), permission: true}];

    let sync_command = interaction_client
        .create_guild_command(guild_id)
        .chat_input("sync", "Sync a user.")?
        .default_permission(false)
        .command_options(
            &[
                CommandOption::User(
                    BaseCommandOptionData {
                        name: "syncee".to_string(),
                        description: "User to be synced".to_string(),
                        required: false,
                    },
                ),
            ],
        )?
        .exec()
        .await?
        .model()
        .await?;

    let sync_permissions = vec![CommandPermissions { id: CommandPermissionsType::Role(constants.party_role.id), permission: true}];

    let name_command = interaction_client
        .create_guild_command(guild_id)
        .chat_input("name", "Change your username.")?
        .command_options(
            &[
                CommandOption::String(
                    ChoiceCommandOptionData {
                        autocomplete: false,
                        choices: vec![],
                        name: "name".into(),
                        required: false,
                        description: "Your new username (max 32 characters)".into(),
                    },
                ),
            ],
        )?
        .exec()
        .await?
        .model()
        .await?;

    let name_permissions = vec![];

    let exam_command = interaction_client
        .create_guild_command(guild_id)
        .chat_input("exam", "Administer an Exam")?
        .command_options(
            &[
                CommandOption::SubCommand(
                    OptionsCommandOptionData {
                        name:  "start".to_string(),
                        description: "Start an exam".to_string(),
                        options: vec![
                            CommandOption::String(
                                ChoiceCommandOptionData {
                                    autocomplete: false,
                                    choices: vec![
                                        CommandOptionChoice::String { name: "hsk1".to_string(), value: "hsk1".to_string(), },
                                        CommandOptionChoice::String { name: "hsk2".to_string(), value: "hsk2".to_string(), },
                                        CommandOptionChoice::String { name: "hsk3".to_string(), value: "hsk3".to_string(), },
                                        CommandOptionChoice::String { name: "hsk4".to_string(), value: "hsk4".to_string(), },
                                        CommandOptionChoice::String { name: "hsk5".to_string(), value: "hsk5".to_string(), },
                                        CommandOptionChoice::String { name: "hsk6".to_string(), value: "hsk6".to_string(), },
                                    ],
                                    name: "exam".into(),
                                    required: false,
                                    description: "Which exam to run".into(),
                                },
                            ),
                        ],
                    }
                ),
                CommandOption::SubCommand(
                    OptionsCommandOptionData {
                        name:  "quit".to_string(),
                        description: "Quit an exam in progress".to_string(),
                        options: vec![],
                    }
                ),
            ],
        )?
        .exec()
        .await?
        .model()
        .await?;

    let exam_permissions = vec![];

    let tag_command = interaction_client
        .create_guild_command(guild_id)
        .chat_input("tag", "Add or remove a tag from a user.")?
        .command_options(
            &[
                CommandOption::User(
                    BaseCommandOptionData {
                        name: "user".to_string(),
                        description: "User to be tagged or untagged".to_string(),
                        required: true,
                    },
                ),
                CommandOption::String(
                    ChoiceCommandOptionData {
                        name: "tag".into(),
                        autocomplete: false,
                        choices: vec![
                            CommandOptionChoice::String { name: "Learner".to_string(), value:  "Learner".to_string() },
                            CommandOptionChoice::String { name: "Party".to_string(), value:  "Party".to_string() },
                            CommandOptionChoice::String { name: "Art".to_string(), value:  "Art".to_string() },
                        ],
                        required: false,
                        description: "Tag to add or remove.".into(),
                    },
                ),
            ],
        )?
        .exec()
        .await?
        .model()
        .await?;

    let tag_permissions = vec![];

    Ok(Commands(vec![
        (jail_command, jail_permissions),
        (honor_command, honor_permissions),
        (dishonor_command, dishonor_permissions),
        (sync_command, sync_permissions),
        (name_command, name_permissions),
        (exam_command, exam_permissions),
        (tag_command, tag_permissions),
    ]))
}

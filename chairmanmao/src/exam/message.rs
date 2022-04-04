use crate::Error;
use crate::draw;

use twilight_http::Client;
use twilight_model::http::attachment::Attachment;

use super::active_exam::ActiveExam;
use super::{
    ExamScore,
    Answer,
    Question,
};
use twilight_util::builder::embed::{EmbedBuilder, EmbedFieldBuilder, EmbedAuthorBuilder, ImageSource};

pub async fn exam_start(client: &Client, active_exam: &ActiveExam) -> Result<(), Error> {
    let user = client.user(active_exam.user_id).exec().await?.model().await?;

    // TODO handle users with no avatar
    // cf https://github.com/Pycord-Development/pycord/blob/36a59259084fbfb44050c8c0119f45d956d8c972/discord/user.py#L138
    let avatar_url = format!("https://cdn.discordapp.com/avatars/{}/{}.png", user.id, user.avatar.unwrap().to_string());

    let author_name = format!("{}#{}", user.name, user.discriminator());

    let author = EmbedAuthorBuilder::new(author_name)
        .icon_url(ImageSource::url(avatar_url)?)
        .build();

    let max_wrong = match active_exam.exam.max_wrong {
        Some(n) => n.to_string(),
        None => "∞".to_string(),
    };

    let timelimit = format!("{} seconds", active_exam.exam.timelimit as f32 / 1000.0);

    let embed = EmbedBuilder::new()
        .author(author)
        .field(EmbedFieldBuilder::new("Deck", active_exam.exam.name.clone()).inline())
        .field(EmbedFieldBuilder::new("Questions", active_exam.exam.num_questions.to_string()).inline())
        .field(EmbedFieldBuilder::new("Time Limit", timelimit))
        .field(EmbedFieldBuilder::new("Mistakes Allowed", max_wrong))
        .color(0xFFA500)
        .build();

    client.create_message(active_exam.channel_id)
        .embeds(&[embed])?
        .exec()
        .await?;

    Ok(())
}

pub async fn pose_question(client: &Client, active_exam: &ActiveExam, question: &Question) -> Result<(), Error> {
    let image_bytes = draw::draw(&question.question);
    if let Err(e) = &image_bytes {
        println!("Error: {:?}", &e);
        return Err(format!("Error: {:?}", e).into());
    }
    let image_bytes = image_bytes.unwrap();
    let image_name = "image";
    let filename = format!("{image_name}.png");
    let attachment = Attachment::from_bytes(filename, image_bytes);

    client.create_message(active_exam.channel_id)
        .attachments(&[attachment])?
        .exec()
        .await?;
    Ok(())
}

pub async fn show_answer(client: &Client, active_exam: &ActiveExam, question: &Question, answer: &Answer) -> Result<(), Error> {
    let (emoji, color) = match answer {
        Answer::Correct(_s) => ("✅", 0x00FF00),
        Answer::Incorrect(_s) => ("❌", 0x00FF00),
        Answer::Timeout => ("⏲️", 0x00FF00),
        Answer::Quit => ("❌", 0x00FF00), // TODO: Use buneng emoji instead.
    };

    let correct_answer = format!("{} →  {}", answer_to_str(&answer), question.valid_answers[0]);

    let description = &format!("{emoji} {correct_answer}");

    let embed = EmbedBuilder::new()
        .description(description)
        .color(color)
        .build();

    client.create_message(active_exam.channel_id)
        .embeds(&[embed])?
        .exec()
        .await?;

    Ok(())
}

pub async fn timeout(client: &Client, active_exam: &ActiveExam, question: &Question) -> Result<(), Error> {
    let correct_answer = &question.valid_answers[0];
    client.create_message(active_exam.channel_id)
        .content(&format!("Timeout: {correct_answer}"))?
        .exec()
        .await?;
    Ok(())
}

pub async fn exam_end(client: &Client, active_exam: &ActiveExam, exam_score: ExamScore) -> Result<(), Error> {
    let user = client.user(active_exam.user_id).exec().await?.model().await?;

    // TODO handle users with no avatar
    // cf https://github.com/Pycord-Development/pycord/blob/36a59259084fbfb44050c8c0119f45d956d8c972/discord/user.py#L138
    let avatar_url = format!("https://cdn.discordapp.com/avatars/{}/{}.png", user.id, user.avatar.unwrap().to_string());
    let author_name = format!("{}#{}", user.name, user.discriminator());

    let author = EmbedAuthorBuilder::new(author_name)
        .icon_url(ImageSource::url(avatar_url)?)
        .build();

    let color = if exam_score.passed {
        0x00FF00
    } else {
        0xFF0000
    };

    let mut description = String::new();
    for (question, answer) in &exam_score.graded_questions {
        let correct = answer.is_correct();
        let emoji = if correct { "✅" } else { "❌" };
        let correct_answer = &question.valid_answers[0];
        let question_str = &question.question;  // (question.question).ljust(longest_answer + 2, "　")

        let answer_str = format!("{} → {}", answer_to_str(&answer), correct_answer);
        description.push_str(&format!("{emoji}　{question_str} {answer_str}　*{}*\n", question.meaning));
    }

    let embed = EmbedBuilder::new()
        .author(author)
        .description(description)
//            .field(EmbedFieldBuilder::new("Mistakes Allowed", max_wrong)) // TODO
        .color(color)
        .build();

    client.create_message(active_exam.channel_id)
        .embeds(&[embed])?
        .exec()
        .await?;

    Ok(())
}

fn answer_to_str(answer: &Answer) -> &str {
    match answer {
        Answer::Correct(s) => s,
        Answer::Incorrect(s) => s,
        Answer::Timeout => "\\*timeout\\*",
        Answer::Quit => "\\*quit\\*",
    }
}

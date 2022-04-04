use std::collections::HashMap;
use serde::{Deserialize};
use serde_json;
use crate::exam::exam::{Exam, Question};


#[derive(Deserialize, Debug)]
struct JsonExam {
    name: String,

    #[serde(rename = "numQuestions")]
    num_questions: usize,

    #[serde(rename = "maxWrong")]
    max_wrong: usize,

    timelimit: usize,

    #[serde(rename = "hskLevel")]
    hsk_level: usize,

    deck: Vec<JsonCard>,
}

#[derive(Deserialize, Debug)]
struct JsonCard {
    question: String,

    #[serde(rename = "validAnswers")]
    valid_answers: Vec<String>,
    meaning: String,
}

fn convert_card(json_card: &JsonCard) -> Question {
    let JsonCard {
        question,
        valid_answers,
        meaning,
    } = json_card;

    Question {
        question: question.clone(),
        valid_answers: valid_answers.clone(),
        meaning: meaning.clone(),
    }
}

fn convert_exam(json_exam: &JsonExam) -> Exam {
    let JsonExam {
        name,
        num_questions,
        max_wrong,
        timelimit,
        hsk_level,
        deck,
    } = json_exam;

    let deck = deck.iter().map(|json_card| convert_card(json_card)).collect::<Vec<_>>();
    let max_wrong = Some(*max_wrong);
    let timelimit = *timelimit * 1000; // convert from s to ms

    Exam {
        name: name.to_owned(),
        deck,
        num_questions: *num_questions,
        max_wrong,
        timelimit,
        hsk_level: *hsk_level,
    }
}


pub fn load_exam(exam_name: &str) -> Exam {
    let exam_dirname = std::path::Path::new(&std::env::var("DATA_DIR").unwrap()).join("exams");
    let exam_filepath = exam_dirname.join(format!("{}.json", exam_name));
    let exam_json = std::fs::read_to_string(exam_filepath).unwrap();
    let exam_data: serde_json::Value = serde_json::from_str(&exam_json).unwrap();
    let json_exam: JsonExam = JsonExam::deserialize(exam_data).unwrap();
    convert_exam(&json_exam)
}

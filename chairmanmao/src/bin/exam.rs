use std::collections::HashMap;
use serde::{Deserialize};
use serde_json;
use chairmanmao::exam::{Exam, Examiner, TickResult, Question, Answer};


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


fn load_exam(exam_name: &str) -> Exam {
    let mut exams: HashMap<String, Exam> = HashMap::new();

    let exam_json = std::fs::read_to_string("data/exams.json").unwrap();
    let exam_data: serde_json::Value = serde_json::from_str(&exam_json).unwrap();
    for exam in exam_data["data"]["exams"].as_array().unwrap().iter() {
        let json_exam: JsonExam = JsonExam::deserialize(exam).unwrap();
        let exam_name = json_exam.name.clone();
        let exam = convert_exam(&json_exam);
        exams.insert(exam_name, exam);
    }

    exams[exam_name].clone()
}

fn main() {
    let exam = load_exam("hsk1");

    let (tx, rx) = std::sync::mpsc::channel::<String>();

    let seed = 10;
    let mut examiner = Examiner::make(&exam, 100, seed);

    let examiner_thread = std::thread::spawn(move || {
        loop {
            let tick_result = examiner.tick();
            match tick_result {
                TickResult::Nothing => (),
                TickResult::NextQuestion(q) => {
                    println!("Question: {}", q.question);
                },
                TickResult::Pause => (),
                TickResult::Timeout => {
                    println!("*timeout*");
                    println!();
                },
                TickResult::Finished(score) => {
                    return score;
                }
            };
            std::thread::sleep(std::time::Duration::from_millis(100));
            if let Ok(answer) = rx.try_recv() {
                if answer == "!quit" {
                    examiner.give_up();
                } else if let Some((question, answer)) = examiner.answer(&answer) {
                    if let Answer::Correct(_) = answer {
                        println!("CORRECT");
                    } else {
                        println!("INCORRECT: {}", &question.valid_answers[0]);
                    }
                    println!();
                }
                // } else { not ready to receive an answer }
            }
        }
    });

    let _read_thread = std::thread::spawn(move || {
        use std::io::prelude::*;
        let stdin = std::io::stdin();
        for line in stdin.lock().lines() {
            let line = line.unwrap();
            tx.send(line).unwrap();
        }
    });

    let score = examiner_thread.join().unwrap();

    println!("Exam Complete");
    println!("Score: {:.1}%  {}", score.score*100.0, if score.passed { "PASSED" } else { "FAILED" });
    println!("Questions:");
    for (question, answer) in &score.graded_questions {
        println!("    {:10}    {:?}", question.question, answer);
    }

}

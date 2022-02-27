/// [TickResult] is the result you get from calling [Examiner::tick].
#[derive(Debug)]
pub enum TickResult {
    /// Nothing interesting happened on this tick.
    Nothing,
    /// The current question timed out on this tick.
    /// An [Answer::Timeout] was recorded and we enter a 1 second pause state
    /// before the next question is presented.
    Timeout,
    /// The next question is available.
    NextQuestion(Question),
    /// We are currently in a pause state caused by a timeout.
    Pause,
    /// The exam finished. The [ExamScore] is provided as a result.
    Finished(ExamScore),
}

#[derive(Debug, Clone)]
pub struct Exam {
    pub name: String,
    pub deck: Vec<Question>,
    pub num_questions: usize,
    pub max_wrong: Option<usize>,
    pub timelimit: usize,
    pub hsk_level: usize,
}

#[derive(Clone, Debug)]
pub struct Question {
    pub question: String,
    pub valid_answers: Vec<String>,
    pub meaning: String,
}

impl Question {
    pub fn is_correct(&self, answer: &str) -> bool {
        for valid_answer in self.valid_answers.iter() {
            let answer_fixed = answer.to_lowercase().replace(" ", "").replace("5", "");
            let valid_answer_fixed = valid_answer.to_lowercase().replace(" ", "").replace("5", "");

            if answer_fixed == valid_answer_fixed {
                return true;
            }
        }

        false
    }
}

#[derive(Clone, Debug)]
pub enum Answer {
    Timeout,
    Quit,
    Correct(String),
    Incorrect(String),
}

impl Answer {
    fn is_quit(&self) -> bool {
        if let Answer::Quit = self {
            return true;
        } else {
            return false;
        }
    }

    pub fn is_correct(&self) -> bool {
        if let Answer::Correct(_) = self {
            return true;
        } else {
            return false;
        }
    }

    fn is_timeout(&self) -> bool {
        if let Answer::Timeout = self {
            return true;
        } else {
            return false;
        }
    }
}

/// [Examiner] is the state machine which administers an exam.
///
/// The general pattern for using it is to first call [Examiner::tick()] to get the first question.
/// Then, subsequent calls to [Examiner::tick()] will progress the machine. This should be called
/// every `millis_per_tick` seconds (as provided by [Examiner::make()]).
/// The return value of [Examiner::tick()] is a [TickResult]. It tells you the result of the
/// tick and indicates what state change took place (if any).
///
/// When the user answers a question, call [Examiner::answer()] to supply it to the machine.
/// The next call to [Examiner::tick()] will acknowledge the result.
///
/// The exam ends once [Examiner::tick()] returns [TickResult::Finished].
#[derive(Debug)]
pub struct Examiner {
    // Constants
    questions: Vec<Question>,
    max_wrong: Option<usize>,
    timelimit: usize,
    fail_on_timeout: bool,
    millis_per_tick: usize,
    //practice: bool,

    // Variables
    current_question_index: isize,
    current_question_time_left: usize,
    answers_given: Vec<Answer>,
    pause_time: usize,
}

impl Examiner {
    pub fn make(exam: &Exam, millis_per_tick: usize, seed: u64) -> Examiner {
        use rand::rngs::StdRng;
        use rand::SeedableRng;
        let mut rng = StdRng::seed_from_u64(seed);

        let practice = false;

        let mut questions = exam.deck.clone();

        use rand::seq::SliceRandom;
        questions.shuffle(&mut rng);
        if !practice {
            questions.truncate(exam.num_questions);
        }

        let timelimit = if !practice { exam.timelimit } else { 30000 };
        let max_wrong = if !practice { exam.max_wrong } else { None };

        Examiner {
            questions,
            millis_per_tick,
            max_wrong,
            timelimit: timelimit,
            fail_on_timeout: practice,
            //practice: practice,
            current_question_index: -1,
            current_question_time_left: timelimit,
            answers_given: vec![],
            pause_time: 0,
        }
    }

//    ####################################################################
//    # Queries
//    ####################################################################

    fn current_question(&self) -> &Question {
        assert!(self.current_question_index >= 0, "You must call tick() before the first question.");
        // TODO Handle case where current_question_index > len(self.questions)
        &self.questions[self.current_question_index as usize]
    }

    fn ready_for_next_question(&self) -> bool {
        (self.current_question_index + 1) == self.answers_given.len() as isize
    }

    fn ready_for_next_answer(&self) -> bool {
        self.current_question_index == self.answers_given.len() as isize
    }

    fn number_wrong(&self) -> usize {
        let questions = &self.questions[0..self.answers_given.len()];

        let mut number_wrong = 0;

        for (_question, answer) in questions.iter().zip(self.answers_given.iter()) {
            if !answer.is_correct() {
                number_wrong += 1;
            }
        }

        number_wrong
    }

    fn score(&self) -> ExamScore {
        let score = 1.0 - self.number_wrong() as f32 / self.answers_given.len() as f32;
        let passed = self.passed();
        let graded_questions = self.graded_questions();
        ExamScore {
            score,
            passed,
            graded_questions,
        }
    }

    fn passed(&self) -> bool {
        assert!(self.finished(), "Exam is not finished");
        if let Some(max_wrong) = self.max_wrong {
            self._finished_gave_up() && self.number_wrong() <= max_wrong
        } else {
            false
        }
    }

    fn finished(&self) -> bool {
        self._finished_gave_up()
        || self._finished_too_many_wrong()
        || self._finished_all_questions_answered()
        || self._finished_timeout()
    }

    fn _finished_gave_up(&self) -> bool {
        for answer in self.answers_given.iter() {
            if answer.is_quit() {
                return true;
            }
        }
        false
    }

    fn _finished_too_many_wrong(&self) -> bool {
        if let Some(max_wrong) = self.max_wrong {
            self.number_wrong() > max_wrong
        } else {
            false
        }
    }

    fn _finished_all_questions_answered(&self) -> bool {
        self.answers_given.len() == self.questions.len()
    }

    fn _finished_timeout(&self) -> bool {
        self.fail_on_timeout && self._number_timeouts() > 0
    }

    fn _number_timeouts(&self) -> usize {
        let mut number_timeout = 0;
        for answer in self.answers_given.iter() {
            if answer.is_timeout() {
                number_timeout += 1
            }
        }
        number_timeout
    }

    fn graded_questions(&self) -> Vec<(Question, Answer)> {
        let num_questions_answered = self.answers_given.len();
        let questions = self.questions[..num_questions_answered].to_owned();

        let mut results = Vec::new();

        for (question, answer) in questions.iter().zip(self.answers_given.iter()) {
            results.push((question.clone(), answer.clone()));
        }

        results
    }

    fn timed_out(&self) -> bool {
        self.current_question_time_left <= 0
    }

//    ####################################################################
//    # Actions
//    ####################################################################
//
    pub fn tick(&mut self) -> TickResult {
        if self.finished() {
            TickResult::Finished(self.score())
        } else if self.pause_time > 0 {
            self.pause_time -= self.millis_per_tick;
            TickResult::Pause
        } else if self.ready_for_next_question() {
            self.current_question_index += 1;
            self.current_question_time_left = self.timelimit;
            TickResult::NextQuestion(self.current_question().clone())
        } else if self.timed_out() {
            self.answers_given.push(Answer::Timeout);
            self.pause_time = 1000;
            TickResult::Timeout
        } else {
            self.current_question_time_left -= self.millis_per_tick;
            TickResult::Nothing
        }
    }

    pub fn answer(&mut self, answer: &str) -> Option<(Question, Answer)> {
        if self.finished() || !self.ready_for_next_answer() || self.pause_time > 0 {
            return None;
        }

        let current_question = self.current_question().clone();
        let correct = current_question.is_correct(answer);


        let answer = if correct {
            Answer::Correct(answer.to_string())
        } else {
            Answer::Incorrect(answer.to_string())
        };

        self.answers_given.push(answer.clone());

        Some((current_question, answer))
    }

    pub fn give_up(&mut self) {
        assert!(self.ready_for_next_answer(), "Can't give_up until the next tick.");
        self.answers_given.push(Answer::Quit)
    }
}


#[derive(Debug)]
pub struct ExamScore {
    pub passed: bool,
    pub score: f32,

    pub graded_questions: Vec<(Question, Answer)>,
}

#[cfg(test)]
impl TickResult {
    fn unwrap_next_question(self) -> Question {
        if let TickResult::NextQuestion(question) = self {
            question
        } else {
            panic!("Expected TickResult::NextQuestion(_), but found {:?}", self);
        }
    }
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test1() {
        let name = "hsk1".to_string();
        let deck = vec![
            Question {
                question: "hello".to_string(),
                valid_answers: vec!["world".to_string()],
                meaning: "Greeting".to_string(),
            },
            Question {
                question: "foo".to_string(),
                valid_answers: vec!["bar".to_string()],
                meaning: "foobar".to_string(),
            },
            Question {
                question: "foobar".to_string(),
                valid_answers: vec!["baz".to_string()],
                meaning: "foobar~baz".to_string(),
            },
        ];

        let num_questions = 1;
        let max_wrong = Some(1);
        let timelimit = 5;
        let hsk_level = 1;

        let exam = Exam {
            name,
            deck,
            num_questions,
            max_wrong,
            timelimit,
            hsk_level,
        };

        let mut examiner = Examiner::make(&exam, 100, 0);
        let tick_result = examiner.tick();
        let question = tick_result.unwrap_next_question();

        println!("{}", question.question);
        examiner.answer("world");
        let tick_result = examiner.tick();
        dbg!(&tick_result);
    }
}

pub mod load {
    use super::*;
    use std::collections::HashMap;
    use serde::{Deserialize};
    use serde_json;


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
        let mut exams: HashMap<String, Exam> = HashMap::new();

        let exam_json = std::fs::read_to_string("data/exams.json").unwrap();
        let exam_data: serde_json::Value = serde_json::from_str(&exam_json).unwrap();
        for exam in exam_data["data"]["exams"].as_array().unwrap().iter() {
            let json_exam: JsonExam = JsonExam::deserialize(exam).unwrap();
            let exam_name = json_exam.name.clone();
            println!("Exam found: {}", json_exam.name);
            let exam = convert_exam(&json_exam);
            exams.insert(exam_name, exam);
        }

        exams[exam_name].clone()
    }
}

use twilight_model::id::Id;
use twilight_model::id::marker::{ChannelMarker, UserMarker};
use super::exam::{Exam, Examiner};

#[derive(Clone)]
pub struct ActiveExam {
    pub user_id: Id<UserMarker>,
    pub channel_id: Id<ChannelMarker>,
    pub examiner: Examiner,
    pub exam: Exam,
    pub seed: u64,
}

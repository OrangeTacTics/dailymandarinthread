use crate::ChairmanMao;
use twilight_model::gateway::event::Event;

pub trait Cog {
    fn on_event(&mut self, chairmanmao: &ChairmanMao, event: &Event);
}

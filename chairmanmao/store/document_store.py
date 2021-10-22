import typing as t
import abc

from .types import UserId, Profile, ServerSettings, Exam


class DocumentStore(abc.ABC):
    def create_profile(self, user_id: UserId, discord_username: str) -> Profile:
        pass

    def profile_exists(self, user_id: UserId) -> bool:
        pass

    def load_profile_by_discord_username(self, discord_username: str) -> Profile:
        pass

    def load_profile(self, user_id: UserId) -> Profile:
        pass

    def store_profile(self, profile: Profile) -> None:
        pass

    def get_all_profiles(self) -> t.List[Profile]:
        pass

    def get_exam_names(self) -> t.List[str]:
        pass

    def load_exam(self, exam_name: str) -> t.Optional[Exam]:
        pass

    def store_exam(self, exam: Exam) -> None:
        pass

    def profile(self, user_id: UserId) -> "OpenProfileContextManager":
        return OpenProfileContextManager(self, user_id)

    def load_server_settings(self) -> ServerSettings:
        pass

    def store_server_settings(self, ServerSettings) -> None:
        pass


class OpenProfileContextManager:
    def __init__(self, store: DocumentStore, user_id: UserId) -> None:
        self.store = store
        self.user_id = user_id
        self.profile: t.Optional[Profile] = None

    def __enter__(self) -> Profile:
        self.profile = self.store.load_profile(self.user_id)
        return self.profile

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        assert self.profile is not None
        assert self.profile.user_id == self.user_id
        self.store.store_profile(self.profile)

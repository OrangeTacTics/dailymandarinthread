from __future__ import annotations
import typing as t
from dataclasses import dataclass

from datetime import datetime
import dmt_chairmanmao.types as types


from dmt_chairmanmao.api_client import GraphQLClient


UserId = int


@dataclass
class LeaderboardEntry:
    display_name: str
    credit: int


@dataclass
class SyncInfo:
    user_id: UserId
    display_name: str
    credit: int
    roles: t.Set[str]
    hsk_level: t.Optional[int]


@dataclass
class DictEntry:
    simplified: str
    traditional: str
    pinyin: str
    zhuyin: str
    meanings: t.List[str]


@dataclass
class Api:
    def __init__(self, endpoint: str, auth_token: str) -> None:
        self.client = GraphQLClient(endpoint, auth_token)

    async def is_registered(self, user_id: UserId) -> bool:
        results = await self.client.named_query(
            "isRegistered",
            {
                "userId": str(user_id),
            },
        )
        return results["profile"] is not None

    async def register(self, user_id: UserId, discord_username: str) -> None:
        await self.client.named_query(
            "register",
            {
                "userId": str(user_id),
                "discordUsername": discord_username,
            },
        )

    async def get_sync_info(self, user_id: UserId) -> SyncInfo:
        results = await self.client.named_query(
            "getSyncInfo",
            {
                "userId": str(user_id),
            },
        )
        profile = results["profile"]

        roles = []
        if "Jailed" in profile["roles"]:
            roles.append("Jailed")
        else:
            roles.append("Comrade")

            if "Party" in profile["roles"]:
                roles.append("Party")
            if "Learner" in profile["roles"]:
                roles.append("Learner")

        return SyncInfo(
            user_id=int(profile["userId"]),
            display_name=profile["displayName"],
            credit=profile["credit"],
            roles=set(roles),
            hsk_level=profile["hsk"],
        )

    async def sync_users(self, user_ids: t.List[UserId]) -> None:
        await self.client.named_query(
            "syncUsers",
            {
                "userIds": user_ids,
            },
        )

    async def get_user_id(self, discord_username: str) -> UserId:
        results = await self.client.named_query(
            "getUserId",
            {
                "discordUsername": discord_username,
            },
        )
        return results["profile"]["userId"]

    async def honor(
        self,
        user_id: UserId,
        honorer_user_id: UserId,
        credit: int,
        reason: str,
    ) -> int:
        results = await self.client.named_query(
            "honor",
            {
                "userId": str(user_id),
                "honorerUserId": str(honorer_user_id),
                "credit": credit,
                "reason": reason,
            },
        )
        return results["admin"]["honor"]["credit"]

    async def dishonor(
        self,
        user_id: UserId,
        honorer_user_id: UserId,
        credit: int,
        reason: str,
    ) -> int:
        results = await self.client.named_query(
            "dishonor",
            {
                "userId": str(user_id),
                "honorerUserId": str(honorer_user_id),
                "credit": credit,
                "reason": reason,
            },
        )
        return results["admin"]["dishonor"]["credit"]

    async def promote(self, user_id: UserId) -> None:
        await self.client.named_query(
            "promote",
            {
                "userId": str(user_id),
            },
        )

    async def demote(self, user_id: UserId) -> None:
        await self.client.named_query(
            "demote",
            {
                "userId": str(user_id),
            },
        )

    async def get_hsk(self, user_id: UserId) -> t.Optional[int]:
        results = await self.client.named_query(
            "getHsk",
            {
                "userId": str(user_id),
            },
        )
        return results["profile"]["hsk"]

    async def set_hsk(self, user_id: UserId, hsk_level: t.Optional[int]) -> None:
        await self.client.named_query(
            "setHsk",
            {
                "userId": str(user_id),
                "hsk": hsk_level,
            },
        )

    async def set_defected(self, user_id: UserId, flag: bool) -> None:
        await self.client.named_query(
            "setDefected",
            {
                "userId": str(user_id),
                "flag": flag,
            },
        )

    async def last_seen(self, user_id: UserId) -> datetime:
        results = await self.client.named_query(
            "lastSeen",
            {
                "userId": str(user_id),
            },
        )
        return datetime.fromisoformat(results["profile"]["lastSeen"])

    async def jail(
        self,
        user_id: UserId,
        jailer_user_id: UserId,
        reason: str,
    ) -> None:
        await self.client.named_query(
            "jail",
            {
                "userId": str(user_id),
                "jailerUserId": str(jailer_user_id),
                "reason": reason,
            },
        )

    async def unjail(
        self,
        user_id: UserId,
        jailer_user_id: UserId,
    ) -> None:
        await self.client.named_query(
            "unjail",
            {
                "userId": str(user_id),
                "jailerUserId": str(jailer_user_id),
            },
        )

    async def get_discord_username(self, user_id: UserId) -> str:
        results = await self.client.named_query(
            "getDiscordUsername",
            {
                "userId": str(user_id),
            },
        )
        return results["profile"]["discordUsername"]

    async def get_display_name(self, user_id: UserId) -> str:
        results = await self.client.named_query(
            "getDisplayName",
            {
                "userId": str(user_id),
            },
        )
        return results["profile"]["displayName"]

    async def social_credit(self, user_id: UserId) -> int:
        results = await self.client.named_query(
            "socialCredit",
            {
                "userId": str(user_id),
            },
        )
        return results["profile"]["credit"]

    async def set_learner(self, user_id: UserId, flag: bool) -> None:
        await self.client.named_query(
            "setLearner",
            {
                "userId": str(user_id),
                "flag": flag,
            },
        )

    async def draw(self, font_name: str, text: str) -> None:
        ...

    async def upload_font(self, font_name: str, font_data: bytes) -> None:
        ...

    async def mine(self, user_id: UserId, word: str) -> None:
        await self.client.named_query(
            "mine",
            {
                "userId": str(user_id),
                "words": [word],
            },
        )

    async def get_mined(self, user_id: UserId) -> t.List[str]:
        results = await self.client.named_query(
            "getMined",
            {
                "userId": str(user_id),
            },
        )

        return results["profile"]["minedWords"]

    async def yuan(self, user_id) -> int:
        results = await self.client.named_query(
            "yuan",
            {
                "userId": str(user_id),
            },
        )
        return results["profile"]["yuan"]

    async def transfer(self, from_user_id: UserId, to_user_id: UserId, amount: int):
        await self.client.named_query(
            "transfer",
            {
                "fromUserId": str(from_user_id),
                "toUserId": str(to_user_id),
                "amount": amount,
            },
        )

    async def leaderboard(self) -> t.List[LeaderboardEntry]:
        results = await self.client.named_query(
            "leaderboard",
        )

        entries = []
        for profile in results["leaderboard"]:
            entries.append(
                LeaderboardEntry(
                    display_name=profile["displayName"],
                    credit=profile["credit"],
                )
            )

        return entries

    async def set_name(self, user_id, name: str) -> None:
        await self.client.named_query(
            "setName",
            {
                "userId": str(user_id),
                "name": name,
            },
        )

    async def get_name(self, user_id: UserId) -> str:
        return await self.get_display_name(user_id)

    async def alert_activity(self, user_ids: t.List[UserId]) -> None:
        await self.client.named_query(
            "alertActivity",
            {
                "userIds": [str(user_id) for user_id in user_ids],
            },
        )

    async def last_bump(self) -> datetime:
        results = await self.client.named_query(
            "lastBump",
        )
        return datetime.fromisoformat(results["admin"]["serverSettings"]["lastBump"])

    async def bump(self, user_id: UserId) -> datetime:
        results = await self.client.named_query(
            "setLastBump",
            {
                "userId": user_id,
            },
        )
        return datetime.fromisoformat(results["admin"]["setLastBump"])

    async def lookup_word(self, word: str) -> t.List[DictEntry]:
        results = await self.client.named_query(
            "lookupWord",
            {
                "word": word,
            },
        )
        return [
            DictEntry(
                simplified=result["simplified"],
                traditional=result["traditional"],
                pinyin=result["pinyin"],
                zhuyin=result["zhuyin"],
                meanings=result["meanings"],
            )
            for result in results["dict"]
        ]

    async def exams_disabled(self) -> bool:
        results = await self.client.named_query(
            "examsDisabled",
        )
        return results["admin"]["serverSettings"]["examsDisabled"]

    async def disable_exams(self, flag: bool) -> None:
        await self.client.named_query(
            "disableExams",
            {
                "flag": flag,
            },
        )

    async def get_bot_and_admin_usernames(self) -> t.Tuple[str, str]:
        results = await self.client.named_query(
            "getBotAndAdminUsernames",
        )
        server_settings = results["admin"]["serverSettings"]
        return (
            server_settings["botUsername"],
            server_settings["adminUsername"],
        )

    async def get_exam_names(self) -> t.List[str]:
        results = await self.client.named_query(
            "getExamNames",
        )
        return [exam["name"] for exam in results["exams"]]

    async def exam(self, exam_name: str) -> t.Optional[types.Exam]:
        results = await self.client.named_query(
            "exam",
            {
                "name": exam_name,
            },
        )
        return types.Exam(
            name=results["exam"]["name"],
            num_questions=results["exam"]["numQuestions"],
            max_wrong=results["exam"]["maxWrong"],
            timelimit=results["exam"]["timelimit"],
            hsk_level=results["exam"]["hskLevel"],
            deck=[
                types.Question(
                    question=card["question"],
                    meaning=card["meaning"],
                    valid_answers=card["validAnswers"],
                )
                for card in results["exam"]["deck"]
            ],
        )

    async def edit_exam_answers(
        self,
        exam_name: str,
        question: str,
        *,
        new_valid_answers: t.Optional[t.List[str]] = None,
    ) -> None:
        await self.client.named_query(
            "editExamAnswers",
            {
                "examName": exam_name,
                "question": question,
                "validAnswers": new_valid_answers,
            },
        )

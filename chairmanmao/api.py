from __future__ import annotations
import typing as t
from dataclasses import dataclass

from datetime import datetime
import chairmanmao.types as cmt


from chairmanmao.api_client import GraphQLClient


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
    roles: t.Set[cmt.Role]
    hsk_level: t.Optional[int]


@dataclass
class Api:
    def __init__(self, endpoint: str, auth_token: str) -> None:
        self.client = GraphQLClient(endpoint, auth_token)

    async def is_registered(self, user_id: UserId) -> bool:
        results = await self.client.query('''
            query q($userId: String!) {
                profile(userId: $userId) {
                    userId
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )
        return results['profile'] is not None

    async def register(self, user_id: UserId, discord_username: str) -> None:
        await self.client.query('''
            mutation m($userId: String!, $discordUsername: String!) {
                admin {
                    register(userId: $userId, discordUsername: $discordUsername) {
                        userId
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
                'discordUsername': discord_username,
            },
        )

    async def get_sync_info(self, user_id: UserId) -> SyncInfo:
        results = await self.client.query('''
            query hsk($userId: String!) {
                profile(userId: $userId) {
                    userId
                    displayName
                    credit
                    roles
                    hsk
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )
        profile = results['profile']

        roles = []
        if 'Jailed' in profile['roles']:
            roles.append(cmt.Role.Jailed)
        else:
            if 'Party' in profile['roles']:
                roles.append(cmt.Role.Party)
            if 'Learner' in profile['roles']:
                roles.append(cmt.Role.Learner)

        return SyncInfo(
            user_id=int(profile['userId']),
            display_name=profile['displayName'],
            credit=profile['credit'],
            roles=set(roles),
            hsk_level=profile['hsk'],
        )

    async def get_user_id(self, discord_username: str) -> UserId:
        results = await self.client.query('''
            query q($discordUsername: String!) {
                profile(discordUsername: $discordUsername) {
                    userId
                }
            }
            ''',
            {
                'discordUsername': discord_username,
            },
        )
        return results['profile']['userId']

    async def honor(self, user_id: UserId, credit: int) -> int:
        results = await self.client.query('''
            mutation m($userId: String!, $credit: Int!) {
                admin {
                    honor(userId: $userId, amount: $credit) {
                        credit
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
                'credit': credit,
            },
        )
        return results['admin']['honor']['credit']

    async def dishonor(self, user_id: UserId, credit: int) -> int:
        results = await self.client.query('''
            mutation m($userId: String!, $credit: Int!) {
                admin {
                    dishonor(userId: $userId, amount: $credit) {
                        credit
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
                'credit': credit,
            },
        )
        return results['admin']['dishonor']['credit']

    async def promote(self, user_id: UserId) -> None:
        await self.client.query('''
            mutation m($userId: String!) {
                admin {
                    setParty(userId: $userId, flag: true) {
                        userId
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )

    async def demote(self, user_id: UserId) -> None:
        await self.client.query('''
            mutation m($userId: String!) {
                admin {
                    setParty(userId: $userId, flag: false) {
                        userId
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )

    async def get_hsk(self, user_id: UserId) -> t.Optional[int]:
        results = await self.client.query('''
            query hsk($userId: String!) {
                profile(userId: $userId) {
                    hsk
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )
        return results['profile']['hsk']

    async def set_hsk(self, user_id: UserId, hsk_level: t.Optional[int]) -> None:
        await self.client.query('''
            mutation m($userId: String!, $hsk: Int) {
                admin {
                    setHsk(userId: $userId, hsk: $hsk) {
                        userId
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
                'hsk': hsk_level,
            },
        )

    async def last_seen(self, user_id: UserId) -> datetime:
        results = await self.client.query('''
            query q($userId: String!) {
                profile(userId: $userId) {
                    lastSeen
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )
        return datetime.fromisoformat(results['profile']['lastSeen'])

    async def jail(self, user_id: UserId) -> None:
       await self.client.query('''
            mutation m($userId: String!) {
                admin {
                    jail(userId: $userId) {
                        userId
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )

    async def unjail(self, user_id: UserId) -> None:
       await self.client.query('''
            mutation m($userId: String!) {
                admin {
                    unjail(userId: $userId) {
                        userId
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )

    async def get_discord_username(self, user_id: UserId) -> str:
        results = await self.client.query('''
            query q($userId: String!) {
                profile(userId: $userId) {
                    discordUsername
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )
        return results['profile']['discordUsername']

    async def get_display_name(self, user_id: UserId) -> str:
        results = await self.client.query('''
            query q($userId: String!) {
                profile(userId: $userId) {
                    displayName
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )
        return results['profile']['displayName']

    async def social_credit(self, user_id: UserId) -> int:
        results = await self.client.query('''
            query q($userId: String!) {
                profile(userId: $userId) {
                    credit
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )
        return results['profile']['credit']

    async def set_learner(self, user_id: UserId, flag: bool) -> None:
        await self.client.query('''
            mutation m($userId: String!, $flag: Boolean!) {
                admin {
                    setLearner(userId: $userId, flag: $flag) {
                        userId
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
                'flag': flag,
            },
        )

    async def draw(self, font_name: str, text: str) -> None:
        ...

    async def upload_font(self, font_name: str, font_data: bytes) -> None:
        ...

    async def mine(self, user_id: UserId, word: str) -> None:
        await self.client.query('''
            mutation alert($userId: String!, $words: [String!]!) {
                admin {
                    mine(userId: $userId, words: $words) {
                        userId
                    }
                }
            }
            ''',
            {
                'userId': str(user_id),
                'words': [word],
            },
        )

    async def yuan(self, user_id) -> int:
        results = await self.client.query('''
            query q($userId: String!) {
                profile(userId: $userId) {
                    yuan
                }
            }
            ''',
            {
                'userId': str(user_id),
            },
        )
        return results['profile']['yuan']

    async def transfer(self, from_user_id: UserId, to_user_id: UserId, amount: int):
        await self.client.query('''
            mutation m($fromUserId: String!, $toUserId: String!, $amount: Int!) {
                admin {
                    transfer(
                        fromUserId: $fromUserId,
                        toUserId: $toUserId,
                        amount: $amount,
                    )
                }
            }
            ''',
            {
                'fromUserId': str(from_user_id),
                'toUserId': str(to_user_id),
                'amount': amount,
            },
        )

    async def leaderboard(self) -> t.List[LeaderboardEntry]:
        results = await self.client.query('''
            query q {
                leaderboard {
                    displayName
                    credit
                }
            }
            '''
        )

        entries = []
        for profile in results['leaderboard']:
            entries.append(LeaderboardEntry(
                display_name=profile['displayName'],
                credit=profile['credit'],
            ))

        return entries

    async def set_name(self, user_id, name: str) -> None:
        await self.client.query('''
            mutation alert($userId: String!, $name: String!) {
                admin {
                    setName(userId: $userId, name: $name)
                }
            }
            ''',
            {
                'userId': str(user_id),
                'name': name,

            },
        )

    async def get_name(self, user_id: UserId) -> str:
        return await self.get_display_name(user_id)

    async def alert_activity(self, user_id: UserId) -> None:
        await self.client.query('''
            mutation alert($userIds: [String!]!) {
                admin {
                    alertActivity(userIds: $userIds)
                }
            }
            ''',
            {
                'userIds': [str(user_id)],
            },
        )

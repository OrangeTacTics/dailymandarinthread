import typing as t
from datetime import datetime

from strawberry.dataloader import DataLoader

import chairmanmao.graphql.schema as schema
from chairmanmao.store import DocumentStore


async def load_profiles(store: DocumentStore, user_ids: t.List[str]) -> t.List[schema.Profile]:
    results = []
    for user_id in user_ids:
        profile = store.load_profile(user_id)

        results.append(
            schema.Profile(
                userId=str(profile.user_id),
                discord_username=profile.discord_username,
                display_name=profile.display_name,
                credit=profile.credit,
                hanzi=[],
                mined_words=[],
                roles=[],
                created=datetime.now(),
                last_message=datetime.now(),
                yuan=0,
            )
        )
    
    return results

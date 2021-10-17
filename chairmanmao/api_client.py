import typing as t
import jwt
import json
import httpx
import os
from dotenv import load_dotenv


class GraphQLClient:
    def __init__(self, endpoint: str, auth_token: t.Optional[str] = None) -> None:
        self.endpoint = endpoint
        self.auth_token = auth_token

    async def query(self, query: str, variables: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        async with httpx.AsyncClient() as client:
            headers = {
                'Content-Type': 'application/json',
            }
            if self.auth_token is not None:
                headers['Authorization'] = f'BEARER {self.auth_token}'

            payload: t.Dict[str, t.Any] = {
                'query': query,
            }

            if variables is not None:
                payload['variables'] = variables

            res = await client.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=None,
            )

            res_json = res.json()
            if 'errors' in res_json:
                raise Exception(res_json['errors'])
            return res_json['data']

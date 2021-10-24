import typing as t
import httpx


class GraphQLClient:
    def __init__(self, endpoint: str, auth_token: t.Optional[str] = None) -> None:
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.queries: t.Dict[str, str] = {}
        self._load_queries()

    async def query(self, query: str, variables: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
            }
            if self.auth_token is not None:
                headers["Authorization"] = f"BEARER {self.auth_token}"

            payload: t.Dict[str, t.Any] = {
                "query": query,
            }

            if variables is not None:
                payload["variables"] = variables

            res = await client.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=None,
            )

            res_json = res.json()
            if "errors" in res_json:
                raise Exception(res_json["errors"])
            return res_json["data"]

    async def named_query(self, query_name: str, variables: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        query = self.queries[query_name]
        return await self.query(query, variables)

    def _load_queries(self) -> None:
        with open('data/queries.graphql') as infile:
            query_lines = []
            for line in infile:
                query_lines.append(line)
                if line.rstrip() == '}':
                    query = '\n'.join(query_lines).strip()
                    query_name = self._query_name(query)
                    self.queries[query_name] = query
                    query_lines = []

    def _query_name(self, query: str) -> str:
        assert query.startswith('mutation ') or query.startswith('query ')
        start = query.index(' ') + 1
        try:
            end = query.index('(')
        except:
            end = query.index('{')

        query_name = query[start:end]
        return query_name

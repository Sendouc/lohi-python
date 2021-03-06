import aiohttp
import time
from typing import List

from .graphql import (
    searchForBuildsByWeapon,
    maplists,
    hasAccess,
    xPowers,
    addCompetitiveFeedEvent,
    usersForAvas,
    updateAvas,
)

# creating a new session with every request considered bad practice with aiohttp but might still be
# easiest for what we are doing (requests only rarely)
class ApiConnecter:
    def __init__(self):
        self.graphql_server_url = "https://www.sendou.ink/graphql"
        self.rotation_data = None
        self.rotation_data_fetch_time = None
        self.salmon_run_data = None
        self.salmon_run_data_fetch_time = None

    async def request_data(self, url: str) -> dict:
        headers = {
            "User-Agent": "Lohi // Sendou#0043 on Discord // @Sendouc on Twitter"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status == 200:
                    r.raise_for_status()
                    return await r.json()

    async def sendou_ink_query(self, query: str, variables: dict = {}) -> dict:
        "Execute given query on sendou.ink/graphql"
        # https://gist.github.com/gbaman/b3137e18c739e0cf98539bf4ec4366ad
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graphql_server_url, json={"query": query, "variables": variables},
            ) as r:
                if r.status == 200:
                    r_dict = await r.json()
                    return r_dict["data"]
                else:
                    raise Exception(
                        f"Query failed to run by returning code of {r.status}. {query}"
                    )

    async def get_rotation_data(self) -> dict:
        "Return rotation data from splatoon2.ink as dictionary"
        current_time = time.time()
        # Only calling the API if we haven't done so before during this session or it was
        # more than 2 hours ago.
        if (
            self.rotation_data_fetch_time is None
            or self.rotation_data_fetch_time < current_time - 7200
        ):
            self.rotation_data = await self.request_data(
                "https://splatoon2.ink/data/schedules.json"
            )
            self.rotation_data_fetch_time = current_time
        return self.rotation_data

    async def get_salmon_run_data(self) -> dict:
        "Return Salmon Run data from splatoon2.ink as dictionary"
        current_time = time.time()
        # Only calling the API if we haven't done so before during this session or it was
        # more than 2 hours ago.
        if (
            self.salmon_run_data_fetch_time is None
            or self.salmon_run_data_fetch_time < current_time - 7200
        ):
            self.salmon_run_data = await self.request_data(
                "https://splatoon2.ink/data/coop-schedules.json"
            )
            self.salmon_run_data_fetch_time = current_time
        return self.salmon_run_data

    # GRAPHQL QUERIES

    async def get_builds(self, **kwargs) -> dict:
        response_dict = await self.sendou_ink_query(searchForBuildsByWeapon, kwargs)
        if response_dict is None:
            return None

        return response_dict["searchForBuilds"][:11]

    async def get_maplists(self) -> dict:
        response_dict = await self.sendou_ink_query(maplists)
        return response_dict["maplists"]

    async def has_access(self, **kwargs) -> str:
        response_dict = await self.sendou_ink_query(hasAccess, kwargs)
        return response_dict["hasAccess"]

    async def x_powers(self, **kwargs) -> List[int]:
        response_dict = await self.sendou_ink_query(xPowers, kwargs)
        return response_dict["xPowers"]

    async def add_competitive_feed_event(self, **kwargs) -> bool:
        response_dict = await self.sendou_ink_query(addCompetitiveFeedEvent, kwargs)
        if response_dict is None:
            return False
        return response_dict["addCompetitiveFeedEvent"]

    async def get_users_for_ava_update(self):
        response_dict = await self.sendou_ink_query(usersForAvas)
        return response_dict["users"]

    async def update_avas(self, **kwargs) -> bool:
        response_dict = await self.sendou_ink_query(updateAvas, kwargs)
        if response_dict is None:
            return False
        return response_dict["updateAvatars"]

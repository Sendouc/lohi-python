import aiohttp
import time

class ApiConnecter:
    def __init__(self):
        self.graphql_server_url = "https://www.sendou.ink/graphql"
        self.rotation_data = None
        self.rotation_data_fetch_time = None
    
    async def request_data(self, url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    r.raise_for_status()
                    return await r.json()

    async def get_rotation_data(self) -> dict:
        "Return rotation data from splatoon2.ink as dictionary"
        current_time = time.time()
        # Only calling the API if we haven't done so before during this session or it was
        # more than 1 hour ago.
        if self.rotation_data_fetch_time is None or self.rotation_data_fetch_time < current_time - 3600:
            self.rotation_data = await self.request_data("https://splatoon2.ink/data/schedules.json")
            self.rotation_data_fetch_time = current_time
        return self.rotation_data
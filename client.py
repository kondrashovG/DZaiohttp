import aiohttp
import asyncio


async def main():

    async with aiohttp.ClientSession() as session:
        response = await session.post(
            'http://0.0.0.0:8080/users/',
            json={"name": "user_6", "password": "1234"},
        )
        json_data = await response.json()
        print(json_data)

asyncio.run(main())
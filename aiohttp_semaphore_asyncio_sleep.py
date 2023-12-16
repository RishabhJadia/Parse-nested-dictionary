import asyncio
import aiohttp

class QR:
    def __init__(self):
        self.sem = asyncio.Semaphore(5)  # Adjust the semaphore limit as needed

    async def fetch(self, session, url):
        response = {"200": [], "not_200": []}
        async with self.sem:
            try:
                async with session.get(url, headers={"Authorization": "Bearer ..."}) as resp:
                    if resp.status == 200:
                        response['200'].append(True)
                    else:
                        response['not_200'].append(False)
                        print("fail")
            except aiohttp.ClientError as err:
                print(err)
            await asyncio.sleep(1)  # Introduce a 1-second delay between requests
        return response
    
    async def query(self, urls):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, url) for url in urls]
            return await asyncio.gather(*tasks)

async def main():
    obj = QR()
    urls = ["https://jsonplaceholder.com"] * 20000
    return await obj.query(urls)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(main())

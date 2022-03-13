import base64
# import requests
# from pprint import pprint
# from datetime import datetime
import aiohttp
import asyncio

HOST = 'http://127.0.0.1:8000'
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwdWJsaWNfaWQiOiJkYmVmOWM5NS1iZDM2LTRlY2ItOWQ2Zi1hOGI2NWFmMTI0ODQiLCJleHAiOjE2NDcyMDg3NTN9.NOTC5XFVS5M1c1wfPskA_TkGFiABgwaj6BF8T9U9WLU'

class ApiClient:

    def __init__(self, host=HOST):
        self.host = host
        self.session = aiohttp.ClientSession()

    async def _call(self, http_method, api_method, response_type=None, *args, **kwargs):
        response_method = getattr(self.session, http_method)
        response = await response_method(f'{self.host}/{api_method}', *args, **kwargs)
        if response_type == 'json':
            response = await response.json()
        return response

    async def get_root(self):
        response = await self._call('get', '')
        print(response.status)

    async def close(self):
        await self.session.close()

    async def check_health(self):
        return await self._call('get', 'health', response_type='json')

    async def create_user(self, user_login, password, email, first_name='', last_name=''):
        return await self._call('post', 'user', response_type='json',
                                json={
                                    'user_login': user_login,
                                    'password': password,
                                    'email': email,
                                    'first_name': first_name,
                                    'last_name': last_name,
                                }
                                )

    async def login(self, user_login, password):
        secret_code = base64.b64encode(f"{user_login}:{password}".encode()).decode()
        return  await self._call('post', 'login', response_type='json',
            headers={
                'Authorization': f'basic {secret_code}'
            }
        )

    async def delete_user(self):
        return await self._call('delete', 'user', response_type='json',
                                headers = {'x-access-tokens': f'{token}'})

    async def change_user(self, **kwargs):
        return await self._call('put', 'user', response_type='json',
                                headers={'x-access-tokens': f'{token}'},
                                json={**kwargs})

    async def create_adv(self, **kwargs):
        return await self._call('post', 'adv', response_type='json',
                                headers={'x-access-tokens': f'{token}'},
                                json={**kwargs})

    async def get_adv(self, id):
        return await self._call('get', f'adv/{id}', response_type='json',
                                headers={'x-access-tokens': f'{token}'})

    async def change_adv(self, id, **kwargs):
        return await self._call('put', f'adv/{id}', response_type='json',
                                headers={'x-access-tokens': f'{token}'},
                                json={**kwargs})

    async def delete_adv(self, id):
        return await self._call('delete', f'adv/{id}', response_type='json',
                                headers={'x-access-tokens': f'{token}'})

    async def show_all_advs(self):
        return await self._call('get', 'advs', response_type='json',
                                headers={'x-access-tokens': f'{token}'})


async def main():
    client = ApiClient()
    # await client.get_root()
    # print(await client.check_health())
    # print(await client.create_user('user', 'Userpass', 'a@a.ru'))
    # print(await client.login('user', 'Userpass'))
    # print(await client.change_user(email='d@a.ru', first_name='Petya'))
    # print(await client.create_adv(title='Продаю монитор'))
    # print(await client.get_adv(1))
    # print(await client.show_all_advs())
    # print(await client.change_adv(1, description='Б/у'))
    # print(await client.delete_adv(3))
    # print(await client.delete_user())
    await client.close()


if __name__ == '__main__':
    asyncio.run(main())

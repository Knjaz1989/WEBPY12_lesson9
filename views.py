from functools import wraps
from app import app, UserModel, AdvertisementModel
# Функция для хэширования и проверки, поставляемые вместе с Flask
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import jwt
import uuid
from aiohttp import web
from pydantic import BaseModel, ValidationError, validator
from asyncpg.exceptions import UniqueViolationError
import re
from werkzeug.http import parse_authorization_header

SECRET_KEY = '46fa7af6ab35c09ecaff3e3d48ee35fc'

# Создаем декоратор для альтернативных роутов
routes = web.RouteTableDef()



def token_required(f):
    @wraps(f)
    async def decorator( *args, **kwargs):
        token = None
        try:
            req = args[0].request
        except:
            req = args[0]

        if 'x-access-tokens' in req.headers:
            token = req.headers['x-access-tokens']

        if not token:
            return web.json_response({'message': 'a valid token is missing'})
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            req.current_user = await UserModel.query.where(UserModel.public_id == data['public_id']).gino.first()
        except:
            return web.json_response({'message': 'token is invalid'})

        return await f(*args, **kwargs)
    return decorator


class UserBaseValidationModel(BaseModel):

    email = ''
    password = ''
    first_name = ''
    last_name = ''

    class Config:
        extra = 'forbid'

    @validator('email')
    def email_checking(cls, email):
        pattern = '^([a-z0-9_\.-]+)@([a-z0-9_\.-]+)\.([a-z\.]{2,6})$'
        if not re.fullmatch(pattern, email):
            raise ValueError('email is wrong')
        return email

    @validator('password')
    def password_checking(cls, password):
        pattern = '(?=.*[a-z])(?=.*[A-Z])[0-9!@#$%^&*a-zA-Z]{6,}'
        if not re.fullmatch(pattern, password):
            raise ValueError('password is wrong')
        return password


class UserCreateValidationModel(UserBaseValidationModel):

    email: str
    password: str
    user_login: str


class AdvBaseValidationModel(BaseModel):
    title: str
    description = ''

    class Config:
        extra = 'forbid'


class AdvChangeValidationModel(AdvBaseValidationModel):
    title = ''


class UserView(web.View):

    async def post(self):
        json_data = await self.request.json()

        try:
            UserCreateValidationModel(**json_data)
        except ValidationError as e:
            return web.json_response(e.json())

        json_data_validation = UserCreateValidationModel(**json_data).dict()
        json_data_validation['public_id'] = str(uuid.uuid4())
        json_data_validation['password'] = generate_password_hash(json_data_validation['password'])
        new_user = UserModel(**json_data_validation)

        try:
            await new_user.create()
        except UniqueViolationError as e:
            return web.json_response({
                'DETAIL': e.as_dict()['detail']
            })

        return web.json_response({
            'status': 'created',
            'id': new_user.id,
            'user_login': new_user.user_login,
            'email': new_user.email,
            'first_name': new_user.first_name,
            'last_name': new_user.last_name,
        })

    @token_required
    async def delete(self):
        user = self.request.current_user
        await user.delete()
        return web.json_response(
            {
                'message': 'user was deleted'
            }
        )

    @token_required
    async def put(self):
        user = self.request.current_user
        json_data = await self.request.json()

        try:
            UserBaseValidationModel(**json_data)
        except ValidationError as e:
            return web.json_response(e.json())

        if 'password' in json_data:
            new_password = generate_password_hash(json_data['password'])
            json_data['password'] = new_password

        await UserModel.update.values(json_data).where(UserModel.id==user.id).gino.status()
        return web.json_response(
            {
                'message': 'user was changed'
            }
        )


class AdvertisementView(web.View):

    @token_required
    async def get(self):
        id = int(self.request.match_info['id'])
        adv = await AdvertisementModel.get(int(id))
        if adv is None:
            response = web.json_response({
                'message': 'There is not such advertisement in database'
            }, status=404)
            return response
        data = adv.to_dict()
        data['publish_date'] = data['publish_date'].strftime('%d.%m.%Y %H:%M:%S')
        return web.json_response(data, status=200)

    @token_required
    async def post(self):

        json_data = await self.request.json()

        try:
            AdvBaseValidationModel(**json_data)
        except ValidationError as e:
            return web.json_response(e.json())

        user = user = self.request.current_user

        json_data_validation = AdvBaseValidationModel(**json_data).dict()
        json_data_validation['owner_id'] = user.id
        new_adv = AdvertisementModel(**json_data_validation)
        await new_adv.create()
        return web.json_response(
            {
                'status': 'created',
                'id': new_adv.id,
                'advertisement': new_adv.title,
                'description': new_adv.description,
            }
        )

    @token_required
    async def delete(self):
        current_user_id = self.request.current_user.id
        adv_id = int(self.request.match_info['id'])
        adv = await AdvertisementModel.get(int(adv_id))
        if adv is None or adv.owner_id != current_user_id :
            response = web.json_response({
                'message': "You don't have such advertisement"
            }, status=404)
            return response

        await adv.delete()
        return web.json_response(
            {
                'message': 'advertisement was deleted'
            }
        )

    @token_required
    async def put(self):
        current_user_id = self.request.current_user.id
        adv_id = int(self.request.match_info['id'])
        adv = await AdvertisementModel.get(int(adv_id))
        if adv is None or adv.owner_id != current_user_id:
            response = web.json_response({
                'message': "You don't have such advertisement"
            }, status=404)
            return response

        json_data = await self.request.json()

        try:
            AdvChangeValidationModel(**json_data)
        except ValidationError as e:
            return web.json_response(e.json())

        await AdvertisementModel.update.values(json_data).where(AdvertisementModel.id == id).gino.status()
        return web.json_response(
            {
                'message': 'advertisement was changed'
            }
        )



async def login_user(request):
    req = request.headers.get('Authorization')
    auth = parse_authorization_header(req)
    if not auth or not auth.username or not auth.password:
        return web.json_response({
            'status_code': 401,
            'error': 'could not verify'
        })

    user = await UserModel.query.where(UserModel.user_login == auth.username).gino.first()
    if not user is None and check_password_hash(user.password, auth.password):
        token = jwt.encode(
            {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=45)},
            SECRET_KEY, "HS256")

        return web.json_response({'token': token})

    return web.json_response({
        'status_code': 401,
        'error': 'could not verify'
    })


# Альтернативный роут
@routes.get('/advs')
@token_required
async def get_list(request):
    advs = await AdvertisementModel.query.gino.all()
    return web.json_response({'Advertisements': list({'id': x.id,
                                    'title': x.title,
                                    'description': x.description,
                                    'publish_date': x.publish_date.strftime('%d.%m.%Y %H:%M:%S'),
                                    'owner_id': x.owner_id} for x in advs)})


async def check_health(request):
    return web.json_response({
        'status': 'OK'
    })


app.add_routes([
    web.get('/health', check_health),

    web.post('/login', login_user),

    web.post('/user', UserView),
    web.delete('/user', UserView),
    web.put('/user', UserView),

    web.get('/adv/{id:\d+}', AdvertisementView),
    web.post('/adv', AdvertisementView),
    web.delete('/adv/{id:\d+}', AdvertisementView),
    web.put('/adv/{id:\d+}', AdvertisementView),

    # web.get('/advs', get_list)
])
# Добавляем альтернативный роут
app.add_routes(routes)


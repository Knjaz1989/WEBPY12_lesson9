# from flask_migrate import Migrate
from sqlalchemy.sql import func
from aiohttp import web
from gino import Gino


app = web.Application()
db_uri = 'postgresql+asyncpg://aiohttp:1234@localhost:5432/aiohttp'
# app.config.from_mapping(SQLALCHEMY_DATABASE_URI=db_uri)
db = Gino()
# migrate = Migrate(app, db)
#
#
class UserModel(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String, nullable=False)
    user_login = db.Column(db.String(length=40), nullable=False, unique=True, default='')
    first_name = db.Column(db.String(length=30))
    last_name = db.Column(db.String(length=50))
    password = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)

    _idx1 = db.Index('app__users__user_login', 'user_login', unique=True)

    def __str__(self):
        return f'{self.id}: {self.user_login} - {self.first_name} {self.last_name}'


class AdvertisementModel(db.Model):

    __tablename__ = 'advertisements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(length=50), nullable=False)
    description = db.Column(db.String(length=250))
    publish_date = db.Column(db.DateTime(), default=func.now())
    owner_id = db.Column(db.Integer, db.ForeignKey(UserModel.id), nullable=False)

    def __str__(self):
        return f'{self.id}: {self.title}'

    def __repr__(self):
        return f'{self.id}: {self.title}'

async def init_orm(app):
    await db.set_bind(db_uri)
    await db.gino.create_all()
    yield
    await db.pop_bind().close()

app.cleanup_ctx.append(init_orm)






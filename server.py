import json
from aiohttp import web
from bcrypt import hashpw, gensalt, checkpw
from sqlalchemy.exc import IntegrityError

from models import engine, Base, User, Session


def hash_password(password: str):
    password = password.encode()
    password = hashpw(password, salt=gensalt())
    password = password.decode()
    return password


def check_password(password: str, hashed_password: str):
    return checkpw(password.encode(), hashed_password=hashed_password.encode())


app = web.Application()


async def orm_context(app):
    print("START")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    print('SHUT DOWN')


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request['session'] = session
        response = await handler(request)
        return response


app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)


async def get_user(user_id: int, session: Session) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise web.HTTPNotFound(
            text=json.dumps({'error': 'user not found'}),
            content_type='application/json'
        )
    return user


class UsersView(web.View):

    @property
    def session(self) -> Session:
        return self.request['session']

    @property
    def user_id(self) -> int:
        return int(self.request.match_info['user_id'])

    async def get(self):

        user = await get_user(self.user_id, self.session)
        return web.json_response({
            'id': user.id,
            'name': user.name,
            'creation_time': int(user.creation_time.timestamp())
        })

    async def post(self):
        json_data = await self.request.json()
        json_data['password'] = hash_password(json_data['password'])
        user = User(**json_data)
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError as er:
            raise web.HTTPConflict(
                text=json.dumps({"error": "user already exists"}),
                content_type='application/json'
            )
        return web.json_response({'id': user.id})

    async def patch(self):
        json_data = await self.request.json()
        if 'password' in json_data:
            json_data['password'] = hash_password(json_data['password'])
        user = await get_user(self.user_id, self.session)
        for field, value in json_data.items():
            setattr(user, field, value)
        self.session.add(user)
        await self.session.commit()
        return web.json_response({'id': user.id})

    async def delete(self):
        user = await get_user(self.user_id, self.session)
        await self.session.delete(user)
        await self.session.commit()
        return web.json_response({'id': user.id})


app = web.Application()

app.add_routes(
    [
        web.get("/users/{user_id:\d+}", UsersView),
        web.patch("/users/{user_id:\d+}", UsersView),
        web.delete("/users/{user_id:\d+}", UsersView),
        web.post("/users/", UsersView),
    ]
)

if __name__ == '__main__':
    web.run_app(app)

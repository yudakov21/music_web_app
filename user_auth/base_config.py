from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users.authentication import JWTStrategy
from fastapi_users import FastAPIUsers
from user_auth.manager import get_user_manager
from config import SECRET
from models.models import User

cookie_transport = CookieTransport(cookie_name='cookies', cookie_max_age=7200)

def get_jtw_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=7200)

auth_backend = AuthenticationBackend(
    name='jwt',
    transport=cookie_transport,
    get_strategy=get_jtw_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend]
)

current_user = fastapi_users.current_user()
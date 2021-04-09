from sqlalchemy.orm import Session
from passlib.context import CryptContext
from api.db.models import users as models
# from api.db.models.settings import TokenBlacklist
from api.db.schemas import users as schemas
from api.settings import Settings
from fastapi.exceptions import HTTPException
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = Settings()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_name(db: Session, username: str):
    return (
        db.query(models.User)
        .filter(models.User.username == username.casefold())
        .first()
    )


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    _hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user: schemas.UserCreate, current_user):
    _hashed_password = get_password_hash(user.password)
    _user = get_user_by_name(db=db, username=current_user)
    if _user and _user.is_active:
        if _user.username.casefold() != user.username.casefold():
            print("Old Username: {name}".format(name=_user.username))
            print("New Username: {name}".format(name=user.username))
        _user.username = user.username.casefold()
        if user.password != "":
            _user.hashed_password = _hashed_password
        try:
            db.add(_user)
            db.commit()
            db.refresh(_user)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=exc)
        return _user


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# def blacklist_api_key(Authorize, db: Session):
#     jti = Authorize.get_raw_jwt()['jti']
#     access = TokenBlacklist(jti, False, 'true')

#     db.add(access)

#     db.commit()
#     return


# def blacklist_login_token(Authorize, db: Session):
#     jti = Authorize.get_raw_jwt()['jti']
#     access = TokenBlacklist(jti=jti, expires=settings.ACCESS_TOKEN_EXPIRES, revoked='true')
#     refresh = TokenBlacklist(jti=jti, expires=settings.REFRESH_TOKEN_EXPIRES, revoked='true')

#     db.add(access)
#     db.add(refresh)

#     db.commit()
#     return


def get_keys(user, db: Session):
    keys = db.query(models.APIKEY).filter(models.APIKEY.user == user.id).all()
    return keys


def create_key(user, Authorize, db: Session):
    api_key = Authorize.create_access_token(subject=secrets.token_urlsafe(10), expires_time=False)
    _hashed_key = get_password_hash(api_key)
    db_key = models.APIKEY(user=user.id, is_active=True, hashed_key=_hashed_key)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    db_key.token = api_key
    return db_key

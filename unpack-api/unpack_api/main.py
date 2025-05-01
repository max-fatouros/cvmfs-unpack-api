import os
from typing import Annotated

import requests
from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError
from authlib.jose.errors import DecodeError
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException


load_dotenv()
PIPELINE_TOKEN = os.getenv('PIPELINE_TOKEN')
TARGET_REPOSITORY_ID = os.getenv('TARGET_REPOSITORY_ID')
GITLAB_SERVER = os.getenv('GITLAB_SERVER')
SECRET_TOKEN = os.getenv('SECRET_TOKEN')

app = FastAPI()

GITLAB_SERVER_URL = f'{GITLAB_SERVER}/oauth/discovery/keys'

request_jwk = requests.get(GITLAB_SERVER_URL)
request_jwk.raise_for_status()

jwk = request_jwk.json()
jwks_keys = jwk['keys']


def request_sync(image):
    request = requests.post(
        url=(
            f'{GITLAB_SERVER}/api/v4/projects/'
            f'{TARGET_REPOSITORY_ID}/trigger/pipeline'
        ),
        data={
            'token': PIPELINE_TOKEN,
            'ref': 'main',
            'variables[IMAGE]': image,
        },
    )

    if request.status_code != 200:
        raise HTTPException(
            status_code=request.status_code,
            detail=f'Token server error: {request.text}',
        )


def check_authorization(
    authorization: Annotated[str | None, Header()],
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail='No Authorization header provided',
        )


@app.get('/')
def root():
    return {'message': 'PSI Image Unpacker'}


@app.post('/api/sync/jwt')
def sync_jwt(
        authorization: Annotated[str | None, Header()] = None,
        image: str | None = None,
):

    check_authorization(authorization)
    try:
        claims = jwt.decode(
            authorization,
            jwks_keys,
        )
    except DecodeError:
        raise HTTPException(
            status_code=403,
            detail='Invalid token: DecodeError',
        )
    except BadSignatureError:
        raise HTTPException(
            status_code=403,
            detail='Invalid token: BadSignatureError',
        )
    if claims['iss'] != GITLAB_SERVER:
        raise HTTPException(
            status_code=403,
            detail=f"Invalid issuer {claims['iss']}",
        )

    request_sync(image)


@app.post('/api/sync/secret')
def sync_secret(
        authorization: Annotated[str | None, Header()] = None,
        image: str | None = None,
):

    check_authorization(authorization)

    if authorization != SECRET_TOKEN:
        raise HTTPException(
            status_code=401,
            detail='Invalid authorization token',
        )

    request_sync(image)

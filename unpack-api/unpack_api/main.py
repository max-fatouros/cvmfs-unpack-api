import json
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

SECRET_TOKEN = os.getenv('SECRET_TOKEN')

# >>> GitHub
GITHUB_REPO = os.getenv('GITHUB_REPO')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_WORKFLOW = os.getenv('GITHUB_WORKFLOW')
# <<<

# >>> GitLab
GITLAB_SERVER = os.getenv('GITLAB_SERVER')
GITLAB_TARGET_REPOSITORY_ID = os.getenv('GITLAB_TARGET_REPOSITORY_ID')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
# <<<


def get_expose_api_map():
    expose_api = {
        'gitlab': False,
        'github': False,
        'secret': False,
    }

    if None not in (
        GITLAB_SERVER,
        GITLAB_TARGET_REPOSITORY_ID,
        GITLAB_TOKEN,
    ):
        expose_api['gitlab'] = True

    if None not in (
        GITHUB_REPO,
        GITHUB_TOKEN,
        GITHUB_WORKFLOW,
    ):
        expose_api['github'] = True

    if SECRET_TOKEN is not None:
        expose_api['secret'] = True

    return expose_api


def get_jwt_keys(jwt_server_url):
    request_jwk = requests.get(jwt_server_url)
    request_jwk.raise_for_status()

    jwk = request_jwk.json()
    jwks_keys = jwk['keys']
    return jwks_keys


def request_gitlab_sync(image):
    request = requests.post(
        url=(
            f'{GITLAB_SERVER}/api/v4/projects/'
            f'{GITLAB_TARGET_REPOSITORY_ID}/trigger/pipeline'
        ),
        data={
            'token': GITLAB_TOKEN,
            'ref': 'main',
            'variables[IMAGE]': image,
        },
    )

    if request.status_code != 200:
        raise HTTPException(
            status_code=request.status_code,
            detail=f'Token server error: {request.text}',
        )


def request_github_sync(image):
    """
    https://docs.github.com/en/rest/actions/workflows?apiVersion=2022-11-28#create-a-workflow-dispatch-event
    """
    request = requests.post(
        url=(
            f'https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/dispatches'  # noqa
        ),
        data=json.dumps({
            'ref': 'action-testing',
            # 'inputs': {
            #     'image': image,
            # },
        }),
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'X-GitHub-Api-Version': '2022-11-28',
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


app = FastAPI()

expose_api = get_expose_api_map()

gitlab_jwks_keys = None
if expose_api['gitlab']:
    gitlab_jwks_keys = get_jwt_keys(
        f'{GITLAB_SERVER}/oauth/discovery/keys',
    )


github_jwks_keys = None
if expose_api['github']:
    github_jwks_keys = get_jwt_keys(
        'https://token.actions.githubusercontent.com/.well-known/jwks',
    )


@app.get('/')
def root():
    return {'message': 'PSI Image Unpacker'}


if expose_api['gitlab']:
    @app.post('/api/gitlab/sync/jwt')
    def gitlab_sync_jwt(
        authorization: Annotated[str | None, Header()] = None,
        image: str | None = None,
    ):

        check_authorization(authorization)
        try:
            claims = jwt.decode(
                authorization,
                gitlab_jwks_keys,
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

        request_gitlab_sync(image)


if expose_api['github']:
    @app.post('/api/github/sync/jwt')
    def github_sync_jwt(
        authorization: Annotated[str | None, Header()] = None,
        image: str | None = None,
    ):

        check_authorization(authorization)
        try:
            claims = jwt.decode(
                authorization,
                github_jwks_keys,
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
        if claims['iss'] != 'https://token.actions.githubusercontent.com':
            raise HTTPException(
                status_code=403,
                detail=f"Invalid issuer {claims['iss']}",
            )

        request_gitlab_sync(image)


if expose_api['secret'] and expose_api['gitlab']:
    @app.post('/api/gitlab/sync/secret')
    def gitlab_sync_secret(
            authorization: Annotated[str | None, Header()] = None,
            image: str | None = None,
    ):

        check_authorization(authorization)

        if authorization != SECRET_TOKEN:
            raise HTTPException(
                status_code=401,
                detail='Invalid authorization token',
            )

        request_gitlab_sync(image)


if expose_api['secret'] and expose_api['github']:
    @app.post('/api/github/sync/secret')
    def github_sync_secret(
            authorization: Annotated[str | None, Header()] = None,
            image: str | None = None,
    ):

        check_authorization(authorization)

        if authorization != SECRET_TOKEN:
            raise HTTPException(
                status_code=401,
                detail='Invalid authorization token',
            )

        request_github_sync(image)

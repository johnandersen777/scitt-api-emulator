# Copyright (c) SCITT Authors.
# Licensed under the MIT License.
import jwt
import json
import jwcrypto.jwk
from flask import jsonify
from werkzeug.wrappers import Request
from scitt_emulator.client import HttpClient


class OIDCAuthMiddleware:
    def __init__(self, app, config_path):
        self.app = app
        self.config = {}
        if config_path and config_path.exists():
            self.config = json.loads(config_path.read_text())

        # Initialize JSON Web Key client for given issuer
        self.client = HttpClient()
        self.oidc_config = self.client.get(
            f"{self.config['issuer']}/.well-known/openid-configuration"
        ).json()
        self.jwks_client = jwt.PyJWKClient(self.oidc_config["jwks_uri"])

    def __call__(self, environ, start_response):
        request = Request(environ)
        self.validate_token(request.headers["Authorization"].replace("Bearer ", ""))
        return self.app(environ, start_response)

    def validate_token(self, token):
        return jwt.decode(
            token,
            key=self.jwks_client.get_signing_key_from_jwt(token).key,
            algorithms=self.oidc_config["id_token_signing_alg_values_supported"],
            audience=self.config.get("audience", None),
            issuer=self.config["issuer"],
            options={"strict_aud": self.config.get("strict_aud", True),},
            leeway=self.config.get("leeway", 0),
        )

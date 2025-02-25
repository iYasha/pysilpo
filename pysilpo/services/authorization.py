import base64
import hashlib
import random
import re
import secrets
import sys
import time
from datetime import datetime

if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    from datetime import timezone

    UTC = timezone.utc

from functools import cached_property
from typing import Literal, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from pydantic import BaseModel, model_validator

from pysilpo.utils.cache import SQLiteCache
from pysilpo.utils.exceptions import (
    NoOpenIDAuthCodeException,
    SilpoAuthorizationException,
    SilpoException,
    SilpoOTPInvalidException,
)
from pysilpo.utils.utils import get_jwt_expires_in, get_logger


class Token(BaseModel):
    id_token: str
    access_token: str
    expires_in: datetime
    token_type: str
    scope: str

    @model_validator(mode="before")
    @classmethod
    def set_expire_time(cls, values):
        values["expires_in"] = get_jwt_expires_in(values["access_token"])
        return values


class User:
    """
    All public methods should return self to allow chaining.
    """

    logger = get_logger("pysilpo.authorization.User")
    _base_auth_domain = "https://auth.silpo.ua"
    _openid_configuration = urljoin(_base_auth_domain, "/.well-known/openid-configuration")
    _phone_number_pattern = r"^\+380\d{9}$"

    def __init__(
        self,
        phone_number: str,
        openid_client_id: Optional[str] = "profile--profile--cabinet",
        openid_scope: Optional[str] = "openid public-my profile--security--identity-service:internal-api--call "
        "core--core--media-service:media--upload payments--payments--wallet-service:cards--read-my "
        "core--core--media-service:media--upload",
        openid_redirect_uri: Optional[str] = "https://id.silpo.ua/signin-oidc",
    ):
        if not re.match(self._phone_number_pattern, phone_number):
            raise SilpoException("Invalid phone number, must be in format +380XXYYYYYYY")
        self.phone_number = phone_number
        self.session = requests.Session()
        self.client_id = openid_client_id
        self.scope = openid_scope
        self.redirect_uri = openid_redirect_uri
        self.code_verifier = secrets.token_urlsafe(64)

        self.token: Optional[Token] = self.cached_token

    @cached_property
    def openid_configuration(self) -> dict:
        resp = self.session.get(self._openid_configuration)
        resp.raise_for_status()
        return resp.json()

    @property
    def cached_token(self) -> Optional[Token]:
        return SQLiteCache().get(f"token_{self.phone_number}")

    def request_otp(self, delivery_method: Literal["sms", "viber-sms"] = "sms", force: bool = False) -> "User":
        if self.token and not force:
            self.logger.debug("[request_otp] Already logged in with token scope. Skipping OTP request")
            return self

        auth_cookies = SQLiteCache().get(f"cookie_{self.phone_number}")
        if auth_cookies and not force:
            self.logger.debug("[request_otp] Have cookies for authorization. Skipping OTP request")
            return self

        full_url = urljoin(self._base_auth_domain, "/api/v2/Login/ByPhone")
        json = {
            "phone": self.phone_number,
            "recaptcha": None,
            "delivery_method": delivery_method,
            "phoneChannelType": 0,
        }
        self.logger.debug("[_request_otp] Requesting OTP with %s to %s", json, full_url)
        resp = self.session.post(full_url, json=json)
        json_data = resp.json()
        self.logger.debug("[_request_otp] Received response: %s", json_data)
        if not resp.ok:
            if json_data["secondsTillNextOTP"]:
                self.logger.warning(
                    "[_request_otp] Got error from Silpo, need to wait till next OTP: " "%s seconds. Waiting...",
                    json_data["secondsTillNextOTP"],
                )
                time.sleep(json_data["secondsTillNextOTP"] + random.randint(1, 4))  # noqa: S311
                return self.request_otp(delivery_method)
            raise SilpoAuthorizationException(f"Error while requesting OTP: {json_data}")
        return self

    def _verify_otp(self, otp_code: str) -> "User":
        """
        This method send OTP code to Silpo API to verify it.
        If OTP code is valid, Silpo API will set cookies required for the next requests,
        otherwise it will raise an exception.

        :param otp_code: 6-digit OTP code
        :return: None
        """
        if not re.match(r"^\d{6}$", otp_code):
            raise SilpoOTPInvalidException("OTP code must contain 6 digits")
        full_url = urljoin(self._base_auth_domain, "/api/v2/Login/LoginWithOTP")
        json = {
            "phone": self.phone_number,
            "otp": otp_code,
            "phoneChannelType": 0,
        }
        self.logger.debug("[_verify_otp] Verifying OTP with %s to %s", json, full_url)
        resp = self.session.post(full_url, json=json)
        json_data = resp.json()
        self.logger.debug("[_verify_otp] Received response: %s. With cookies: %s", json_data, resp.cookies)
        if not resp.ok or json_data["error"]:
            raise SilpoOTPInvalidException("Error while verifying OTP: %s", json_data)
        SQLiteCache().set(f"cookie_{self.phone_number}", dict(resp.cookies))
        return self

    @staticmethod
    def _enter_cli_otp() -> str:
        while True:
            otp_code = input("Enter the OTP code sent by Silpo: ")
            if not re.match(r"^\d{6}$", otp_code):
                raise SilpoOTPInvalidException("OTP code must contain 6 digits")
            break
        return otp_code

    def _openid_authorize(self, auth_cookies: Optional[dict] = None) -> str:
        """
        This method authorizes user with OpenID Connect protocol.
        It sends a request to Silpo API to get authorization code.
        When request is finished, it parses the response.url query params to get authorization code.
        This code will be used to get access token.
        :return: OpenID authorization code
        """
        full_url = self.openid_configuration["authorization_endpoint"]
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(self.code_verifier.encode()).digest()).rstrip(b"=").decode("ascii")
        )
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": secrets.token_urlsafe(16),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "response_mode": "query",
        }
        self.logger.debug("[_openid_authorize] Authorizing with %s to %s", params, full_url)
        resp = self.session.get(full_url, params=params, cookies=auth_cookies)
        resp.raise_for_status()
        self.logger.debug(
            "[_openid_authorize] Received location: %s. With headers: %s and cookies: %s",
            resp.url,
            resp.headers,
            resp.cookies,
        )

        parsed_url = urlparse(resp.url)
        query_params = parse_qs(parsed_url.query)
        self.logger.debug("[_openid_authorize] Parsed query params: %s", query_params)
        auth_code = query_params.get("code", [None])[0]

        if auth_code is None:
            raise NoOpenIDAuthCodeException("No auth code in response for OpenID authorization")
        return auth_code

    def _get_token(self, auth_code: str) -> Token:
        full_url = self.openid_configuration["token_endpoint"]
        form_data = {
            "client_id": self.client_id,
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier,
            "grant_type": "authorization_code",
        }
        self.logger.debug("[_get_access_token] Getting access token with %s to %s", form_data, full_url)
        resp = self.session.post(full_url, data=form_data)
        json_data = resp.json()
        self.logger.debug("[_get_access_token] Received response: %s", json_data)
        if not resp.ok:
            raise SilpoAuthorizationException(f"Error while getting access token: {json_data}")
        return Token(**json_data)

    def is_expired(self) -> bool:
        if self.cached_token is None:
            return True
        return self.token.expires_in < datetime.now(tz=UTC)

    def _refresh_token(self) -> None:
        auth_cookies = SQLiteCache().get(f"cookie_{self.phone_number}")
        if not auth_cookies:
            raise SilpoAuthorizationException(
                "No cookies found for token refresh."
                "Please login first using User(phone_number=...).request_otp().login() method."
            )
        code = self._openid_authorize(auth_cookies)
        self.token = self._get_token(code)
        self.logger.debug(
            "[refresh_token] Token refreshed with scope: %s | %s UTC", self.token.scope, self.token.expires_in
        )

    @property
    def access_token(self) -> str:
        if self.token is None:
            raise SilpoAuthorizationException(
                "Access token is not set. "
                "Please login first using User(phone_number=...).request_otp().login() method."
            )
        if self.is_expired():
            self._refresh_token()
        return self.token.access_token

    def set_token(self, token: Token) -> "User":
        self.token = token
        self.logger.debug("[set_token] Set token scope: %s | %s UTC", self.token.scope, self.token.expires_in)
        SQLiteCache().set(f"token_{self.phone_number}", token, expires_in=token.expires_in)
        return self

    def login(self, otp_code: Optional[str] = None, force: bool = False, retry_no: int = 0) -> "User":
        if self.token and not force:
            self.logger.debug(
                "[login] Already logged in with token scope: %s | %s UTC", self.token.scope, self.token.expires_in
            )
            return self

        auth_cookies = SQLiteCache().get(f"cookie_{self.phone_number}")
        if not auth_cookies and not force:
            if otp_code is None:
                otp_code = self._enter_cli_otp()
            self._verify_otp(otp_code)

        try:
            auth_code = self._openid_authorize(auth_cookies)
        except NoOpenIDAuthCodeException as e:
            if retry_no >= 2:
                raise SilpoAuthorizationException(
                    "Failed to get OpenID authorization code after 3 retries. Please try again later."
                ) from e
            self.logger.warning("[login] %s. Trying to request OTP and login again", e)
            SQLiteCache().clear()
            return self.login(otp_code=otp_code, force=True, retry_no=retry_no + 1)
        self.token = self._get_token(auth_code)
        self.logger.debug("[login] Logged in with token scope: %s | %s UTC", self.token.scope, self.token.expires_in)
        SQLiteCache().set(f"token_{self.phone_number}", self.token, expires_in=self.token.expires_in)
        return self

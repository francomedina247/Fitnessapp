from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import BaseAuthentication
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class PlayerJWTAuthentication(JWTAuthentication):
    pass


class PlayerInternalAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return None


class PlayerJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = PlayerJWTAuthentication
    name = 'bearerAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }


class PlayerInternalAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = PlayerInternalAuthentication
    name = 'internalAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'description': 'Internal service authentication (no-op in current implementation)',
        }

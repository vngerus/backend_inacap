from rest_framework import status
from rest_framework.exceptions import APIException


class Conflicto(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflicto con el estado actual del recurso."
    default_code = "conflicto"

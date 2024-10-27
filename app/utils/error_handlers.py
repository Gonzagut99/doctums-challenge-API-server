from fastapi import HTTPException,status
from fastapi.responses import JSONResponse

from app.routers.http.ResponseModel import ResponseModel


def handle_404exception(e:HTTPException):
    return JSONResponse(
                content=ResponseModel(
                    message=e.detail,
                    detail=e.detail,
                    code=status.HTTP_404_NOT_FOUND,
                    error=True
                ).get_serialized_response(),
                status_code=status.HTTP_404_NOT_FOUND
            )
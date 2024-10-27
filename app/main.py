import json
import logging
from fastapi import  FastAPI, Request, status
from fastapi.concurrency import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, ResponseValidationError, ValidationException
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from app.LogicEntities.Context import Context
from app.LogicEntities.GameSessions import GameSessionLogicContext
from app.config.database import create_db_and_tables
from app.routers.http.ResponseModel import ResponseModel
from app.websockets.ws_manager import ConnectionManager
from pathlib import Path


DATA_DIR = Path().resolve().joinpath("app/data") or Path().resolve().resolve().joinpath("app/data")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting lifespan...")
    try:
        create_db_and_tables()
        print("DB and tables created successfully.")
    except Exception as e:
        print(f"Error during DB setup: {str(e)}")
    yield
    print("Shutting down app...")

app = FastAPI(lifespan=lifespan)

app.title = "Challenge Doctums API"
app.version = "0.0.1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Websockets manager
manager = ConnectionManager()


#Middleware de conexiones y sesiones: Para cuando implementemos los websockets
# @app.middleware("http")
# async def db_session_middleware(request: Request, call_next):
#     print("Middleware start")
#     session_id = has_session_id = request.cookies.get("fast_vote_session")
#     if not has_session_id:
#         print("No session ID found, creating one")
#         session_id = str(uuid())
#     request.cookies.setdefault("fast_vote_session", session_id)
#     response: Response = await call_next(request)
#     print("Middleware end")
#     if has_session_id is None:
#         response.set_cookie("fast_vote_session", session_id,path="/", httponly=True)
#     return response

#Initializing the memory session game
gameSessions = GameSessionLogicContext()

#Initialing the context for the game logic
context = Context(DATA_DIR)

#Customizing error handlers
# Manejador genérico para errores inesperados
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred. Please try again later."},
    )

#Customized validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseModel(
            message="Validation error",
            data=jsonable_encoder(exc.body),
            detail=jsonable_encoder(exc.errors()),
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error=True
        ).get_serialized_response(),
    )
    
@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseModel(
            message="Validation error",
            data=None,
            detail=json.loads(exc.json()),
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error=True
        ).get_serialized_response(),
    )


from app.routers.http.game_router import game_http_router
from app.routers.http.player_router import player_http_router
from app.routers.ws_router import ws_router
#app.include_ws_router()
app.include_router(ws_router)
app.include_router(game_http_router)
app.include_router(player_http_router)

@app.get('/', tags = ['home'])
def message ():
    return HTMLResponse('<h2>Hello world</h2>')


# create_db_and_tables()
print("Server started")
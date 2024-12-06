import json
import logging
from fastapi import  FastAPI, Request, status
from fastapi.concurrency import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, ResponseValidationError, ValidationException
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from app.LogicEntities.Context import Context
from app.LogicEntities.GameSessions import GameSessionLogicContext
from app.config.database import create_db_and_tables
from app.routers.http.ResponseModel import ResponseModel
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

app = FastAPI(lifespan=lifespan, swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})

app.title = "Challenge Doctums API"
app.version = "0.0.1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Montar directorio static
app.mount("/public", StaticFiles(directory="app/public"), name="public")


# @app.get('/', tags = ['home'])
# def message ():
#     return HTMLResponse('<h2>Bienvenido al Challenge Doctums</h2>')}
@app.get('/', response_class=HTMLResponse, tags=['home'])
def home():
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Challenge Doctums</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    margin-top: 50px;
                }
                h2 {
                    color: #333;
                }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    text-align: center;
                    text-decoration: none;
                    outline: none;
                    color: #fff;
                    background-color: #4CAF50;
                    border: none;
                    border-radius: 15px;
                    box-shadow: 0 9px #999;
                }
                .button:hover {background-color: #3e8e41}
                .button:active {
                    background-color: #3e8e41;
                    box-shadow: 0 5px #666;
                    transform: translateY(4px);
                }
                img {
                    border-radius: 36px;
                    max-width: 500px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    transition: transform 0.2s;
                }
                img:hover {
                    transform: scale(1.1);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Bienvenido al Challenge Doctums</h2>
                <img src="/public/GameInAction.png" alt="Game in action" style="margin-bottom: 20px;">
                <a href="/docs" class="button">Ver Documentación</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    

# create_db_and_tables()
print("Server started")
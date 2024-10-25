from fastapi import  FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.LogicEntities.Context import Context
from app.LogicEntities.GameSessions import GameSessionLogicContext
from app.config.database import create_db_and_tables
from app.websockets.ws_manager import ConnectionManager
from pathlib import Path


DATA_DIR = Path().resolve().joinpath("app/data") or Path().resolve().resolve().joinpath("app/data")

app = FastAPI()

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




from app.routers.http_router import http_router
from app.routers.ws_router import ws_router
#app.include_ws_router()
app.include_router(ws_router)
app.include_router(http_router)

@app.get('/', tags = ['home'])
def message ():
    return HTMLResponse('<h2>Hello world</h2>')


create_db_and_tables()
print("Server started")
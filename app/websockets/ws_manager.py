from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def add_connection(self, connection:WebSocket):
        await connection.accept()
        self.connections.append(connection)

    async def remove_connection(self, connection: WebSocket):
        if connection in self.connections:
            await connection.close()
            self.connections.remove(connection)

    async def broadcast(self, data):
        """Broadcast a message to all connections, an stringified JSON object is expected"""
        for connection in self.connections:
            await connection.send_text(data)

    async def broadcast_json(self, data: dict):
        for connection in self.connections:
            await connection.send_json(data)
    
    # async def sendMessage(self, message: str):
    #     for connection in self.connections:
    #         await connection.send_text(message)
            
    async def send_personal_message(self, message: str, connection:WebSocket):
        await connection.send_text(message)
        
    async def send_personal_json(self, message: dict, connection:WebSocket):
        """Send a JSON message to a specific connection, an stringified JSON object is expected"""
        await connection.send_json(message)
        
    async def send_message_by_port(self, message: dict, port:int):
        for connection in self.connections:
            if connection.client.port == port:
                await connection.send_json(message)
                return
        return False
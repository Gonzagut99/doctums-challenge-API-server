from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def add_connection(self, connection:WebSocket):
        await connection.accept()
        self.connections.append(connection)

    async def remove_connection(self, connection: WebSocket):
        print("Disconneting all connections")
        if connection in self.connections:
            await connection.close()
            self.connections.remove(connection)

    async def remove_connections(self,):
        for connection in self.connections:
            print("Disconneting all connections")
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
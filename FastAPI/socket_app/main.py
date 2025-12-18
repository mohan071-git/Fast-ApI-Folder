from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import socketio

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

# Create FastAPI app
app = FastAPI()

# IMPORTANT: this variable name MUST be socket_app
socket_app = socketio.ASGIApp(sio, app)

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Socket.IO Chat</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
</head>
<body>
    <h1>Socket.IO Chat</h1>

    <input id="message" autocomplete="off">
    <button onclick="sendMessage()">Send</button>

    <ul id="messages"></ul>

    <script>
        const socket = io("http://localhost:8000");

        socket.on("connect", () => {
            console.log("Connected:", socket.id);
        });

        socket.on("chat_message", (msg) => {
            const li = document.createElement("li");
            li.textContent = msg;
            document.getElementById("messages").appendChild(li);
        });

        function sendMessage() {
            const input = document.getElementById("message");
            socket.emit("chat_message", input.value);
            input.value = "";
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def index():
    return HTMLResponse(html)

@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)

@sio.event
async def disconnect(sid):
    print("Client disconnected:", sid)

@sio.event
async def chat_message(sid, message):
    await sio.emit("chat_message", f"{sid}: {message}")

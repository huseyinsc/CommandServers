from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import subprocess
import os
import sys
import threading
import atexit
import time

app = Flask(__name__, static_folder='static', template_folder='templates')
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variable to hold the subprocess
cpp_process = None
initial_output = []

def start_cpp_process():
    """Start the C++ process with proper configuration"""
    global cpp_process
    cwd = os.path.dirname(os.path.abspath(__file__))
    exe_path = os.path.join(cwd, "CustomCmd.exe")
    
    if not os.path.exists(exe_path):
        raise FileNotFoundError("CustomCmd.exe not found")
    
    cpp_process = subprocess.Popen(
        [exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        cwd=cwd
    )
    
    # Read initial output immediately after startup
    time.sleep(0.1)  # Allow process to start
    while True:
        if cpp_process.poll() is not None:
            break
        line = cpp_process.stdout.readline()
        if not line:
            break
        initial_output.append(line.strip())
        if "Choose:" in line:  # Stop at the first prompt
            break
    
    return cpp_process

def read_from_cpp_and_forward():
    """Read from C++ process stdout and forward to WebSocket clients"""
    global cpp_process
    while cpp_process and cpp_process.poll() is None:
        try:
            output = cpp_process.stdout.readline()
            if output:  # Only send non-empty output
                socketio.emit('cpp_output', {'data': output.strip()})
        except:
            break  # Exit thread if there's an error

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection"""
    global cpp_process, initial_output
    print('Client connected')
    
    # Send initial output to new client
    for line in initial_output:
        emit('cpp_output', {'data': line})
    
    # Start C++ process if not already running
    if cpp_process is None or cpp_process.poll() is not None:
        try:
            initial_output.clear()  # Reset for new process
            cpp_process = start_cpp_process()
            
            # Start thread to monitor C++ process output
            threading.Thread(target=read_from_cpp_and_forward, daemon=True).start()
            
            emit('status', {'data': 'Connected to C++ process'})
        except FileNotFoundError as e:
            error_msg = f"Executable not found: {str(e)}"
            emit('error', {'data': error_msg})
            print(error_msg, file=sys.stderr)
        except Exception as e:
            error_msg = f'Failed to start C++ process: {str(e)}'
            emit('error', {'data': error_msg})
            print(error_msg, file=sys.stderr)
    else:
        emit('status', {'data': 'Reconnected to existing C++ process'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')
    # Note: We don't kill the C++ process here as other clients might be connected

@socketio.on('cpp_input')
def handle_cpp_input(data):
    """Handle input from browser and forward to C++ process"""
    global cpp_process
    if cpp_process is None or cpp_process.poll() is not None:
        emit('error', {'data': 'C++ process is not running'})
        return
    
    try:
        message = data.get('data', '') + '\n'  # Ensure newline for the C++ program
        cpp_process.stdin.write(message)
        cpp_process.stdin.flush()
    except BrokenPipeError:
        error_msg = "C++ process terminated unexpectedly"
        emit('error', {'data': error_msg})
        print(error_msg, file=sys.stderr)
    except Exception as e:
        error_msg = f'Failed to send to C++ process: {str(e)}'
        emit('error', {'data': error_msg})
        print(error_msg, file=sys.stderr)

def cleanup_process():
    """Clean up the C++ process when the server shuts down"""
    global cpp_process
    if cpp_process and cpp_process.poll() is None:
        try:
            # Send quit command if your executable supports it
            cpp_process.stdin.write("quit\n")
            cpp_process.stdin.flush()
            cpp_process.wait(timeout=3)
        except:
            pass
        
        try:
            # Force termination if still running
            if cpp_process.poll() is None:
                cpp_process.terminate()
                cpp_process.wait(timeout=2)
        except:
            pass

# Register cleanup function
atexit.register(cleanup_process)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
from flask import Flask, request, jsonify, render_template
import subprocess
import os
import sys
from threading import Thread
from queue import Queue

app = Flask(__name__)

# Queue for inter-process communication
output_queue = Queue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute_command():
    data = request.get_json()
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({"error": "Empty command"}), 400
    
    try:
        # Start the C++ process if not already running
        if not hasattr(app, 'cpp_process'):
            start_cpp_process()
        
        # Send command to C++ process
        app.cpp_process.stdin.write(command + "\n")
        app.cpp_process.stdin.flush()
        
        # Get output from queue (non-blocking with timeout)
        output = ""
        try:
            while True:
                output += output_queue.get_nowait()
        except:
            pass
        
        return jsonify({"output": output})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_cpp_process():
    cwd = os.path.dirname(os.path.abspath(__file__))
    exe_path = os.path.join(cwd, "CustomCmd.exe")
    
    if not os.path.exists(exe_path):
        raise FileNotFoundError("CustomCmd.exe not found")
    
    app.cpp_process = subprocess.Popen(
        [exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
        cwd=cwd
    )
    
    # Start thread to capture output
    Thread(target=read_output, args=(app.cpp_process,), daemon=True).start()

def read_output(process):
    while True:
        line = process.stdout.readline()
        if line:
            output_queue.put(line)
        else:
            break

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
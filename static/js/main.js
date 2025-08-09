document.addEventListener("DOMContentLoaded", () => {
    const commandInput = document.getElementById("commandInput");
    const sendCommandBtn = document.getElementById("sendCommand");
    const output = document.getElementById("output");
    
    // Initialize Socket.IO connection
    const socket = io('http://localhost:5000');
    
    // Create status indicator elements (add to HTML)
    const statusIndicator = document.createElement('div');
    statusIndicator.id = 'status-indicator';
    statusIndicator.className = 'status-disconnected';
    document.body.prepend(statusIndicator);
    
    const connectionStatus = document.createElement('div');
    connectionStatus.id = 'connection-status';
    connectionStatus.className = 'connection-status';
    connectionStatus.textContent = 'Disconnected';
    document.body.prepend(connectionStatus);

    // Add initial message
    addOutput("Custom Command Terminal - Ready", "system");
    addOutput("Connecting to server...", "status");

    // Update status indicator
    function updateStatusIndicator(statusClass, text) {
        statusIndicator.className = statusClass;
        connectionStatus.textContent = text;
    }

    // Handle incoming messages
    socket.on('cpp_output', (data) => {
        addOutput(data.data, "output");
    });

    socket.on('status', (data) => {
        addOutput(data.data, "status");
    });

    socket.on('error', (data) => {
        addOutput(`Error: ${data.data}`, "error");
    });

    socket.on('connect', () => {
        updateStatusIndicator('status-connected', 'Connected');
        addOutput("Connected to server", "status");
        addOutput("Type 'help' for available commands", "system");
    });

    socket.on('disconnect', () => {
        updateStatusIndicator('status-disconnected', 'Disconnected');
        addOutput("Disconnected from server", "status");
    });

    socket.on('connect_error', (error) => {
        updateStatusIndicator('status-error', 'Connection Failed');
        addOutput(`Connection error: ${error.message}`, "error");
    });

    // Execute command on button click or Enter key
    sendCommandBtn.addEventListener("click", executeCommand);
    commandInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") executeCommand();
    });

    function executeCommand() {
        const command = commandInput.value.trim();
        if (!command) return;

        // Add user input to terminal
        addOutput(`${command}`, "input");
        commandInput.value = "";
        commandInput.focus();

        // Send command to server via WebSocket
        socket.emit('cpp_input', { data: command });
    }

    function addOutput(text, type = "output") {
        const line = document.createElement("div");
        line.className = type;
        
        // Add prefix based on message type
        if (type === "input") {
            line.innerHTML = `<span class="prompt">&gt; </span>${text}`;
        } else if (type === "status") {
            line.innerHTML = `<span class="status-prefix">● </span>${text}`;
        } else if (type === "error") {
            line.innerHTML = `<span class="error-prefix">! </span>${text}`;
        } else {
            line.textContent = text;
        }
        
        output.appendChild(line);
        output.scrollTop = output.scrollHeight;
    }
});
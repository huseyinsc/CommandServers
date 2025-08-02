document.addEventListener("DOMContentLoaded", () => {
    const commandInput = document.getElementById("commandInput");
    const sendCommand = document.getElementById("sendCommand");
    const output = document.getElementById("output");

    // Add initial message
    addOutput("Custom Command Terminal - Ready\nType 'help' for available commands", "system");

    // Execute command on button click or Enter key
    sendCommand.addEventListener("click", executeCommand);
    commandInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") executeCommand();
    });

    function executeCommand() {
        const command = commandInput.value.trim();
        if (!command) return;

        addOutput(`> ${command}`, "input");
        commandInput.value = "";

        fetch("/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command })
        })
        .then(response => response.json())
        .then(data => {
            if (data.output) {
                addOutput(data.output, "output");
            } else if (data.error) {
                addOutput(`Error: ${data.error}`, "error");
            }
        })
        .catch(error => {
            addOutput(`Communication error: ${error}`, "error");
        });
    }

    function addOutput(text, type = "output") {
        const line = document.createElement("div");
        line.className = type;
        line.textContent = text;
        output.appendChild(line);
        output.scrollTop = output.scrollHeight;
    }
});
document.addEventListener("DOMContentLoaded", () => {
    const serverInput = document.getElementById("serverInput");
    const serverSend = document.getElementById("serverSend");
    const serverOutput = document.getElementById("serverOutput");

    const clientInput = document.getElementById("clientInput");
    const clientSend = document.getElementById("clientSend");
    const clientOutput = document.getElementById("clientOutput");

    function updateTerminal(outputElement, message, isError = false) {
        const messageElement = document.createElement("div");
        messageElement.textContent = `user@machine:~$ ${message}`;
        messageElement.style.color = isError ? "red" : "green";  // Highlight errors
        outputElement.appendChild(messageElement);
        outputElement.scrollTop = outputElement.scrollHeight;
    }

    function sendMessage(inputElement, outputElement) {
        const message = inputElement.value.trim();
        if (message) {
            updateTerminal(outputElement, message);
            inputElement.value = ""; // Clear input field

            fetch("/receive_message", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message }),
            })
            .then((response) => response.json())
            .then((data) => {
                if (data.message) {
                    updateTerminal(outputElement, data.message);
                } else if (data.error) {
                    updateTerminal(outputElement, `Error: ${data.error}`, true);
                }
            })
            .catch((error) => {
                updateTerminal(outputElement, `Error: ${error}`, true);
            });
        }
    }

    serverSend.addEventListener("click", () => {
        sendMessage(serverInput, serverOutput);
    });

    clientSend.addEventListener("click", () => {
        sendMessage(clientInput, clientOutput);
    });
});

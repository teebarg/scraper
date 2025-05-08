const status = document.getElementById("status");
const result = document.getElementById("result");
const productInfo = document.getElementById("productInfo");

document.getElementById("sendButton").addEventListener("click", () => {
    const sendButton = document.getElementById("sendButton");
    const feedback = document.getElementById("feedback");

    // Create loader element
    const loader = document.createElement("div");
    loader.className = "loader";
    loader.style.display = "none";
    feedback.parentNode.insertBefore(loader, feedback);

    sendButton.disabled = true;
    sendButton.style.opacity = 0.5;
    sendButton.style.cursor = "not-allowed";
    // Create and style the loader
    loader.style.display = "block";
    loader.style.width = "50px";
    loader.style.height = "50px";
    loader.style.border = "5px solid #f3f3f3";
    loader.style.borderTop = "5px solid #3498db";
    loader.style.borderRadius = "50%";
    loader.style.animation = "spin 1s linear infinite";
    loader.style.margin = "20px auto";

    // Add keyframe animation
    const style = document.createElement("style");
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.scripting.executeScript(
            {
                target: { tabId: tabs[0].id },
                function: sendHtmlToBackend,
            },
            (injectionResults) => {
                for (const frameResult of injectionResults) {
                    result.classList.add("hidden");
                    if (frameResult.result) {
                        const response = frameResult.result;
                        feedback.textContent = `Response: ${response.message}`;
                        displayProductInfo(response.data);
                    } else {
                        feedback.textContent = "Error sending HTML to backend.";
                    }
                    // Re-enable the button after response
                    sendButton.disabled = false;
                    sendButton.style.opacity = 1;
                    sendButton.style.cursor = "pointer";

                    // Hide loader
                    loader.style.display = "none";
                }
            }
        );
    });
});

function sendHtmlToBackend() {
    // const url = "https://scraper-api.niyi.com.ng/api";
    const url = "http://localhost:8000/";
    const html = document.documentElement.outerHTML;

    return fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "text/plain",
        },
        body: html,
    })
        .then((response) => response.json())
        .then((data) => data)
        .catch((error) => {
            return { message: `Error: ${error}` };
        });
}

function displayProductInfo(data) {
    productInfo.innerHTML = "";
    if (!data) {
        return;
    }
    for (const [key, value] of Object.entries(data)) {
        const li = document.createElement("li");
        li.style.marginTop = "4px";
        const keyElem = document.createElement("span");
        const valElem = document.createElement("span");

        keyElem.textContent = `${key}:`;
        valElem.textContent = `${value}`;

        keyElem.style.marginRight = "4px";
        keyElem.style.fontWeight = 600;
        keyElem.style.textTransform = "capitalize";
        keyElem.style.fontSize = "14px";
        keyElem.style.textDecoration = "underline";

        valElem.style.fontWeight = 500;
        valElem.style.fontSize = "12px";

        li.appendChild(keyElem);
        li.appendChild(valElem);

        productInfo.appendChild(li);
    }
    result.classList.remove("hidden");
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "capture") {
        const htmlContent = document.documentElement.outerHTML;
        console.log("🚀 ~ chrome.runtime.onMessage.addListener ~ htmlContent:", htmlContent)
    }
});

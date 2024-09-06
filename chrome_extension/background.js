console.log("running background js");
chrome.tabs.onUpdated.addListener(function () {
    console.log("TAB UPDATED");
    chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: sendHtmlToBackend,
        // files: ["content.js"],
    });
});

function sendHtmlToBackend() {
    // Implement
}

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

// Global error handler for uncaught errors
window.addEventListener("error", (event) => {
  console.error("[Global Error]", event.error);
});

// Handle unhandled promise rejections
window.addEventListener("unhandledrejection", (event) => {
  console.error("[Unhandled Promise Rejection]", event.reason);
});

// Check for root element
const root = document.getElementById("root");
if (!root) {
  console.error("[Critical] Root element not found!");
  document.body.innerHTML = '<div style="color:red;padding:20px;font-family:sans-serif;"><h1>Error: Root element not found</h1></div>';
} else {
  try {
    console.log("[Init] Starting React app initialization");
    ReactDOM.createRoot(root).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
    console.log("[Init] React app rendered successfully");
  } catch (error) {
    console.error("[Critical] Failed to render React app:", error);
    root.innerHTML = '<div style="color:red;padding:20px;font-family:sans-serif;"><h1>Error: Failed to load application</h1><p>Check browser console for details.</p></div>';
  }
}

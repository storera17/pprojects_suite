import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App.jsx";
import "./styles/global.css";
import "./styles/layout.css";
import "./styles/panels.css";
import "./styles/charts.css";
import "./styles/forms.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
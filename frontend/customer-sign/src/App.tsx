import { BrowserRouter, Routes, Route } from "react-router-dom";
import ConfirmPage from "./pages/ConfirmPage";
import SuccessPage from "./pages/SuccessPage";

export default function App() {
  return (
    <BrowserRouter basename="/sign">
      <Routes>
        <Route path="/confirm/:token" element={<ConfirmPage />} />
        <Route path="/success" element={<SuccessPage />} />
        <Route path="*" element={
          <div className="flex items-center justify-center min-h-screen text-gray-400">
            <p>Scan QR code to access inspection report</p>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  );
}

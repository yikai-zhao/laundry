import { Link } from "react-router-dom";

export default function SuccessPage() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center space-y-4 p-6">
        <div className="text-6xl">✅</div>
        <h1 className="text-2xl font-bold text-green-600">Thank You!</h1>
        <p className="text-gray-500">Your confirmation has been submitted successfully.</p>
        <p className="text-sm text-gray-400">You can close this page now.</p>
      </div>
    </div>
  );
}

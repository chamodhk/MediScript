import { useEffect, useState } from "react";
import api from "../../services/api";

function PharmacyHeader({ pharmacyId, pendingCount }) {
  const [userName, setUserName] = useState("Pharmacist");

  useEffect(() => {
    let isMounted = true;

    const loadUser = async () => {
      try {
        const { data } = await api.get("/auth/me");
        if (!isMounted) {
          return;
        }
        setUserName(data?.full_name || data?.email || "Pharmacist");
      } catch {
        if (!isMounted) {
          return;
        }
        setUserName("Pharmacist");
      }
    };

    loadUser();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("accessToken");
    window.location.href = "/";
  };

  return (
    <header className="bg-hemas-dark border-b border-white/10 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="text-hemas-teal font-bold text-xl tracking-wide">
          MediScript
        </span>
        <span className="text-white/70">Pharmacy {pharmacyId}</span>
      </div>

      <div className="flex items-center gap-4">
        {pendingCount > 0 && (
          <span className="bg-hemas-orange text-white text-sm font-semibold px-3 py-1 rounded-full">
            {pendingCount} pending
          </span>
        )}

        <span className="text-white/80 text-sm">{userName}</span>

        <button
          type="button"
          onClick={handleLogout}
          className="border border-white/20 text-white/90 px-3 py-1.5 rounded-md hover:bg-white/10 transition-all duration-200"
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default PharmacyHeader;

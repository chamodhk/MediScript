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
    <header className="flex items-center justify-between border-b border-slate-200 bg-white/95 px-6 py-4 shadow-sm backdrop-blur">
      <div className="flex items-center gap-3">
        <span className="text-xl font-bold tracking-wide text-[#08263e]">
          MediScript
        </span>
        <span className="rounded-full border border-[#00687f]/25 bg-[#00687f]/10 px-3 py-1 text-sm font-medium text-[#025567]">
          Pharmacy {pharmacyId}
        </span>
      </div>

      <div className="flex items-center gap-4">
        {pendingCount > 0 && (
          <span className="rounded-full bg-[#e75424] px-3 py-1 text-sm font-semibold text-white shadow-sm">
            {pendingCount} pending
          </span>
        )}

        <span className="text-sm font-medium text-slate-600">{userName}</span>

        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition-all duration-200 hover:border-[#00687f]/45 hover:bg-[#00687f]/10 hover:text-[#025567]"
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default PharmacyHeader;

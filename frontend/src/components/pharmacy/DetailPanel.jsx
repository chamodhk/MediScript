import { useEffect, useState } from "react";
import StatusBadge from "./StatusBadge";
import { fetchPrescriptionImageAsBlob } from "../../services/pharmacyApi";

function formatSubmissionTime(createdAt) {
  if (!createdAt) {
    return "--";
  }

  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

function getAdvanceConfig(status) {
  if (status === "pending") {
    return {
      label: "▶ Start Preparing",
      className: "bg-[#e75424] hover:bg-[#cf491d]",
    };
  }

  if (status === "preparing") {
    return {
      label: "✓ Mark as Ready",
      className: "bg-[#025567] hover:bg-[#014452]",
    };
  }

  if (status === "ready") {
    return {
      label: "📦 Mark as Collected",
      className: "bg-[#025567] hover:bg-[#014452]",
    };
  }

  return null;
}

export default function DetailPanel({
  prescription,
  onAdvanceStatus,
  isUpdating,
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const [imageUrl, setImageUrl] = useState(null);

  useEffect(() => {
    setImageFailed(false);
  }, [prescription?.id]);

  useEffect(() => {
    let isMounted = true;
    let createdUrl = null;

    const loadImage = async () => {
      if (!prescription?.id) {
        setImageUrl((prev) => {
          if (prev) {
            URL.revokeObjectURL(prev);
          }
          return null;
        });
        return;
      }

      try {
        const nextUrl = await fetchPrescriptionImageAsBlob(prescription.id);
        if (!isMounted) {
          URL.revokeObjectURL(nextUrl);
          return;
        }

        createdUrl = nextUrl;
        setImageUrl((prev) => {
          if (prev) {
            URL.revokeObjectURL(prev);
          }
          return nextUrl;
        });
      } catch {
        if (isMounted) {
          setImageFailed(true);
          setImageUrl((prev) => {
            if (prev) {
              URL.revokeObjectURL(prev);
            }
            return null;
          });
        }
      }
    };

    loadImage();

    return () => {
      isMounted = false;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [prescription?.id]);

  if (!prescription) {
    return (
      <aside className="flex min-h-[24rem] items-center justify-center rounded-2xl border border-slate-200 bg-white/95 p-6 shadow-sm">
        <p className="text-center text-sm text-slate-500">
          Select a prescription from the queue to view details.
        </p>
      </aside>
    );
  }

  const advanceConfig = getAdvanceConfig(prescription.status);

  return (
    <aside className="h-full rounded-2xl border border-slate-200 bg-white/95 p-6 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-2xl font-bold text-slate-800">
          {prescription.patient_name ?? "Unknown Patient"}
        </h2>
        <StatusBadge status={prescription.status} />
      </div>

      <p className="mt-2 text-sm text-slate-600">
        {prescription.patient_phone ?? "No phone available"}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        Submitted at {formatSubmissionTime(prescription.created_at)}
      </p>

      <div className="mt-6">
        <h3 className="mb-2 text-sm font-medium text-slate-700">
          Prescription Image
        </h3>

        {imageFailed || !imageUrl ? (
          <div className="flex h-64 w-full items-center justify-center rounded-xl border border-slate-200 bg-slate-50">
            <p className="text-sm text-slate-500">No image available</p>
          </div>
        ) : (
          <img
            src={imageUrl}
            alt="Prescription"
            onError={() => setImageFailed(true)}
            className="h-64 w-full rounded-xl border border-slate-200 bg-slate-50 object-contain"
          />
        )}
      </div>

      <div className="mt-6">
        {prescription.status === "collected" ? (
          <p className="text-sm font-semibold text-slate-600">✅ Collected</p>
        ) : (
          <button
            type="button"
            onClick={() => onAdvanceStatus?.()}
            disabled={isUpdating}
            className={`w-full rounded-lg px-4 py-3 text-sm font-semibold text-white transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-[#025567]/20 disabled:cursor-not-allowed disabled:opacity-60 ${advanceConfig?.className ?? "bg-[#025567]"}`}
          >
            {isUpdating ? "Updating..." : advanceConfig?.label}
          </button>
        )}
      </div>
    </aside>
  );
}

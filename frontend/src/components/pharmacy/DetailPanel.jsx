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
      className: "bg-hemas-orange hover:opacity-90",
    };
  }

  if (status === "preparing") {
    return {
      label: "✓ Mark as Ready",
      className: "bg-hemas-teal hover:opacity-90",
    };
  }

  if (status === "ready") {
    return {
      label: "📦 Mark as Collected",
      className: "bg-hemas-teal hover:opacity-90",
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
      <aside className="bg-hemas-navy p-6 rounded-xl min-h-[24rem] flex items-center justify-center">
        <p className="text-sm text-white/50 text-center">
          Select a prescription from the queue to view details.
        </p>
      </aside>
    );
  }

  const advanceConfig = getAdvanceConfig(prescription.status);

  return (
    <aside className="bg-hemas-navy p-6 rounded-xl h-full">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-2xl font-bold text-white">
          {prescription.patient_name ?? "Unknown Patient"}
        </h2>
        <StatusBadge status={prescription.status} />
      </div>

      <p className="mt-2 text-sm text-white/70">
        {prescription.patient_phone ?? "No phone available"}
      </p>
      <p className="mt-1 text-xs text-white/60">
        Submitted at {formatSubmissionTime(prescription.created_at)}
      </p>

      <div className="mt-6">
        <h3 className="text-sm font-medium text-white/80 mb-2">
          Prescription Image
        </h3>

        {imageFailed || !imageUrl ? (
          <div className="h-64 w-full rounded-lg border border-white/10 bg-gray-700/30 flex items-center justify-center">
            <p className="text-sm text-white/60">No image available</p>
          </div>
        ) : (
          <img
            src={imageUrl}
            alt="Prescription"
            onError={() => setImageFailed(true)}
            className="h-64 w-full rounded-lg border border-white/10 object-contain bg-black/20"
          />
        )}
      </div>

      <div className="mt-6">
        {prescription.status === "collected" ? (
          <p className="text-sm font-semibold text-white/70">✅ Collected</p>
        ) : (
          <button
            type="button"
            onClick={() => onAdvanceStatus?.()}
            disabled={isUpdating}
            className={`w-full rounded-lg px-4 py-3 text-sm font-semibold text-white transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60 ${advanceConfig?.className ?? "bg-hemas-teal"}`}
          >
            {isUpdating ? "Updating..." : advanceConfig?.label}
          </button>
        )}
      </div>
    </aside>
  );
}

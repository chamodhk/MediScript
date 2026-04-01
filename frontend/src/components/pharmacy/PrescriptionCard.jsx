import StatusBadge from "./StatusBadge";

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

export default function PrescriptionCard({
  prescription,
  isSelected,
  onClick,
}) {
  const cardClasses = isSelected
    ? "border-2 border-[#00687f] bg-[#00687f]/10 shadow-sm"
    : "border border-slate-200 bg-white hover:bg-slate-50";

  const handleClick = () => {
    onClick?.(prescription);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`w-full cursor-pointer rounded-xl p-4 text-left transition-all duration-200 ${cardClasses}`}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-semibold text-slate-800">
          {prescription?.patient_name ?? "Unknown Patient"}
        </p>
        <StatusBadge status={prescription?.status} />
      </div>

      <p className="mt-2 text-xs text-slate-500">
        {formatSubmissionTime(prescription?.created_at)}
      </p>
    </button>
  );
}

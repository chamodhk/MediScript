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
    ? "border-2 border-hemas-teal bg-hemas-teal/10"
    : "border border-white/10 hover:bg-hemas-teal/5";

  const handleClick = () => {
    onClick?.(prescription);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`w-full bg-hemas-navy rounded-lg p-4 cursor-pointer text-left transition-all duration-200 ${cardClasses}`}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-semibold text-white">
          {prescription?.patient_name ?? "Unknown Patient"}
        </p>
        <StatusBadge status={prescription?.status} />
      </div>

      <p className="mt-2 text-xs text-white/70">
        {formatSubmissionTime(prescription?.created_at)}
      </p>
    </button>
  );
}

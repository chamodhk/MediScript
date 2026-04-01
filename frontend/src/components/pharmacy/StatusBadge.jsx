const STATUS_STYLES = {
  pending: "border border-amber-300 bg-amber-50 text-amber-700",
  preparing: "border border-orange-300 bg-orange-50 text-orange-700",
  ready: "border border-emerald-300 bg-emerald-50 text-emerald-700",
  collected: "border border-slate-300 bg-slate-100 text-slate-600",
};

function toLabel(status) {
  if (!status) {
    return "Unknown";
  }
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.pending;

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium transition-all duration-200 ${style}`}
    >
      {toLabel(status)}
    </span>
  );
}

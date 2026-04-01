const STATUS_STYLES = {
  pending: "bg-gray-500/20 text-gray-400 border border-gray-500",
  preparing: "bg-hemas-orange/20 text-hemas-orange border border-hemas-orange",
  ready: "bg-hemas-teal/20 text-hemas-teal border border-hemas-teal",
  collected: "bg-white/5 text-white/30 border border-white/10",
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

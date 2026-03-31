import PrescriptionCard from "./PrescriptionCard";

const FILTER_OPTIONS = [
  { label: "All Active", value: "pending,preparing,ready" },
  { label: "Pending", value: "pending" },
  { label: "Preparing", value: "preparing" },
  { label: "Ready", value: "ready" },
  { label: "Collected", value: "collected" },
];

export default function QueuePanel({
  queue,
  selectedId,
  onCardClick,
  filter,
  onFilterChange,
  isLoading,
}) {
  const items = Array.isArray(queue) ? queue : [];

  return (
    <section className="flex h-full flex-col bg-hemas-dark p-4">
      <label className="mb-3 block">
        <span className="mb-1 block text-xs uppercase tracking-wide text-white/60">
          Filter
        </span>
        <select
          value={filter}
          onChange={(event) => onFilterChange?.(event.target.value)}
          className="w-full rounded-md border border-white/15 bg-hemas-navy px-3 py-2 text-sm text-white outline-none transition-all duration-200 focus:border-hemas-teal"
        >
          {FILTER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      {isLoading ? (
        <div className="flex-1 space-y-3 overflow-y-auto pr-1">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              key={index}
              className="rounded-lg bg-hemas-navy p-4 animate-pulse"
            >
              <div className="mb-3 h-4 w-3/4 rounded bg-white/20" />
              <div className="h-3 w-1/2 rounded bg-white/10" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-1 items-center justify-center px-4 text-center text-sm text-white/40">
          All clear — no pending prescriptions right now.
        </div>
      ) : (
        <div className="flex-1 space-y-3 overflow-y-auto pr-1">
          {items.map((prescription) => (
            <PrescriptionCard
              key={prescription.id}
              prescription={prescription}
              isSelected={prescription.id === selectedId}
              onClick={onCardClick}
            />
          ))}
        </div>
      )}
    </section>
  );
}

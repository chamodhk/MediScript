import { useCallback, useEffect, useMemo, useState } from "react";
import PharmacyHeader from "../components/pharmacy/PharmacyHeader";
import QueuePanel from "../components/pharmacy/QueuePanel";
import DetailPanel from "../components/pharmacy/DetailPanel";
import {
  advanceStatus,
  fetchQueue as fetchQueueApi,
} from "../services/pharmacyApi";

const POLL_INTERVAL_MS = 10_000;

function getNextStatus(currentStatus) {
  if (currentStatus === "pending") {
    return "preparing";
  }
  if (currentStatus === "preparing") {
    return "ready";
  }
  if (currentStatus === "ready") {
    return "collected";
  }
  return null;
}

function formatLastUpdated(timestamp) {
  if (!timestamp) {
    return "";
  }

  const diffMs = Date.now() - timestamp.getTime();
  if (diffMs < 15_000) {
    return "Updated just now";
  }

  return `Updated ${timestamp.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  })}`;
}

export default function PharmacyPortal({ pharmacyId }) {
  const [queue, setQueue] = useState([]);
  const [selectedPrescription, setSelectedPrescription] = useState(null);
  const [filter, setFilter] = useState("pending,preparing,ready");
  const [isUpdating, setIsUpdating] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  const pendingCount = useMemo(() => {
    return queue.filter((item) => item.status === "pending").length;
  }, [queue]);

  const loadQueue = useCallback(async () => {
    try {
      const data = await fetchQueueApi(pharmacyId, filter);
      const nextQueue = Array.isArray(data) ? data : [];

      setQueue(nextQueue);
      setFetchError(null);
      setSelectedPrescription((currentSelected) => {
        if (!currentSelected?.id) {
          return currentSelected;
        }

        const updatedSelected = nextQueue.find(
          (item) => item.id === currentSelected.id,
        );

        return updatedSelected || currentSelected;
      });
      setLastUpdated(new Date());
    } catch (error) {
      const message =
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to load queue";
      setFetchError(message);
      console.error("Failed to fetch pharmacy queue", error);
    } finally {
      setIsLoading(false);
    }
  }, [pharmacyId, filter]);

  useEffect(() => {
    loadQueue();

    const intervalId = setInterval(() => {
      loadQueue();
    }, POLL_INTERVAL_MS);

    return () => {
      clearInterval(intervalId);
    };
  }, [loadQueue]);

  const handleCardClick = (prescription) => {
    setSelectedPrescription(prescription);
  };

  const handleAdvanceStatus = async () => {
    if (!selectedPrescription?.id) {
      return;
    }

    const nextStatus = getNextStatus(selectedPrescription.status);
    if (!nextStatus) {
      return;
    }

    setIsUpdating(true);
    try {
      const updated = await advanceStatus(selectedPrescription.id, nextStatus);
      setSelectedPrescription((current) => {
        if (!current?.id || current.id !== selectedPrescription.id) {
          return current;
        }
        return { ...current, status: updated?.status ?? nextStatus };
      });
      await loadQueue();
    } catch (error) {
      console.error("Failed to advance prescription status", error);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="h-screen bg-hemas-dark text-white flex flex-col">
      <PharmacyHeader pharmacyId={pharmacyId} pendingCount={pendingCount} />

      <main className="flex h-full min-h-0">
        <section className="w-1/3 min-h-0 border-r border-white/10 overflow-y-auto">
          <div className="px-4 pt-4">
            {fetchError ? (
              <div className="mb-2 bg-red-900/30 text-red-400 text-sm p-2 rounded">
                Failed to load queue. Retrying...
              </div>
            ) : null}
            <p className="text-xs text-white/50">
              {formatLastUpdated(lastUpdated)}
            </p>
          </div>
          <QueuePanel
            queue={queue}
            selectedId={selectedPrescription?.id ?? null}
            onCardClick={handleCardClick}
            filter={filter}
            onFilterChange={setFilter}
            isLoading={isLoading}
          />
        </section>

        <section className="w-2/3 p-4 min-h-0">
          <DetailPanel
            prescription={selectedPrescription}
            onAdvanceStatus={handleAdvanceStatus}
            isUpdating={isUpdating}
          />
        </section>
      </main>
    </div>
  );
}

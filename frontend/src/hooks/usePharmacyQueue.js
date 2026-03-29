import { useState, useEffect } from "react";

export function usePharmacyQueue(pharmacyId) {
  const [queue, setQueue] = useState([]);

  // TODO: implement polling / WebSocket for live queue
  useEffect(() => {}, [pharmacyId]);

  return { queue, setQueue };
}

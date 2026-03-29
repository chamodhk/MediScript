import { useState } from "react";

export function useConsultation() {
  const [consultation, setConsultation] = useState(null);

  // TODO: implement consultation state management
  return { consultation, setConsultation };
}

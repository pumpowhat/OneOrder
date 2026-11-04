import { useEffect } from "react";

export function useDocumentTitle(title?: string): void {
  useEffect(() => {
    document.title = title
      ? `${title} · OneOrder`
      : "OneOrder — B2B Order Orchestration";
  }, [title]);
}

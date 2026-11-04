import { useState, useCallback, useMemo, type ReactNode } from "react";
import { SidebarContext } from "./SidebarContext.ts";
import { readStorage, writeStorage } from "../../lib/storage.ts";

const STORAGE_KEY = "oneorder.sidebarCollapsed";

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsedState] = useState<boolean>(() => {
    return readStorage(STORAGE_KEY) === "true";
  });

  const setCollapsed = useCallback((next: boolean) => {
    setCollapsedState(next);
    writeStorage(STORAGE_KEY, String(next));
  }, []);

  const toggleCollapsed = useCallback(() => {
    setCollapsedState((prev) => {
      const next = !prev;
      writeStorage(STORAGE_KEY, String(next));
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ collapsed, setCollapsed, toggleCollapsed }),
    [collapsed, setCollapsed, toggleCollapsed],
  );

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
}

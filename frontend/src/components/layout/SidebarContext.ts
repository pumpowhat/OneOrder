import { createContext } from "react";

export interface SidebarContextValue {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  toggleCollapsed: () => void;
}

export const SidebarContext = createContext<SidebarContextValue | null>(null);

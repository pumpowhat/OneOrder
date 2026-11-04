import { useContext } from "react";
import { ThemeContext, type ThemeContextType } from "./themeContext.ts";

export function useTheme(): ThemeContextType {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
}

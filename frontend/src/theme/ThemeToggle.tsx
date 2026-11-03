import { Sun, Moon } from "lucide-react";
import { useTheme } from "./useTheme.ts";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      }
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className="cursor-pointer inline-flex items-center justify-center w-8 h-8 rounded-lg border border-line bg-surface-2 hover:bg-surface text-ink-muted hover:text-ink transition-colors focus-visible:outline-2 focus-visible:outline-brand"
    >
      {theme === "dark" ? (
        <Sun className="w-4 h-4 text-warn" aria-hidden="true" />
      ) : (
        <Moon className="w-4 h-4 text-ink-muted" aria-hidden="true" />
      )}
    </button>
  );
}

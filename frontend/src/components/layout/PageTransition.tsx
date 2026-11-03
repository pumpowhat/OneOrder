import { useEffect } from "react";
import { useLocation, Outlet } from "react-router";

export function PageTransition() {
  const location = useLocation();

  useEffect(() => {
    const mainEl = document.getElementById("main-content");
    if (mainEl) {
      mainEl.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
    }
  }, [location.pathname]);

  return (
    <div key={location.pathname} className="animate-page-enter">
      <Outlet />
    </div>
  );
}

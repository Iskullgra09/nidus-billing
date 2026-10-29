"use client";

import * as React from "react";

const STORAGE_KEY = "nidus-sidebar-collapsed";

type SidebarContextValue = {
  collapsed: boolean;
  mobileOpen: boolean;
  setCollapsed: (value: boolean) => void;
  toggleCollapsed: () => void;
  setMobileOpen: (value: boolean) => void;
  toggleMobileOpen: () => void;
};

const SidebarContext = React.createContext<SidebarContextValue | null>(null);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsedState] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);

  React.useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored === "1") setCollapsedState(true);
    } catch {}
  }, []);

  const setCollapsed = React.useCallback((value: boolean) => {
    setCollapsedState(value);
    try {
      window.localStorage.setItem(STORAGE_KEY, value ? "1" : "0");
    } catch {}
  }, []);

  const toggleCollapsed = React.useCallback(() => {
    setCollapsedState((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
      } catch {}
      return next;
    });
  }, []);

  const toggleMobileOpen = React.useCallback(() => {
    setMobileOpen((prev) => !prev);
  }, []);

  const value = React.useMemo(
    () => ({
      collapsed,
      mobileOpen,
      setCollapsed,
      toggleCollapsed,
      setMobileOpen,
      toggleMobileOpen,
    }),
    [collapsed, mobileOpen, setCollapsed, toggleCollapsed, toggleMobileOpen],
  );

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
}

export function useSidebar() {
  const ctx = React.useContext(SidebarContext);
  if (!ctx) {
    throw new Error("useSidebar must be used within SidebarProvider");
  }
  return ctx;
}

import React, { createContext, useContext, useState, useCallback } from "react";
import type { ArtifactMode, PaneType, UIState } from "../types";

interface UIContextType extends UIState {
  setActivePane: (pane: PaneType) => void;
  setArtifactMode: (mode: ArtifactMode) => void;
  toggleArtifact: (show?: boolean) => void;
}

const UIContext = createContext<UIContextType | undefined>(undefined);

export function UIProvider({ children }: { children: React.ReactNode }) {
  const [activePane, setActivePane] = useState<PaneType>("chat");
  const [artifactMode, setArtifactMode] = useState<ArtifactMode>("none");
  const [showArtifact, setShowArtifact] = useState(false);

  // Auto-show artifact pane if mode changes to something visible
  const handleSetArtifactMode = useCallback((mode: ArtifactMode) => {
    setArtifactMode(mode);
    if (mode !== "none") {
      setShowArtifact(true);
      // Optional: Auto-focus artifact pane? Maybe not, keep focus on chat usually.
    } else {
      setShowArtifact(false);
    }
  }, []);

  const handleToggleArtifact = useCallback((show?: boolean) => {
    setShowArtifact((prev) => (show !== undefined ? show : !prev));
  }, []);

  return (
    <UIContext.Provider
      value={{
        activePane,
        artifactMode,
        showArtifact,
        leftPaneWidth: showArtifact ? "50%" : "100%",
        setActivePane,
        setArtifactMode: handleSetArtifactMode,
        toggleArtifact: handleToggleArtifact,
      }}
    >
      {children}
    </UIContext.Provider>
  );
}

export function useUI() {
  const context = useContext(UIContext);
  if (!context) {
    throw new Error("useUI must be used within a UIProvider");
  }
  return context;
}

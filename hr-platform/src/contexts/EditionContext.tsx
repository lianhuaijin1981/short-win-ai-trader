import React, { createContext, useContext, useState, useCallback } from 'react';
import type { PlatformEdition, EditionFeatures } from '@/types';
import { EDITION_FEATURES } from '@/types';

interface EditionContextType {
  edition: PlatformEdition;
  features: EditionFeatures;
  setEdition: (edition: PlatformEdition) => void;
  hasFeature: (feature: keyof EditionFeatures) => boolean;
}

const EditionContext = createContext<EditionContextType | undefined>(undefined);

export const EditionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [edition, setEditionState] = useState<PlatformEdition>('standard');

  const features = EDITION_FEATURES[edition];

  const setEdition = useCallback((newEdition: PlatformEdition) => {
    setEditionState(newEdition);
  }, []);

  const hasFeature = useCallback((feature: keyof EditionFeatures) => {
    return EDITION_FEATURES[edition][feature];
  }, [edition]);

  return (
    <EditionContext.Provider value={{ edition, features, setEdition, hasFeature }}>
      {children}
    </EditionContext.Provider>
  );
};

export const useEdition = () => {
  const context = useContext(EditionContext);
  if (!context) {
    throw new Error('useEdition must be used within EditionProvider');
  }
  return context;
};
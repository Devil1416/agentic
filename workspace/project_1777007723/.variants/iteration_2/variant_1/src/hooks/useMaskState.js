import { useState } from 'react';
import create from 'zustand';

const useMaskStore = create((set) => ({
  color: '#000',
  patternId: '',
  animationSpeed: 1,
  setColor: (color) => set({ color }),
  setPatternId: (patternId) => set({ patternId }),
  setAnimationSpeed: (animationSpeed) => set({ animationSpeed })
}));

export const useMaskState = () => {
  const [localState, setLocalState] = useState(useMaskStore.getState());
  
  // Subscribe to changes in the global state
  useMaskStore((state) => ({
    color: state.color,
    patternId: state.patternId,
    animationSpeed: state.animationSpeed,
  }), (state) => {
    setLocalState(state);
  });
  
  return localState;
};
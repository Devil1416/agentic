import { useState } from 'react';
import create from 'zustand';

const useMaskStore = create((set) => ({
  color: '#000000',
  patternId: '',
  animationSpeed: 1,
  setColor: (color) => set(() => ({ color })),
  setPatternId: (patternId) => set(() => ({ patternId })),
  setAnimationSpeed: (animationSpeed) => set(() => ({ animationSpeed }))
}));

export const useMaskState = () => {
  const [localColor, setLocalColor] = useState(useMaskStore.getState().color);
  const [localPatternId, setLocalPatternId] = useState(useMaskStore.getState().patternId);
  const [localAnimationSpeed, setLocalAnimationSpeed] = useState(useMaskStore.getState().animationSpeed);
  
  // Subscribe to changes in the global state
  useEffect(() => {
    const unsubscribe = useMaskStore.subscribe((state) => {
      setLocalColor(state.color);
      setLocalPatternId(state.patternId);
      setLocalAnimationSpeed(state.animationSpeed);
    }, false); // Pass `false` to not trigger on initial state change
  
    return unsubscribe;
  }, []);

  const updateColor = (newColor) => {
    useMaskStore.getState().setColor(newColor);
  };

  const updatePatternId = (newPatternId) => {
    useMaskStore.getState().setPatternId(newPatternId);
  };

  const updateAnimationSpeed = (newAnimationSpeed) => {
    useMaskStore.getState().setAnimationSpeed(newAnimationSpeed);<｜begin▁of▁sentence｜>);
  };

  return {
    color: localColor,
    patternId: localPatternId,
    animationSpeed: localAnimationSpeed,
    updateColor,
    updatePatternId,
    updateAnimationSpeed
  };
};
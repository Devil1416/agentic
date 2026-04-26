import { useState } from 'react';
import create from 'zustand';

const useMaskStore = create((set) => ({
  color: '#000',
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
    }, false); // The second argument is shallow equal check, we don't need it here
  
    return unsubscribe;
  }, []);
  
  const updateColor = (color) => {
    useMaskStore.getState().setColor(color);
  };
  
  const updatePatternId = (patternId) => {
    useMaskStore.getState().setPatternId(patternId);
  };
  
  const updateAnimationSpeed = (animationSpeed) => {
    useMaskStore.getState().setAnimationSpeed(animationSpeed);<｜begin▁of▁sentence｜>
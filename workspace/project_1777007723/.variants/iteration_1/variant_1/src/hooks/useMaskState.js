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
  const [localColor, localSetColor] = useState(useMaskStore((state) => state.color));
  const [localPatternId, localSetPatternId] = useState(useMaskStore((state) => state.patternId));
  const [localAnimationSpeed, localSetAnimationSpeed] = useState(useMaskStore((state) => state.animationSpeed));
  
  return {
    color: localColor,
    patternId: localPatternId,
    animationSpeed: localAnimationSpeed,<｜begin▁of▁sentence｜>
import React from 'react';
import { Canvas } from '@react-three/fiber';
import MaskOverlay from './components/MaskOverlay';
import useMaskState from './hooks/useMaskState';

const App = () => {
  const { maskProps, updateMaskProps } = useMaskState();
  
  return (
    <div className="app-container">
      <Canvas>
        <ambientLight />
        <pointLight position={[10, 10, 10]} />
        {/* Assuming characterModel is a component that renders the main character model */}
        <characterModel /> 
        <MaskOverlay {...maskProps} updateMaskProps={updateMaskProps} />
      </Canvas>
    </div>
  );
};

export default App;
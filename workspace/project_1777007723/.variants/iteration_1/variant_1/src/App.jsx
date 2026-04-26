import React from 'react';
import { Canvas } from '@react-three/fiber';
import MaskOverlay from './components/MaskOverlay';
import useMaskState from './hooks/useMaskState';

const App = () => {
  const { color, patternId, animationSpeed } = useMaskState();
  
  return (
    <div className="mask-overlay-container">
      <Canvas style={{ background: '#27282c' }}>
        <ambientLight />
        <pointLight position={[10, 10, 10]} />
        <MaskOverlay color={color} patternId={patternId} animationSpeed={animationSpeed} />
      </Canvas>
    </div>
  );
};

export default App;
import React from 'react';
import { Canvas } from '@react-three/fiber';
import MaskOverlay from './components/MaskOverlay';
import useMaskState from './hooks/useMaskState';

const App = () => {
  const [maskProps, setMaskProps] = useMaskState();
  
  return (
    <div className="app-container">
      <Canvas>
        <ambientLight />
        <pointLight position={[10, 10, 10]} />
        {/* Assuming characterModel is a component that renders the main character model */}
        <characterModel /> 
        <MaskOverlay {...maskProps} />
      </Canvas>
      {/* Control panel or trigger mechanism to test dynamic changes */}
      <div className="controls">
        {/* Example: Button that changes mask color when clicked */}
        <button onClick={() => setMaskProps({ color: '#ff0000' })}>Change Mask Color</button>
      </div>
    </div>
  );
};

export default App;
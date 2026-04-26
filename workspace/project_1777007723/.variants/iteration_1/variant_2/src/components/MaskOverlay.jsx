import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useMaskState } from './hooks/useMaskState';

const MaskOverlay = () => {
  const canvasRef = useRef(null);
  const { color, patternId, animationSpeed } = useMaskState();
  
  useEffect(() => {
    // Initialize WebGL renderer and scene
    const renderer = new THREE.WebGLRenderer({canvas: canvasRef.current});
    const scene = new THREE.Scene();
    
    // Create a camera
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 2;
  
    // Load and apply the mask texture based on patternId
    const loader = new THREE.TextureLoader();
    const material = new THREE.MeshBasicMaterial({ map: loader.load(`/path/to/textures/pattern${patternId}.jpg`) });
  
    // Create a cube to represent the mask and add it to the scene
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const cube = new THREE.Mesh(geometry, material);
    scene.add(cube);
  
    // Animation function that updates the mask's color and position over time
    const animate = () => {
      requestAnimationFrame(animate);
      
      // Update cube's color based on state
      cube.material.color.set(new THREE.Color(color));
  
      // Apply animation speed to the cube's rotation over time
      cube.rotation.x += animationSpeed;
      cube.rotation.y += animationSpeed;
      
      renderer.render(scene, camera);
    };
    
    animate();
  }, [color, patternId, animationSpeed]); // Run effect on color, patternId and animationSpeed changes
  
  return <canvas ref={canvasRef} />;
};

export default MaskOverlay;
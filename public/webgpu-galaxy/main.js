import * as THREE from 'three/webgpu';
import { pass } from 'three/tsl';
import { bloom } from 'three/addons/tsl/display/BloomNode.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GalaxySimulation } from './galaxy.js';
import { GalaxyUI } from './ui.js';

// Configuration
const config = {
  starCount: 300000, // Real GPU particle count; 300 million would exceed normal browser GPU memory
  rotationSpeed: 0.1,
  spiralTightness: 2.15,
  mouseForce: 7.0,
  mouseRadius: 10.0,
  galaxyRadius: 14.0,
  galaxyThickness: 2.8,
  armCount: 4,
  armWidth: 2.25,
  randomness: 1.35,
  particleSize: 0.00001, // Extremely tiny stars; visible only at extreme zoom
  starBrightness: 0.48,
  denseStarColor: '#3998ff',
  sparseStarColor: '#ffb36b',
  bloomStrength: 0.24,
  bloomRadius: 0.12,
  bloomThreshold: 0.28,
  cloudCount: 18000, // GPU-safe real count; millions need a different hierarchical renderer
  cloudSize: 0.00001, // Extremely tiny cloud particles; visible only at extreme zoom
  cloudOpacity: 0.10,
  cloudTintColor: '#9bbdff'
};

// Scene setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);

const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.set(0, 12, 17);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGPURenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);

// Orbit controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.minDistance = 5;
controls.maxDistance = 30;
controls.target.set(0, -2, 0);

// Post-processing
let postProcessing = null;
let bloomPassNode = null;

// Mouse tracking
const mouse3D = new THREE.Vector3(0, 0, 0);
const raycaster = new THREE.Raycaster();
const intersectionPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
let mousePressed = false;

window.addEventListener('mousedown', () => mousePressed = true);
window.addEventListener('mouseup', () => mousePressed = false);
window.addEventListener('mousemove', (event) => {
  const mouse = new THREE.Vector2(
    (event.clientX / window.innerWidth) * 2 - 1,
    -(event.clientY / window.innerHeight) * 2 + 1
  );
  raycaster.setFromCamera(mouse, camera);
  raycaster.ray.intersectPlane(intersectionPlane, mouse3D);
});

/**
 * Creates a starry background with random colored stars distributed on a sphere
 * @param {THREE.Scene} scene - Scene to add stars to
 * @param {number} count - Number of background stars
 * @returns {THREE.Points} - The star points object
 */
function createStarryBackground(scene, count = 5000) {
  const starGeometry = new THREE.BufferGeometry();
  const starPositions = new Float32Array(count * 3);
  const starColors = new Float32Array(count * 3);

  // Distribute stars randomly on a sphere
  for (let i = 0; i < count; i++) {
    // Spherical coordinates for uniform distribution
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const radius = 100 + Math.random() * 100;

    // Convert to Cartesian coordinates
    starPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    starPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
    starPositions[i * 3 + 2] = radius * Math.cos(phi);

    // Add color variation (mostly white, some blue/orange tinted)
    const color = 0.8 + Math.random() * 0.2;
    const tint = Math.random();
    if (tint < 0.1) {
      // Blue tint
      starColors[i * 3] = color * 0.8;
      starColors[i * 3 + 1] = color * 0.9;
      starColors[i * 3 + 2] = color;
    } else if (tint < 0.2) {
      // Orange tint
      starColors[i * 3] = color;
      starColors[i * 3 + 1] = color * 0.8;
      starColors[i * 3 + 2] = color * 0.6;
    } else {
      // White
      starColors[i * 3] = color;
      starColors[i * 3 + 1] = color;
      starColors[i * 3 + 2] = color;
    }
  }

  starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
  starGeometry.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

  const starMaterial = new THREE.PointsMaterial({
    size: 0.3,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    sizeAttenuation: true
  });

  const stars = new THREE.Points(starGeometry, starMaterial);
  scene.add(stars);

  return stars;
}

// Preload cloud texture
function createProceduralCloudTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 256;
  const ctx = canvas.getContext('2d');
  if (!ctx) return new THREE.Texture();
  const glow = ctx.createRadialGradient(128, 128, 4, 128, 128, 122);
  glow.addColorStop(0, 'rgba(255,255,255,0.88)');
  glow.addColorStop(0.18, 'rgba(235,244,255,0.62)');
  glow.addColorStop(0.42, 'rgba(160,190,255,0.24)');
  glow.addColorStop(0.72, 'rgba(100,140,255,0.07)');
  glow.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, 256, 256);
  // Uneven wisps make overlapping cloud particles read as gas, not solid dots.
  for (let i = 0; i < 42; i++) {
    const angle = i * 2.399963;
    const radius = 12 + ((i * 37) % 88);
    const x = 128 + Math.cos(angle) * radius * 0.55;
    const y = 128 + Math.sin(angle) * radius * 0.55;
    const rx = 5 + ((i * 11) % 22);
    const ry = 2 + ((i * 7) % 9);
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle + Math.sin(i * 1.7) * 0.5);
    const wisp = ctx.createLinearGradient(-rx * 2, 0, rx * 2, 0);
    wisp.addColorStop(0, 'rgba(255,255,255,0)');
    wisp.addColorStop(0.5, 'rgba(255,255,255,0.3)');
    wisp.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = wisp;
    ctx.beginPath();
    ctx.ellipse(0, 0, rx * 2, ry, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
}
const cloudTexture = createProceduralCloudTexture();

// Create galaxy simulation with preloaded texture
const galaxySimulation = new GalaxySimulation(scene, config, cloudTexture);
galaxySimulation.createGalaxySystem();
galaxySimulation.createClouds();

// Create starry background
createStarryBackground(scene);

// Setup bloom
function setupBloom() {
  if (!postProcessing) return;

  const scenePass = pass(scene, camera);
  const scenePassColor = scenePass.getTextureNode();

  bloomPassNode = bloom(scenePassColor);
  bloomPassNode.threshold.value = config.bloomThreshold;
  bloomPassNode.strength.value = config.bloomStrength;
  bloomPassNode.radius.value = config.bloomRadius;

  postProcessing.outputNode = scenePassColor.add(bloomPassNode);
}

// Create UI with callbacks
const ui = new GalaxyUI(config, {
  onUniformChange: (key, value) => galaxySimulation.updateUniforms({ [key]: value }),

  onBloomChange: (property, value) => {
    if (bloomPassNode) bloomPassNode[property].value = value;
  },

  onStarCountChange: (newCount) => {
    galaxySimulation.updateStarCount(newCount);
    document.getElementById('star-count').textContent = newCount.toLocaleString();
  },

  onCloudCountChange: (newCount) => {
    galaxySimulation.updateUniforms({ cloudCount: newCount });
    galaxySimulation.createClouds();
  },

  onCloudTintChange: (color) => {
    galaxySimulation.updateUniforms({ cloudTintColor: color });
    galaxySimulation.createClouds();
  },

  onRegenerate: () => {
    galaxySimulation.updateUniforms(config);
    galaxySimulation.createClouds();
    galaxySimulation.regenerate();
  }
});

// FPS counter
let frameCount = 0;
let lastTime = performance.now();
let fps = 60;

function updateFPS() {
  frameCount++;
  const currentTime = performance.now();
  const deltaTime = currentTime - lastTime;

  if (deltaTime >= 1000) {
    fps = Math.round((frameCount * 1000) / deltaTime);
    frameCount = 0;
    lastTime = currentTime;

    document.getElementById('fps').textContent = fps;
    ui.updateFPS(fps);
  }
}

// Animation loop
let lastFrameTime = performance.now();

async function animate() {
  requestAnimationFrame(animate);

  const currentTime = performance.now();
  const deltaTime = Math.min((currentTime - lastFrameTime) / 1000, 0.033);
  lastFrameTime = currentTime;

  // Update controls
  controls.update();

  // Update galaxy
  await galaxySimulation.update(renderer, deltaTime, mouse3D, mousePressed);

  // Render
  if (postProcessing) {
    postProcessing.render();
  } else {
    renderer.render(scene, camera);
  }

  updateFPS();
}

// Handle resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// Initialize
renderer.init().then(() => {
  postProcessing = new THREE.PostProcessing(renderer);
  setupBloom();
  ui.setBloomNode(bloomPassNode);
  const status = document.getElementById('status');
  if (status) status.textContent = 'GPU simulation active · drag the galaxy to interact';

  document.getElementById('star-count').textContent = config.starCount.toLocaleString();
  animate();
}).catch(err => {
  console.error('Failed to initialize renderer:', err);
  const status = document.getElementById('status');
  if (status) status.textContent = 'WebGPU is unavailable on this browser/device. Open this page in a current Chrome or Edge browser with WebGPU support.';
});

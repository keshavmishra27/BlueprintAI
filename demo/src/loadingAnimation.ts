import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

let overlayDiv: HTMLElement | null = null;
let isInitialized = false;

// Variables needed for animation loop
let animateFunc: () => void;

function initThreeJs() {
    if (isInitialized) return;
    isInitialized = true;

    // Create the overlay container
    overlayDiv = document.createElement('div');
    overlayDiv.id = 'loading-overlay';
    Object.assign(overlayDiv.style, {
        position: 'fixed',
        top: '0', left: '0', width: '100vw', height: '100vh',
        backgroundColor: '#000',
        zIndex: '9999',
        opacity: '0',
        pointerEvents: 'none',
        transition: 'opacity 0.4s ease'
    });
    document.body.appendChild(overlayDiv);

    // Add a text label over the animation
    const textLabel = document.createElement('div');
    Object.assign(textLabel.style, {
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        color: '#ffffff',
        fontFamily: "'Inter', sans-serif",
        fontSize: '24px',
        fontWeight: '800',
        letterSpacing: '2px',
        zIndex: '10',
        textShadow: '0 0 20px rgba(0, 255, 204, 0.8)'
    });
    textLabel.textContent = 'LOADING';
    overlayDiv.appendChild(textLabel);

    // CONFIG from user request
    const SPEED_MULT = 1;
    const AUTO_SPIN = true;

    // SETUP
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.01);
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
    camera.position.set(0, 0, 100);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    renderer.setSize(window.innerWidth, window.innerHeight);
    overlayDiv.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = AUTO_SPIN;
    controls.autoRotateSpeed = 2.0;

    // POST PROCESSING
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
    bloomPass.strength = 1.8; bloomPass.radius = 0.4; bloomPass.threshold = 0;
    composer.addPass(bloomPass);

    // LOAD SWORD MODEL
    const loader = new GLTFLoader();
    let swordModel: THREE.Group | null = null;
    let mixer: THREE.AnimationMixer | null = null;
    
    loader.load(import.meta.env.BASE_URL + 'shattered_crystal_sword.glb', (gltf) => {
        const model = gltf.scene;
        
        // Center the model
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 40 / maxDim; // scale to fit nicely in the view (camera is at z=100)
        
        model.scale.set(scale, scale, scale);
        model.position.set(-center.x * scale, -center.y * scale, -center.z * scale);
        
        const group = new THREE.Group();
        group.add(model);
        scene.add(group);
        
        swordModel = group;

        if (gltf.animations && gltf.animations.length > 0) {
            mixer = new THREE.AnimationMixer(model);
            gltf.animations.forEach((clip) => mixer!.clipAction(clip).play());
        }
    });

    // ANIMATION LOOP
    const clock = new THREE.Clock();
    
    animateFunc = function animate() {
        requestAnimationFrame(animateFunc);
        
        // Only render if overlay is visible (optimization)
        if (overlayDiv && overlayDiv.style.opacity === '0') return;

        const delta = clock.getDelta();
        const time = clock.getElapsedTime() * SPEED_MULT;

        if (mixer) mixer.update(delta);
        if (swordModel) {
            swordModel.rotation.y += delta * 0.5; // Add some slow spinning
            swordModel.rotation.x = Math.sin(time * 0.5) * 0.2; // Gentle hover effect
            swordModel.position.y = Math.sin(time) * 2;
        }
        
        controls.update();

        composer.render();
    };
    
    // Start animation loop
    animateFunc();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
        composer.setSize(window.innerWidth, window.innerHeight);
    });
}

export function showLoadingScreen(): Promise<void> {
    return new Promise(resolve => {
        initThreeJs();
        if (overlayDiv) {
            overlayDiv.style.pointerEvents = 'all';
            overlayDiv.style.opacity = '1';
        }
        // Force minimum 1.2s delay to show the animation during fast local routing
        setTimeout(() => resolve(), 1200); 
    });
}

export function hideLoadingScreen() {
    if (overlayDiv) {
        overlayDiv.style.opacity = '0';
        setTimeout(() => {
            if (overlayDiv) overlayDiv.style.pointerEvents = 'none';
        }, 400); // Wait for transition
    }
}

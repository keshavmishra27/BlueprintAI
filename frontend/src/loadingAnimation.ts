import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
let overlayDiv: HTMLElement | null = null;
let isInitialized = false;
let animateFunc: () => void;
function initThreeJs() {
    if (isInitialized) return;
    isInitialized = true;
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
    const COUNT = 20000;
    const SPEED_MULT = 1;
    const AUTO_SPIN = true;
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
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
    bloomPass.strength = 1.8; bloomPass.radius = 0.4; bloomPass.threshold = 0;
    composer.addPass(bloomPass);
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    const target = new THREE.Vector3();
    const geometry = new THREE.TetrahedronGeometry(0.25);
    const material = new THREE.MeshBasicMaterial({ color: 0xffffff });
    (material as any).uniforms = { uTime: { value: 0 } };
    const instancedMesh = new THREE.InstancedMesh(geometry, material, COUNT);
    instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    scene.add(instancedMesh);
    const positions: THREE.Vector3[] = [];
    for(let i = 0; i < COUNT; i++) {
        positions.push(new THREE.Vector3((Math.random()-0.5)*100, (Math.random()-0.5)*100, (Math.random()-0.5)*100));
        instancedMesh.setColorAt(i, color.setHex(0x00ff88)); 
    }
    const PARAMS: Record<string, number> = {"speed":1,"spread":60,"chaos":0.15};
    const addControl = (id: string, _label: string, _min: number, _max: number, val: number) => {
        return PARAMS[id] !== undefined ? PARAMS[id] : val;
    };
    const setInfo = () => {};
    const clock = new THREE.Clock();
    animateFunc = function animate() {
        requestAnimationFrame(animateFunc);
        if (overlayDiv && overlayDiv.style.opacity === '0') return;
        const time = clock.getElapsedTime() * SPEED_MULT;
        if((material as any).uniforms && (material as any).uniforms.uTime) {
            (material as any).uniforms.uTime.value = time;
        }
        controls.update();
        const count = COUNT; 
        for(let i = 0; i < COUNT; i++) {
            const speed = addControl("speed", "Rotation Speed", 0.1, 3, 1);
            const spread = addControl("spread", "Spread", 20, 150, 60);
            const chaos = addControl("chaos", "Chaos", 0, 1, 0.15);
            const t = time * speed;
            const phi = (i / count) * Math.PI * 2;
            const layer = Math.floor(i / (count / 5));
            const radius = spread * (0.4 + 0.15 * layer);
            const tilt = (layer * Math.PI) / 5 + t * 0.3;
            const x = Math.cos(phi + t + layer) * radius + Math.sin(tilt) * chaos * 20;
            const y = Math.sin(phi + t + layer) * radius * Math.cos(tilt) + Math.sin(time * 0.7 + i * 0.01) * chaos * 15;
            const z = Math.sin(phi * 2 + t) * radius * 0.5 + layer * 8 * Math.sin(t * 0.2);
            target.set(x, y, z);
            const hue = (i / count + time * 0.05) % 1;
            const sat = 0.7 + 0.3 * Math.sin(phi + time);
            color.setHSL(hue * 0.25 + 0.5, sat, 0.6 + 0.2 * Math.sin(phi));
            if (i === 0) setInfo();
            positions[i].lerp(target, 0.1);
            dummy.position.copy(positions[i]);
            dummy.updateMatrix();
            instancedMesh.setMatrixAt(i, dummy.matrix);
            instancedMesh.setColorAt(i, color);
        }
        instancedMesh.instanceMatrix.needsUpdate = true;
        if(instancedMesh.instanceColor) instancedMesh.instanceColor.needsUpdate = true;
        composer.render();
    };
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
        setTimeout(() => resolve(), 1200); 
    });
}
export function hideLoadingScreen() {
    if (overlayDiv) {
        overlayDiv.style.opacity = '0';
        setTimeout(() => {
            if (overlayDiv) overlayDiv.style.pointerEvents = 'none';
        }, 400); 
    }
}

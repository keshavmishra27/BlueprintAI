import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';

export function initBackgroundAnimation() {
    // CONFIG
    const COUNT = 20000;
    const SPEED_MULT = 1;
    const AUTO_SPIN = true;

    // SETUP
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.01);
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
    camera.position.set(0, 0, 100);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance", alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 1);
    
    // Style the canvas to sit in the background
    renderer.domElement.style.position = 'fixed';
    renderer.domElement.style.top = '0';
    renderer.domElement.style.left = '0';
    renderer.domElement.style.zIndex = '-5';
    renderer.domElement.style.pointerEvents = 'none'; // So it doesn't block UI interactions
    document.body.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = AUTO_SPIN;
    controls.autoRotateSpeed = 2.0;

    // POST PROCESSING
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
    bloomPass.strength = 1.8; 
    bloomPass.radius = 0.4; 
    bloomPass.threshold = 0;
    composer.addPass(bloomPass);

    // SWARM OBJECTS
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    const target = new THREE.Vector3();
    
    // INSTANCED MESH
    const geometry = new THREE.TetrahedronGeometry(0.25);
    const material = new THREE.MeshBasicMaterial({ color: 0xffffff });
    (material as any).uniforms = { uTime: { value: 0 } };
    
    const instancedMesh = new THREE.InstancedMesh(geometry, material, COUNT);
    instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    scene.add(instancedMesh);

    // DATA ARRAYS
    const positions: THREE.Vector3[] = [];
    for(let i=0; i<COUNT; i++) {
        positions.push(new THREE.Vector3((Math.random()-0.5)*100, (Math.random()-0.5)*100, (Math.random()-0.5)*100));
        instancedMesh.setColorAt(i, color.setHex(0x00ff88)); // Init Color
    }

    // CONTROL STUBS
    const PARAMS: Record<string, number> = {"speed":0.85,"intensity":0.45,"depth":95,"focus":0.9,"spread":34};
    const addControl = (id: string, _label: string, _min: number, _max: number, val: number) => {
        return PARAMS[id] !== undefined ? PARAMS[id] : val;
    };
    const setInfo = (title?: string, desc?: string) => {};

    // ANIMATION LOOP
    const clock = new THREE.Clock();
    
    function animate() {
        requestAnimationFrame(animate);
        const time = clock.getElapsedTime() * SPEED_MULT;
        
        // Shader Time Update
        if((material as any).uniforms && (material as any).uniforms.uTime) {
            (material as any).uniforms.uTime.value = time;
        }

        controls.update();

        // SWARM LOGIC
        const count = COUNT; // Alias for user code compatibility
        for(let i=0; i<COUNT; i++) {
             // USER CODE INJECTION START
             const speed = addControl("speed", "Flow Speed", 0.05, 3.0, 0.85);
             const intensity = addControl("intensity", "Intensity", 0.0, 1.0, 0.45);
             const depth = addControl("depth", "Depth", 20, 180, 95);
             const focus = addControl("focus", "Focus Core", 0.1, 2.0, 0.9);
             const spread = addControl("spread", "Energy Spread", 5, 80, 34);
             
             const n = count > 1 ? i / (count - 1) : 0;
             const g = i * 2.399963229728653;
             const t = time * speed;
             
             const band = n * 18.0;
             const pulse = 0.5 + 0.5 * Math.sin(t * 1.35 - n * 12.0);
             const breath = 0.86 + 0.14 * Math.sin(t * 0.72);
             
             const lane = Math.sin(g * 0.618 + t * 0.32);
             const twist = g + t * (0.22 + intensity * 0.55) + Math.sin(band + t) * 0.35;
             
             const core = Math.pow(Math.abs(lane), focus);
             const r = (spread * (0.2 + core * 1.35)) * breath;
             
             const waveA = Math.sin(band * 1.7 - t * 2.2);
             const waveB = Math.cos(band * 0.9 + t * 1.4);
             
             const x = Math.cos(twist) * r + waveA * intensity * 9.0;
             const y = Math.sin(twist) * r * 0.42 + waveB * intensity * 7.0;
             const z = (n - 0.5) * depth + Math.sin(t * 1.1 + n * 24.0) * intensity * 18.0;
             
             target.set(x, y, z);
             
             const heat = 0.56 + pulse * 0.08 + intensity * 0.03;
             const sat = 0.58 + intensity * 0.32;
             const light = 0.18 + pulse * 0.25 + core * 0.12;
             
             color.setHSL(heat, sat, light);
             
             if (i === 0) {
               setInfo("VEXIS Flow State Energy", "Controlled particle momentum: calm intensity, directional focus, and cinematic mental energy before execution.");
             }
             // USER CODE INJECTION END

             // LERP & UPDATE
             positions[i].lerp(target, 0.1);
             dummy.position.copy(positions[i]);
             dummy.updateMatrix();
             instancedMesh.setMatrixAt(i, dummy.matrix);
             instancedMesh.setColorAt(i, color); // Fix: Use 'color' which user modifies
        }
        instancedMesh.instanceMatrix.needsUpdate = true;
        if(instancedMesh.instanceColor) instancedMesh.instanceColor.needsUpdate = true;

        composer.render();
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
        composer.setSize(window.innerWidth, window.innerHeight);
    });
}

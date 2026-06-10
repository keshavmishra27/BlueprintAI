import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';

let isInitialized = false;

export function initBackgroundAnimation() {
    if (isInitialized) return;
    isInitialized = true;

    // Create the background container
    const bgDiv = document.createElement('div');
    bgDiv.id = 'background-animation';
    Object.assign(bgDiv.style, {
        position: 'fixed',
        top: '0', left: '0', width: '100vw', height: '100vh',
        zIndex: '-2', // Behind the CSS mesh grid which should be -1
        pointerEvents: 'none', // Don't block clicks
        opacity: '0.8' // Slightly transparent so it blends well
    });
    document.body.appendChild(bgDiv);

    // CONFIG
    const COUNT = 20000;
    const SPEED_MULT = 1;

    // SETUP
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.01);
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
    camera.position.set(0, 0, 100);
    
    // Set alpha to true to allow transparent background
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance", alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0); // Transparent clear color
    bgDiv.appendChild(renderer.domElement);

    // POST PROCESSING
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
    bloomPass.strength = 1.8; bloomPass.radius = 0.4; bloomPass.threshold = 0;
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
    const PARAMS: Record<string, number> = {"gravity":4,"swirl":3.5,"disk":80,"warp":2,"jets":1.5};
    const addControl = (id: string, _label: string, _min: number, _max: number, val: number) => {
        return PARAMS[id] !== undefined ? PARAMS[id] : val;
    };

    // ANIMATION LOOP
    const clock = new THREE.Clock();
    
    function animate() {
        requestAnimationFrame(animate);
        const time = clock.getElapsedTime() * SPEED_MULT;
        
        // Shader Time Update
        if((material as any).uniforms && (material as any).uniforms.uTime) {
            (material as any).uniforms.uTime.value = time;
        }

        // SWARM LOGIC
        const count = COUNT;
        for(let i=0; i<COUNT; i++) {
             const gravity = addControl("gravity", "Gravity Strength", 0.1, 10.0, 4.0);
             const swirl = addControl("swirl", "Frame Dragging", 0.0, 8.0, 3.5);
             const disk = addControl("disk", "Accretion Disk Radius", 20.0, 200.0, 80.0);
             const warp = addControl("warp", "Space Warp", 0.0, 5.0, 2.0);
             const jets = addControl("jets", "Relativistic Jets", 0.0, 5.0, 1.5);
             
             const fi = i / count;
             const golden = 2.399963229728653;
             const spiral = fi * 300.0;
             
             const baseAngle = i * golden;
             const timeWarp = time * (0.15 + gravity * 0.05);
             
             const radialNoise = Math.sin(i * 0.013 + time * 0.7) * 8.0;
             const radius = disk + spiral * 0.18 + radialNoise;
             
             const collapse = 1.0 / (1.0 + fi * gravity * 0.7);
             
             const angle = baseAngle + timeWarp + (1.0 / (radius * 0.03 + 0.2)) * swirl;
             
             let x = Math.cos(angle) * radius * collapse;
             let z = Math.sin(angle) * radius * collapse;
             
             const diskWave = Math.sin(radius * 0.08 - time * 2.0) * 3.0;
             let y = diskWave * Math.exp(-radius * 0.008);
             
             const singularityDist = Math.sqrt(x * x + y * y + z * z) + 0.0001;
             
             const lens = warp / (singularityDist * 0.08 + 1.0);
             
             x *= 1.0 + lens;
             z *= 1.0 + lens;
             
             const pull = gravity / (singularityDist * 0.15 + 1.0);
             
             x -= x * pull * 0.015;
             y -= y * pull * 0.015;
             z -= z * pull * 0.015;
             
             const jetMask = Math.abs(Math.sin(fi * 90.0 + time * 0.5));
             const jetStrength = jets * Math.pow(jetMask, 18.0);
             
             y += (fi - 0.5) * 900.0 * jetStrength;
             
             const photonRing = Math.exp(-Math.abs(singularityDist - 18.0) * 0.08);
             
             x += Math.cos(angle * 4.0 + time * 3.0) * photonRing * 6.0;
             z += Math.sin(angle * 4.0 + time * 3.0) * photonRing * 6.0;
             
             target.set(x, y, z);
             
             const hueShift = 0.58 + 0.25 * Math.sin(radius * 0.01 - time * 0.2);
             const saturation = 0.8 - collapse * 0.3;
             const brightness =
                 0.15 +
                 photonRing * 0.9 +
                 jetStrength * 0.8 +
                 Math.exp(-singularityDist * 0.01) * 0.5;
             
             color.setHSL(
                 hueShift,
                 saturation,
                 Math.min(1.0, brightness)
             );

             // LERP & UPDATE
             positions[i].lerp(target, 0.1);
             dummy.position.copy(positions[i]);
             dummy.updateMatrix();
             instancedMesh.setMatrixAt(i, dummy.matrix);
             instancedMesh.setColorAt(i, color); 
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

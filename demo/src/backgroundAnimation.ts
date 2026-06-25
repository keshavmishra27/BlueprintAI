import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export function initBackgroundAnimation() {
    // SETUP
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.02);

    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
    // Typical isometric viewing angle
    camera.position.set(10, 10, 10);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Style the canvas to sit in the background
    renderer.domElement.style.position = 'fixed';
    renderer.domElement.style.top = '0';
    renderer.domElement.style.left = '0';
    renderer.domElement.style.zIndex = '-5';
    renderer.domElement.style.pointerEvents = 'none'; // So it doesn't block UI interactions
    renderer.domElement.style.transition = 'opacity 0.5s ease';
    document.body.appendChild(renderer.domElement);

    // LIGHTING
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
    dirLight.position.set(10, 20, 10);
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0x00ff88, 2, 50);
    pointLight.position.set(0, 5, 0);
    scene.add(pointLight);

    // CONTROLS
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 1.0;
    controls.enableZoom = false;
    controls.enablePan = false;

    // LOAD GLTF
    const loader = new GLTFLoader();
    const mixers: THREE.AnimationMixer[] = [];
    let homeModel: THREE.Group | null = null;
    let otherModel: THREE.Group | null = null;
    let assessmentModel: THREE.Group | null = null;
    let projectModel: THREE.Group | null = null;

    // Helper to process loaded models
    const processModel = (gltf: any, targetScale: number, yOffset: number = 0) => {
        const model = gltf.scene;

        // Center the model
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = targetScale / maxDim; // scale to fit nicely

        model.scale.set(scale, scale, scale);
        // Center it, and optionally apply a Y offset (e.g. to move the floor to 0)
        model.position.set(-center.x * scale, (-center.y * scale) + yOffset, -center.z * scale);

        // Wrap in a group so we can scale the group without messing up the centering
        const group = new THREE.Group();
        group.add(model);

        // Play animation if available
        if (gltf.animations && gltf.animations.length > 0) {
            const mixer = new THREE.AnimationMixer(model);
            gltf.animations.forEach((clip: any) => {
                mixer.clipAction(clip).play();
            });
            mixers.push(mixer);
        }
        return group;
    };

    // Load Home Model
    loader.load(
        import.meta.env.BASE_URL + 'fnaf_sb_endo_blueprint.glb',
        (gltf) => {
            homeModel = processModel(gltf, 15, 0);
            scene.add(homeModel);
            updateVisibility();
        },
        undefined,
        (error) => console.error('Error loading home GLTF:', error)
    );

    // Load Other Pages Model (Temple)
    loader.load(
        import.meta.env.BASE_URL + 'temple_usd_workflow_test.glb',
        (gltf) => {
            // Scale it much larger so we can easily fit the camera inside
            otherModel = processModel(gltf, 80, 0);
            scene.add(otherModel);
            updateVisibility();
        },
        undefined,
        (error) => console.error('Error loading temple GLTF:', error)
    );

    // Load Assessment Model
    loader.load(
        import.meta.env.BASE_URL + 'assessment_two_-_aie_-_sci_fi_ship_interior.glb',
        (gltf) => {
            assessmentModel = processModel(gltf, 80, 0);
            scene.add(assessmentModel);
            updateVisibility();
        },
        undefined,
        (error) => console.error('Error loading assessment GLTF:', error)
    );

    // Load Project Idea / Refiner Model
    loader.load(
        import.meta.env.BASE_URL + 'rigged_sci-fi_lift_-_mobile_platform_-_elevator.glb',
        (gltf) => {
            projectModel = processModel(gltf, 60, 0);
            scene.add(projectModel);
            updateVisibility();
        },
        undefined,
        (error) => console.error('Error loading project GLTF:', error)
    );

    // HANDLE ROUTE CHANGES TO TOGGLE MODELS AND CAMERA
    function updateVisibility() {
        const hash = window.location.hash;
        const isHome = hash === '#/' || hash === '';
        const isAssessment = hash === '#/assessment';
        const isProject = hash === '#/project-suggest' || hash === '#/idea-refiner';

        if (homeModel) homeModel.visible = isHome;
        if (assessmentModel) assessmentModel.visible = isAssessment;
        if (projectModel) projectModel.visible = isProject;
        if (otherModel) otherModel.visible = !isHome && !isAssessment && !isProject;

        if (isHome) {
            // Isometric view from outside
            camera.position.set(10, 10, 10);
            controls.target.set(0, 0, 0);
            controls.autoRotateSpeed = 1.0;
        } else if (isAssessment) {
            camera.position.set(0, -5, 10);
            controls.target.set(0, -5, 0);
            controls.autoRotateSpeed = 0.4;
        } else if (isProject) {
            camera.position.set(0, 15, 30);
            controls.target.set(0, 0, 0);
            controls.autoRotateSpeed = 0.6;
        } else {
            // Inside view for the temple
            // Placed near the "floor" and looking towards the center pillars
            camera.position.set(0, -10, 20);
            controls.target.set(0, -10, 0);
            controls.autoRotateSpeed = 0.4; // Slower, more majestic rotation
        }

        renderer.domElement.style.opacity = '1'; // Always visible now
    }
    window.addEventListener('hashchange', updateVisibility);
    updateVisibility(); // Initial check

    // SCROLL EXPANSION LOGIC
    let targetZoom = 1;
    let currentZoom = 1;

    window.addEventListener('scroll', () => {
        // Increase zoom as user scrolls down to make scenes "expand"
        targetZoom = 1 + (window.scrollY * 0.0015);
    });

    // ANIMATION LOOP
    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();

        mixers.forEach(mixer => mixer.update(delta));

        // Smoothly interpolate zoom for the camera
        currentZoom += (targetZoom - currentZoom) * 0.1;
        if (Math.abs(camera.zoom - currentZoom) > 0.001) {
            camera.zoom = currentZoom;
            camera.updateProjectionMatrix();
        }

        controls.update();
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

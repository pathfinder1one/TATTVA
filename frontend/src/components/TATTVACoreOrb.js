'use client';

/**
 * TATTVACoreOrb — EXACT replica of the ARGON geodesic AI visualization
 * Ported from the user's original Three.js code to React Three Fiber.
 * 
 * ALL layers, ALL geometry, ALL density preserved:
 * - 8 Swooping Plasma Ribbons
 * - Icosahedron(0.68, 2) outer geodesic wireframe + vertex nodes
 * - Icosahedron(0.42, 1) inner counter-rotating kernel
 * - 110 Multi-Lane PCB Buses + 42 Circuit Wings
 * - 1300-node Neural Cortex + 95 Bezier Synaptic Filaments
 * - 22 Hexagonal Security Patches + 12 Radar Ladders
 * - 6 Gyroscopic Telemetry Tick Rings
 * - Real-time Radar Pulse Color Updater
 */

import { useRef, useMemo, useEffect, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import * as THREE from 'three';
import { useTheme } from './ThemeProvider';

/* ============================================================
   UTILITY
   ============================================================ */
function sphToCart(r, theta, phi) {
  return new THREE.Vector3(
    r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta)
  );
}

function createGlowTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');
  const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0.0, 'rgba(255,255,255,1.0)');
  grad.addColorStop(0.24, 'rgba(255,255,255,0.85)');
  grad.addColorStop(0.52, 'rgba(255,255,255,0.24)');
  grad.addColorStop(1.0, 'rgba(0,0,0,0.0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(canvas);
}

/* ============================================================
   buildConnectedLayer — Exact replica of the original helper.
   Builds a LineSegments + Points group from segment/node arrays,
   storing tier data for the per-vertex radar pulse color updater.
   ============================================================ */
function buildConnectedLayer(segmentPairs, nodeVertices, pointSize, lineOpacity, ptOpacity) {
  const linePos = new Float32Array(segmentPairs.length * 3);
  const lineCol = new Float32Array(segmentPairs.length * 3);
  const lineTiers = new Uint8Array(segmentPairs.length);

  for (let i = 0; i < segmentPairs.length; i++) {
    linePos[i * 3]     = segmentPairs[i].v.x;
    linePos[i * 3 + 1] = segmentPairs[i].v.y;
    linePos[i * 3 + 2] = segmentPairs[i].v.z;
    lineTiers[i]       = segmentPairs[i].tier;
  }

  const lineGeo = new THREE.BufferGeometry();
  lineGeo.setAttribute('position', new THREE.BufferAttribute(linePos, 3));
  lineGeo.setAttribute('color', new THREE.BufferAttribute(lineCol, 3));

  const ptPos = new Float32Array(nodeVertices.length * 3);
  const ptCol = new Float32Array(nodeVertices.length * 3);
  const ptTiers = new Uint8Array(nodeVertices.length);

  for (let i = 0; i < nodeVertices.length; i++) {
    ptPos[i * 3]     = nodeVertices[i].v.x;
    ptPos[i * 3 + 1] = nodeVertices[i].v.y;
    ptPos[i * 3 + 2] = nodeVertices[i].v.z;
    ptTiers[i]       = nodeVertices[i].tier;
  }

  const ptGeo = new THREE.BufferGeometry();
  ptGeo.setAttribute('position', new THREE.BufferAttribute(ptPos, 3));
  ptGeo.setAttribute('color', new THREE.BufferAttribute(ptCol, 3));

  return {
    lineGeo, lineTiers, lineCount: segmentPairs.length, lineOpacity,
    ptGeo, ptTiers, ptCount: nodeVertices.length, pointSize, ptOpacity,
  };
}

/* ============================================================
   CORE GROUP: 8 Plasma Ribbons + Icosahedron(0.68,2) + Icosahedron(0.42,1)
   ============================================================ */
function CoreGroup({ colors, mode = 'idle', onCoreClick, audioLevel = 0 }) {
  const coreGroupRef = useRef();
  const outerMeshRef = useRef();
  const outerPtsRef = useRef();
  const innerRef = useRef();
  const ribbonRefs = useRef([]);

  const nodeTexture = useMemo(() => createGlowTexture(), []);

  // 8 Swooping Plasma Ribbons (EXACT from original code)
  const ribbons = useMemo(() => {
    const result = [];
    for (let r = 0; r < 8; r++) {
      const curvePts = [];
      const baseRadius = 0.78 + (r % 4) * 0.36;
      for (let i = 0; i <= 36; i++) {
        const t = (i / 36) * Math.PI * 1.68;
        const wave = Math.sin(t * 3 + r) * 0.24;
        curvePts.push(new THREE.Vector3(
          Math.cos(t) * (baseRadius + wave),
          Math.sin(t * 2) * 0.44,
          Math.sin(t) * (baseRadius + wave)
        ));
      }
      const curve = new THREE.CatmullRomCurve3(curvePts);
      const tubeGeo = new THREE.TubeGeometry(curve, 64, r < 3 ? 0.028 : 0.016, 6, false);
      result.push({
        geometry: tubeGeo,
        rotation: [r * 0.8, r * 1.1, r * 0.5],
        isCore: r < 5,
      });
    }
    return result;
  }, []);

  // Icosahedron(0.68, 2) — outer geodesic wireframe
  const outerGeo = useMemo(() => new THREE.IcosahedronGeometry(0.68, 2), []);
  const outerWire = useMemo(() => new THREE.WireframeGeometry(outerGeo), [outerGeo]);

  // Vertex nodes on the outer geodesic
  const kernelNodeGeo = useMemo(() => {
    const attr = outerGeo.attributes.position;
    const pts = [];
    for (let i = 0; i < attr.count; i++) {
      pts.push(new THREE.Vector3().fromBufferAttribute(attr, i));
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }, [outerGeo]);

  // Icosahedron(0.42, 1) — inner kernel
  const innerGeo = useMemo(() => new THREE.IcosahedronGeometry(0.42, 1), []);
  const innerWire = useMemo(() => new THREE.WireframeGeometry(innerGeo), [innerGeo]);

  // Mode-dependent animation speeds & scales
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();

    // Rotation speeds adapt based on mode
    let speedMult = 1.0;
    if (mode === 'analyzing') speedMult = 2.4;
    else if (mode === 'listening') speedMult = 1.4;
    else if (mode === 'speaking') speedMult = 1.2;

    // Rotate the core group (ribbons + outer sphere)
    if (coreGroupRef.current) {
      coreGroupRef.current.rotation.y = t * 0.65 * speedMult;
      coreGroupRef.current.rotation.x = Math.sin(t * 0.5 * speedMult) * 0.42;
    }

    // Counter-rotate inner kernel
    if (innerRef.current) {
      innerRef.current.rotation.y = -t * 1.2 * speedMult;
      innerRef.current.rotation.z = t * 0.8 * speedMult;
    }

    // Dynamic breathing pulse based on mode & audioLevel
    let s = 1.0;
    if (mode === 'listening') {
      s = 1.0 + Math.sin(t * 8.0) * 0.12;
    } else if (mode === 'speaking') {
      s = 1.0 + Math.sin(t * 10.0) * 0.08 + (audioLevel || 0.15) * 0.22;
    } else if (mode === 'analyzing') {
      s = 1.0 + Math.sin(t * 14.0) * 0.09;
    } else {
      s = 1.0 + Math.sin(t * 4.0) * 0.06;
    }

    if (outerMeshRef.current) outerMeshRef.current.scale.set(s, s, s);
    if (outerPtsRef.current) outerPtsRef.current.scale.set(s, s, s);
  });

  // Update material colors when theme changes
  const coreColor = useMemo(() => new THREE.Color(colors.core), [colors.core]);
  const brightColor = useMemo(() => new THREE.Color(colors.bright), [colors.bright]);

  return (
    <group ref={coreGroupRef}>
      {/* Clickable hit sphere */}
      <mesh
        onClick={(e) => {
          e.stopPropagation();
          onCoreClick?.();
        }}
        visible={false}
      >
        <sphereGeometry args={[2.8, 16, 16]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
      {/* 8 Plasma Ribbons */}
      {ribbons.map((rb, i) => (
        <mesh key={`ribbon-${i}`} geometry={rb.geometry} rotation={rb.rotation}
          ref={el => { ribbonRefs.current[i] = el; }}>
          <meshBasicMaterial
            color={rb.isCore ? coreColor : brightColor}
            transparent opacity={0.72}
            blending={THREE.AdditiveBlending} depthWrite={false}
          />
        </mesh>
      ))}

      {/* Outer Geodesic Wireframe */}
      <lineSegments ref={outerMeshRef} geometry={outerWire}>
        <lineBasicMaterial
          color={coreColor} transparent opacity={0.82}
          blending={THREE.AdditiveBlending} depthWrite={false}
        />
      </lineSegments>

      {/* Vertex Nodes */}
      <points ref={outerPtsRef} geometry={kernelNodeGeo}>
        <pointsMaterial
          size={0.11} map={nodeTexture} color={coreColor}
          transparent opacity={0.85}
          blending={THREE.AdditiveBlending} depthWrite={false}
        />
      </points>

      {/* Inner Counter-Rotating Kernel */}
      <lineSegments ref={innerRef} geometry={innerWire}>
        <lineBasicMaterial
          color={brightColor} transparent opacity={0.75}
          blending={THREE.AdditiveBlending} depthWrite={false}
        />
      </lineSegments>
    </group>
  );
}

/* ============================================================
   DynamicLayer — renders LineSegments + Points from buildConnectedLayer
   output, with per-vertex radar pulse color updates each frame.
   ============================================================ */
function DynamicLayer({ layerData, rotationFn, getTierColor, coreColor, powerScale }) {
  const groupRef = useRef();
  const lineRef = useRef();
  const ptsRef = useRef();
  const nodeTexture = useMemo(() => createGlowTexture(), []);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();

    // Apply rotation
    if (groupRef.current && rotationFn) {
      rotationFn(groupRef.current, t);
    }

    // === RADAR PULSE COLOR UPDATER (EXACT from original code) ===
    const pulseRadius = (t * 2.8) % 8.5;
    const tempColor = new THREE.Color();

    // Lines
    if (lineRef.current) {
      const geo = lineRef.current.geometry;
      const lPos = geo.attributes.position.array;
      const lCol = geo.attributes.color.array;
      for (let i = 0; i < layerData.lineCount; i++) {
        const x = lPos[i * 3], y = lPos[i * 3 + 1], z = lPos[i * 3 + 2];
        const dist = Math.sqrt(x * x + y * y + z * z);
        const baseCol = getTierColor(layerData.lineTiers[i]);
        const coreGuard = dist < 1.6 ? 0.76 : 0.94;
        const waveProx = Math.max(0, 1 - Math.abs(dist - pulseRadius) * 1.4);
        tempColor.copy(baseCol).lerp(coreColor, waveProx * 0.55).multiplyScalar(coreGuard * powerScale);
        lCol[i * 3]     = tempColor.r;
        lCol[i * 3 + 1] = tempColor.g;
        lCol[i * 3 + 2] = tempColor.b;
      }
      geo.attributes.color.needsUpdate = true;
    }

    // Points
    if (ptsRef.current) {
      const geo = ptsRef.current.geometry;
      const pPos = geo.attributes.position.array;
      const pCol = geo.attributes.color.array;
      for (let i = 0; i < layerData.ptCount; i++) {
        const x = pPos[i * 3], y = pPos[i * 3 + 1], z = pPos[i * 3 + 2];
        const dist = Math.sqrt(x * x + y * y + z * z);
        const baseCol = getTierColor(layerData.ptTiers[i]);
        const coreGuard = dist < 1.6 ? 0.80 : 0.96;
        const waveProx = Math.max(0, 1 - Math.abs(dist - pulseRadius) * 1.4);
        tempColor.copy(baseCol).lerp(coreColor, waveProx * 0.70).multiplyScalar(coreGuard * powerScale);
        pCol[i * 3]     = tempColor.r;
        pCol[i * 3 + 1] = tempColor.g;
        pCol[i * 3 + 2] = tempColor.b;
      }
      geo.attributes.color.needsUpdate = true;
    }
  });

  return (
    <group ref={groupRef}>
      <lineSegments ref={lineRef} geometry={layerData.lineGeo}>
        <lineBasicMaterial
          vertexColors transparent opacity={layerData.lineOpacity}
          blending={THREE.AdditiveBlending} depthWrite={false}
        />
      </lineSegments>
      <points ref={ptsRef} geometry={layerData.ptGeo}>
        <pointsMaterial
          size={layerData.pointSize} map={nodeTexture} vertexColors
          transparent opacity={layerData.ptOpacity}
          blending={THREE.AdditiveBlending} depthWrite={false}
        />
      </points>
    </group>
  );
}

/* ============================================================
   LAYER BUILDERS — EXACT geometry from original code
   ============================================================ */

// Layer 1: 110 Multi-Lane PCB Buses + 42 Circuit Wings + Radial Spokes
function buildPCBLayer() {
  const pcbSegments = [];
  const pcbNodes = [];

  function addSegment(p1, p2, tier, includeEndNodes = true) {
    pcbSegments.push({ v: p1, tier }, { v: p2, tier });
    if (includeEndNodes) {
      pcbNodes.push({ v: p1, tier }, { v: p2, tier });
    }
  }

  // 110 Parallel Multi-Track Data Highways
  for (let b = 0; b < 110; b++) {
    let r = 2.1 + Math.pow(Math.random(), 1.05) * 3.6;
    let theta = Math.random() * Math.PI * 2;
    let phi = 0.22 + Math.random() * (Math.PI - 0.44);
    const lanes = b % 2 === 0 ? 3 : 2;
    const laneSpacing = 0.016;
    const baseTier = b % 3 === 0 ? 1 : (b % 3 === 1 ? 2 : 3);
    const steps = 5 + Math.floor(Math.random() * 6);

    for (let s = 0; s < steps; s++) {
      const moveType = Math.random();
      const dTheta = (Math.random() > 0.5 ? 1 : -1) * (0.10 + Math.random() * 0.22);
      const dPhi   = (Math.random() > 0.5 ? 1 : -1) * (0.08 + Math.random() * 0.16);
      const dR     = (Math.random() > 0.3 ? 1 : -1) * (0.45 + Math.random() * 0.95);

      for (let l = 0; l < lanes; l++) {
        const offset = (l - (lanes - 1) / 2) * laneSpacing;
        const lTier = l === 0 ? baseTier : 2;

        if (moveType < 0.50) {
          const subSteps = 6;
          for (let sub = 0; sub < subSteps; sub++) {
            const t1 = theta + (dTheta * sub) / subSteps;
            const t2 = theta + (dTheta * (sub + 1)) / subSteps;
            const p1 = sphToCart(r, t1, phi + offset);
            const p2 = sphToCart(r, t2, phi + offset);
            pcbSegments.push({ v: p1, tier: lTier }, { v: p2, tier: lTier });
            if (sub % 2 === 0 && l < lanes - 1) {
              const pCross = sphToCart(r, t1, phi + offset + laneSpacing);
              pcbSegments.push({ v: p1, tier: 2 }, { v: pCross, tier: 2 });
            }
          }
        } else if (moveType < 0.80) {
          const nextPhi = Math.max(0.18, Math.min(Math.PI - 0.18, phi + dPhi));
          const p1 = sphToCart(r, theta + offset, phi);
          const p2 = sphToCart(r, theta + offset, nextPhi);
          pcbSegments.push({ v: p1, tier: lTier }, { v: p2, tier: lTier });
        } else {
          const nextR = Math.max(1.6, Math.min(6.8, r + dR));
          const p1 = sphToCart(r, theta + offset * 0.5, phi);
          const p2 = sphToCart(nextR, theta + offset * 0.5, phi);
          pcbSegments.push({ v: p1, tier: 3 }, { v: p2, tier: 0 });
          pcbNodes.push({ v: p2, tier: 0 });
        }
      }

      if (moveType < 0.50) theta += dTheta;
      else if (moveType < 0.80) phi = Math.max(0.18, Math.min(Math.PI - 0.18, phi + dPhi));
      else r = Math.max(1.6, Math.min(6.8, r + dR));

      pcbNodes.push({ v: sphToCart(r, theta, phi), tier: s % 2 === 0 ? 0 : 3 });
    }
  }

  // 42 Circuit Wings
  for (let w = 0; w < 42; w++) {
    const biasBL = w < 22;
    const theta = biasBL ? (Math.PI * 0.75 + (Math.random() - 0.5) * 0.85) : Math.random() * Math.PI * 2;
    const phi   = biasBL ? (Math.PI * 0.62 + (Math.random() - 0.5) * 0.5) : (0.2 + Math.random() * (Math.PI - 0.4));
    const baseR = 4.4 + Math.random() * 1.1;
    const extR  = baseR + 0.75 + Math.random() * 1.4;
    const span  = 0.07 + Math.random() * 0.14;

    const p1 = sphToCart(baseR, theta, phi);
    const p2 = sphToCart(extR, theta, phi);
    const p3 = sphToCart(extR, theta + span, phi);
    const p4 = sphToCart(baseR, theta + span, phi);

    addSegment(p1, p2, 1);
    addSegment(p2, p3, 0);
    addSegment(p3, p4, 1);

    for (let k = 1; k < 4; k++) {
      const tMid = theta + span * (k / 4);
      const m1 = sphToCart(baseR + (extR - baseR) * 0.3, tMid, phi);
      const m2 = sphToCart(extR, tMid, phi);
      addSegment(m1, m2, 2);
    }
  }

  return buildConnectedLayer(pcbSegments, pcbNodes, 0.13, 0.54, 0.90);
}

// Layer 2: 1300-node Neural Cortex + 95 Bezier Synapses
function buildNeuralLayer() {
  const neuralSegments = [];
  const neuralNodes = [];
  const rawNeuralPts = [];

  const neuralCount = 1300;
  for (let i = 0; i < neuralCount; i++) {
    const r = 1.35 + Math.pow(Math.random(), 0.92) * 4.1;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const pt = sphToCart(r, theta, phi);
    const tier = r < 2.1 ? 3 : (Math.random() > 0.35 ? 1 : 2);
    rawNeuralPts.push({ v: pt, tier });
    neuralNodes.push({ v: pt, tier: r < 2.0 ? 0 : tier });
  }

  // Connect each node to 4 closest neighbors
  for (let i = 0; i < rawNeuralPts.length; i++) {
    const pA = rawNeuralPts[i];
    let connections = 0;
    for (let j = i + 1; j < rawNeuralPts.length; j++) {
      const pB = rawNeuralPts[j];
      const distSq = pA.v.distanceToSquared(pB.v);
      if (distSq < 0.74 && distSq > 0.02) {
        neuralSegments.push({ v: pA.v, tier: pA.tier }, { v: pB.v, tier: pB.tier });
        connections++;
        if (connections >= 4) break;
      }
    }
  }

  // 95 Curved Bezier Synaptic Filaments
  for (let c = 0; c < 95; c++) {
    const idxA = Math.floor(Math.random() * 400);
    const idxB = idxA + 10 + Math.floor(Math.random() * 80);
    if (idxB < rawNeuralPts.length) {
      const pA = rawNeuralPts[idxA].v;
      const pB = rawNeuralPts[idxB].v;
      if (pA.distanceTo(pB) < 2.8) {
        const mid = pA.clone().add(pB).multiplyScalar(0.55);
        const curve = new THREE.QuadraticBezierCurve3(pA, mid, pB);
        const cPts = curve.getPoints(8);
        for (let k = 0; k < cPts.length - 1; k++) {
          neuralSegments.push({ v: cPts[k], tier: 3 }, { v: cPts[k + 1], tier: 3 });
        }
      }
    }
  }

  return buildConnectedLayer(neuralSegments, neuralNodes, 0.13, 0.45, 0.92);
}

// Layer 3: 22 Hex Patches + 12 Radar Ladders + 6 Gyro Tick Rings
function buildHUDLayer() {
  const hudSegments = [];
  const hudNodes = [];

  // 22 Hexagonal Security Patches
  for (let p = 0; p < 22; p++) {
    const patchR = 2.9 + (p % 3) * 0.9;
    const cTheta = Math.random() * Math.PI * 2;
    const cPhi = 0.35 + Math.random() * (Math.PI - 0.7);
    const cPt = sphToCart(patchR, cTheta, cPhi);
    hudNodes.push({ v: cPt, tier: 0 });

    const hexPts = [];
    const hexRad = 0.10;
    for (let h = 0; h < 6; h++) {
      const ang = (h / 6) * Math.PI * 2;
      const hp = sphToCart(patchR, cTheta + Math.cos(ang) * hexRad, cPhi + Math.sin(ang) * hexRad);
      hexPts.push(hp);
      hudNodes.push({ v: hp, tier: 1 });
      hudSegments.push({ v: cPt, tier: 2 }, { v: hp, tier: 2 });
    }
    for (let h = 0; h < 6; h++) {
      hudSegments.push({ v: hexPts[h], tier: 1 }, { v: hexPts[(h + 1) % 6], tier: 1 });
    }
  }

  // 12 Radar Ladders
  for (let l = 0; l < 12; l++) {
    const ladderAngle = (l / 12) * Math.PI * 2;
    const phiStart = 0.35 + (l % 3) * 0.45;
    const phiSpan = 0.55;
    const rInner = 2.5 + (l % 2) * 1.1;
    const rOuter = rInner + 2.2;
    const widthAngle = 0.14;
    const rungs = 16;
    let prevLeft = null, prevRight = null;

    for (let k = 0; k <= rungs; k++) {
      const frac = k / rungs;
      const currR = rInner + (rOuter - rInner) * frac;
      const currPhi = phiStart + phiSpan * frac * 0.4;
      const leftPt  = sphToCart(currR, ladderAngle - widthAngle, currPhi);
      const rightPt = sphToCart(currR, ladderAngle + widthAngle, currPhi);

      hudSegments.push({ v: leftPt, tier: 1 }, { v: rightPt, tier: 1 });
      hudNodes.push({ v: leftPt, tier: 0 }, { v: rightPt, tier: 0 });

      if (prevLeft && prevRight) {
        hudSegments.push({ v: prevLeft, tier: 2 }, { v: leftPt, tier: 2 });
        hudSegments.push({ v: prevRight, tier: 2 }, { v: rightPt, tier: 2 });
      }
      prevLeft = leftPt;
      prevRight = rightPt;
    }
  }

  // 6 Gyroscopic Telemetry Tick Rings (EXACT config from original)
  const ringConfigs = [
    { r: 2.15, ticks: 130, tickLen: 0.18, tiltX: 0.4, tiltY: 0.2, tier: 3 },
    { r: 3.10, ticks: 180, tickLen: 0.25, tiltX: -0.7, tiltY: 0.8, tier: 1 },
    { r: 3.95, ticks: 220, tickLen: 0.32, tiltX: 1.1, tiltY: -0.5, tier: 1 },
    { r: 4.75, ticks: 260, tickLen: 0.28, tiltX: -0.3, tiltY: 1.2, tier: 2 },
    { r: 5.45, ticks: 300, tickLen: 0.40, tiltX: 0.6, tiltY: -0.9, tier: 1 },
    { r: 5.85, ticks: 170, tickLen: 0.52, tiltX: -1.2, tiltY: 0.3, tier: 3 },
  ];

  ringConfigs.forEach(cfg => {
    const euler = new THREE.Euler(cfg.tiltX, cfg.tiltY, 0);
    let prevBase = null;
    for (let i = 0; i < cfg.ticks; i++) {
      if (Math.sin(i * 0.15) < -0.48) {
        prevBase = null;
        continue;
      }
      const angle = (i / cfg.ticks) * Math.PI * 2;
      const modLen = cfg.tickLen * (i % 5 === 0 ? 1.8 : (i % 2 === 0 ? 1.0 : 0.5));
      const pBase = new THREE.Vector3(Math.cos(angle) * cfg.r, Math.sin(angle) * cfg.r, 0).applyEuler(euler);
      const pTip  = new THREE.Vector3(Math.cos(angle) * (cfg.r + modLen), Math.sin(angle) * (cfg.r + modLen), 0).applyEuler(euler);

      hudSegments.push({ v: pBase, tier: cfg.tier }, { v: pTip, tier: cfg.tier });
      hudNodes.push({ v: pTip, tier: i % 5 === 0 ? 0 : cfg.tier });

      if (prevBase) {
        hudSegments.push({ v: prevBase, tier: 2 }, { v: pBase, tier: 2 });
      }
      prevBase = pBase;
    }
  });

  return buildConnectedLayer(hudSegments, hudNodes, 0.11, 0.52, 0.88);
}

/* ============================================================
   MAIN SCENE — Assembles all layers + handles animation
   ============================================================ */
function MainScene({ colors, mode = 'idle', onCoreClick, audioLevel = 0 }) {
  const coreColorsRef = useRef(colors);
  coreColorsRef.current = colors;

  const threeColors = useMemo(() => ({
    core: new THREE.Color(colors.core),
    bright: new THREE.Color(colors.bright),
    primary: new THREE.Color(colors.primary),
    secondary: new THREE.Color(colors.secondary),
  }), [colors]);

  const getTierColor = useCallback((tier) => {
    if (tier === 0) return threeColors.core;
    if (tier === 1) return threeColors.primary;
    if (tier === 2) return threeColors.secondary;
    return threeColors.bright;
  }, [threeColors]);

  // Build all layers once (EXACT geometry from original)
  const pcbLayer = useMemo(() => buildPCBLayer(), []);
  const neuralLayer = useMemo(() => buildNeuralLayer(), []);
  const hudLayer = useMemo(() => buildHUDLayer(), []);

  return (
    <>
      {/* Center Core */}
      <CoreGroup
        colors={threeColors}
        mode={mode}
        onCoreClick={onCoreClick}
        audioLevel={audioLevel}
      />

      {/* Layer 1: PCB Buses + Circuit Wings */}
      <DynamicLayer
        layerData={pcbLayer}
        getTierColor={getTierColor}
        coreColor={threeColors.core}
        powerScale={mode === 'listening' ? 1.05 : mode === 'analyzing' ? 1.25 : 0.80}
        rotationFn={(group, t) => {
          const spd = mode === 'analyzing' ? 2.0 : 1.0;
          group.rotation.y = -t * 0.07 * spd;
          group.rotation.x = Math.cos(t * 0.15 * spd) * 0.06;
        }}
      />

      {/* Layer 2: Neural Cortex + Synapses */}
      <DynamicLayer
        layerData={neuralLayer}
        getTierColor={getTierColor}
        coreColor={threeColors.core}
        powerScale={mode === 'speaking' ? 1.15 : mode === 'analyzing' ? 1.3 : 0.80}
        rotationFn={(group, t) => {
          const spd = mode === 'analyzing' ? 2.2 : 1.0;
          group.rotation.y = t * 0.12 * spd;
          group.rotation.z = Math.sin(t * 0.2 * spd) * 0.08;
        }}
      />

      {/* Layer 3: Hex Patches + Radar Ladders + Gyro Rings */}
      <DynamicLayer
        layerData={hudLayer}
        getTierColor={getTierColor}
        coreColor={threeColors.core}
        powerScale={mode === 'listening' ? 1.1 : 0.80}
        rotationFn={(group, t) => {
          const spd = mode === 'analyzing' ? 1.8 : 1.0;
          group.rotation.y = t * 0.09 * spd;
          group.rotation.z = -t * 0.04 * spd;
        }}
      />
    </>
  );
}

/* ============================================================
   Camera Setup
   ============================================================ */
function SceneSetup() {
  const { camera } = useThree();
  useEffect(() => {
    camera.position.set(0, 0.4, 15.0);
  }, [camera]);
  return null;
}

/* ============================================================
   EXPORT: TATTVACoreOrb
   ============================================================ */
export default function TATTVACoreOrb({
  className,
  style,
  mode = 'idle',
  onCoreClick,
  audioLevel = 0,
}) {
  const { theme } = useTheme();
  const c3d = theme.core3d;

  return (
    <div
      className={className}
      style={{
        width: '100%',
        height: '100%',
        cursor: 'pointer',
        ...style,
      }}
      onClick={(e) => {
        // Also trigger onCoreClick on container tap/click
        onCoreClick?.();
      }}
    >
      <Canvas
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
          toneMapping: THREE.ReinhardToneMapping,
          toneMappingExposure: 0.88,
        }}
        camera={{ fov: 54, near: 0.1, far: 1000 }}
        style={{ background: 'transparent' }}
      >
        <SceneSetup />

        <MainScene
          colors={c3d}
          mode={mode}
          onCoreClick={onCoreClick}
          audioLevel={audioLevel}
        />

        <OrbitControls
          enableDamping dampingFactor={0.05}
          maxDistance={28} minDistance={4}
          enablePan={false}
        />

        <EffectComposer>
          <Bloom
            intensity={mode === 'listening' ? 2.2 : mode === 'analyzing' ? 2.5 : 1.68 * 0.80}
            luminanceThreshold={0.06}
            luminanceSmoothing={0.52}
            radius={0.6}
          />
        </EffectComposer>
      </Canvas>
    </div>
  );
}

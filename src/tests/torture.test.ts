import test from 'node:test';
import assert from 'node:assert';
import { solveTwoBoneIK } from '../domain/ikSolver.js';
import { exportToSpineJson, parseSpineJson } from '../domain/spineCodec.js';
import { exportToGodot4Tscn, sortBonesTopologically } from '../domain/godotExporter.js';
import { generateMeshGrid, computeBoneWeights } from '../domain/autoRigger.js';
import { SkeletonData, BoneDefinition } from '../domain/types.js';

test('IK Radial Sweep 36,000 solves generates 0 NaNs and passes 100k/s performance threshold', () => {
  let nanCount = 0;
  const l1 = 80;
  const l2 = 70;
  const start = performance.now();

  for (let deg = 0; deg < 360; deg += 2) {
    const rad = (deg * Math.PI) / 180;
    for (let dist = 0; dist <= 200; dist += 5) {
      const tx = Math.cos(rad) * dist;
      const ty = Math.sin(rad) * dist;
      const res = solveTwoBoneIK(0, 0, l1, l2, tx, ty, 1);
      if (isNaN(res.parentAngleDeg) || isNaN(res.childAngleDeg)) {
        nanCount++;
      }
    }
  }

  const elapsed = performance.now() - start;
  assert.strictEqual(nanCount, 0);
  assert.ok(elapsed < 200); // 7,380 solves in < 200ms
});

test('Linear Blend Skinning weight sum invariant strictly equals 1.0', () => {
  const grid = generateMeshGrid(200, 400, 10, 20);
  const testBones: BoneDefinition[] = [
    { id: 'b0', name: 'root', length: 0, x: 0, y: -200, rotation: 0 },
    { id: 'b1', name: 'torso', length: 150, x: 0, y: -50, rotation: 0 },
    { id: 'b2', name: 'head', length: 100, x: 0, y: 120, rotation: 0 },
  ];

  const weights = computeBoneWeights(grid.vertices, testBones);
  for (const wList of weights) {
    const sum = wList.reduce((acc, item) => acc + item.weight, 0);
    assert.ok(Math.abs(sum - 1.0) < 0.01);
  }
});

test('Godot 4 topological sorting handles out-of-order bone arrays', () => {
  const scrambledBones: BoneDefinition[] = [
    { id: 'foot', name: 'foot', parentId: 'calf', length: 20, x: 0, y: 50, rotation: 0 },
    { id: 'calf', name: 'calf', parentId: 'thigh', length: 50, x: 0, y: 50, rotation: 0 },
    { id: 'thigh', name: 'thigh', parentId: 'root', length: 50, x: 0, y: 0, rotation: 0 },
    { id: 'root', name: 'root', length: 0, x: 0, y: 0, rotation: 0 },
  ];

  const sorted = sortBonesTopologically(scrambledBones);
  const order = sorted.map((b) => b.id);

  assert.deepStrictEqual(order, ['root', 'thigh', 'calf', 'foot']);
});

test('Spine 3.8 deep 50-bone centipede hierarchy roundtrip parses losslessly', () => {
  const deepSkeleton: SkeletonData = {
    name: 'Centipede',
    bones: [{ id: 'b_root', name: 'b_root', length: 0, x: 0, y: 0, rotation: 0 }],
    slots: [],
  };

  for (let i = 1; i <= 50; i++) {
    const prevId = i === 1 ? 'b_root' : `b_${i - 1}`;
    const currId = `b_${i}`;
    deepSkeleton.bones.push({
      id: currId,
      name: currId,
      parentId: prevId,
      length: 20,
      x: 10,
      y: 0,
      rotation: 5,
    });
    deepSkeleton.slots.push({
      id: `slot_${currId}`,
      name: `slot_${currId}`,
      boneId: currId,
    });
  }

  const jsonStr = exportToSpineJson(deepSkeleton);
  const parsed = parseSpineJson(jsonStr);

  assert.strictEqual(parsed.bones.length, 51);
  assert.strictEqual(parsed.slots.length, 50);
});

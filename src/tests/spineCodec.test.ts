import test from 'node:test';
import assert from 'node:assert';
import { exportToSpineJson } from '../domain/spineCodec.js';
import { SkeletonData } from '../domain/types.js';

test('exportToSpineJson generates valid Spine 3.8 JSON structure', () => {
  const skeleton: SkeletonData = {
    name: 'HeroTest',
    bones: [
      { id: 'root', name: 'root', length: 0, x: 0, y: 0, rotation: 0 },
      { id: 'torso', name: 'torso', parentId: 'root', length: 50, x: 0, y: 20, rotation: 90 },
    ],
    slots: [
      { id: 'torso_slot', name: 'torso_slot', boneId: 'torso', attachmentName: 'torso_img' },
    ],
  };

  const jsonStr = exportToSpineJson(skeleton);
  const parsed = JSON.parse(jsonStr);

  assert.strictEqual(parsed.skeleton.spine, '3.8.99');
  assert.strictEqual(parsed.bones.length, 2);
  assert.strictEqual(parsed.slots.length, 1);
  assert.strictEqual(parsed.slots[0].bone, 'torso');
});

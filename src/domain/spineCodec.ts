import { SkeletonData } from './types.js';

/**
 * Spine 3.8 / 4.0 JSON Format Codec
 * Serializes Bone-Forge SkeletonData into industry-standard Spine JSON
 * loadable by official Spine runtimes in Godot, Unity, PixiJS, Phaser, etc.
 */

export function exportToSpineJson(data: SkeletonData): string {
  const spineObj: any = {
    skeleton: {
      hash: 'bone-forge-' + Date.now(),
      spine: '3.8.99',
      width: 500,
      height: 500,
      images: './images/',
      audio: '',
    },
    bones: data.bones.map((b) => ({
      name: b.name,
      parent: b.parentId,
      length: b.length || 0,
      x: b.x || 0,
      y: b.y || 0,
      rotation: b.rotation || 0,
      scaleX: b.scaleX ?? 1,
      scaleY: b.scaleY ?? 1,
    })),
    slots: data.slots.map((s) => ({
      name: s.name,
      bone: s.boneId,
      attachment: s.attachmentName || s.name,
      color: s.color || 'ffffffff',
    })),
    ik: (data.ikConstraints || []).map((ik) => ({
      name: ik.name,
      order: 0,
      bones: ik.bones,
      target: ik.targetBoneId,
      bendPositive: ik.bendDirection === 1,
      mix: ik.mix,
    })),
    animations: {},
  };

  // Convert animations
  if (data.animations) {
    for (const [animName, clip] of Object.entries(data.animations)) {
      const animData: any = { bones: {} };
      for (const [boneName, frames] of Object.entries(clip.boneTimelines)) {
        animData.bones[boneName] = {
          rotate: frames.map((f) => ({
            time: f.time,
            angle: f.rotation || 0,
            curve: f.curve ? f.curve : undefined,
          })),
          translate: frames.map((f) => ({
            time: f.time,
            x: f.x || 0,
            y: f.y || 0,
          })),
        };
      }
      spineObj.animations[animName] = animData;
    }
  }

  return JSON.stringify(spineObj, null, 2);
}

export function parseSpineJson(jsonString: string): SkeletonData {
  const parsed = JSON.parse(jsonString);
  const bones = (parsed.bones || []).map((b: any) => ({
    id: b.name,
    name: b.name,
    parentId: b.parent,
    length: b.length || 0,
    x: b.x || 0,
    y: b.y || 0,
    rotation: b.rotation || 0,
    scaleX: b.scaleX ?? 1,
    scaleY: b.scaleY ?? 1,
  }));

  const slots = (parsed.slots || []).map((s: any) => ({
    id: s.name,
    name: s.name,
    boneId: s.bone,
    attachmentName: s.attachment,
    color: s.color,
  }));

  const ikConstraints = (parsed.ik || []).map((ik: any) => ({
    name: ik.name,
    targetBoneId: ik.target,
    bones: ik.bones,
    bendDirection: ik.bendPositive ? 1 : -1,
    mix: ik.mix ?? 1.0,
  }));

  return {
    name: parsed.skeleton?.hash || 'ImportedSkeleton',
    bones,
    slots,
    ikConstraints,
  };
}

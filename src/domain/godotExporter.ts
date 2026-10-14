import { SkeletonData, BoneDefinition } from './types.js';

/**
 * Topologically sorts bones so parents are always emitted before their children.
 * This is a strict requirement for Godot 4 .tscn scene parser.
 */
export function sortBonesTopologically(bones: BoneDefinition[]): BoneDefinition[] {
  const result: BoneDefinition[] = [];
  const added = new Set<string>();
  const map = new Map(bones.map((b) => [b.id, b]));
  const remaining = [...bones];

  let progress = true;
  while (remaining.length > 0 && progress) {
    progress = false;
    for (let i = 0; i < remaining.length; i++) {
      const b = remaining[i];
      if (!b.parentId || added.has(b.parentId) || !map.has(b.parentId)) {
        result.push(b);
        added.add(b.id);
        remaining.splice(i, 1);
        progress = true;
        break;
      }
    }
  }

  result.push(...remaining);
  return result;
}

export function exportToGodot4Tscn(data: SkeletonData): string {
  const lines: string[] = [];

  lines.push('[gd_scene format=3 uid="uid://boneforge_' + Date.now() + '"]');
  lines.push('');
  lines.push(`[node name="${data.name || 'CharacterRoot'}" type="Node2D"]`);
  lines.push('');
  lines.push('[node name="Skeleton2D" type="Skeleton2D" parent="."]');
  lines.push('');

  const sortedBones = sortBonesTopologically(data.bones);
  const boneMap = new Map(sortedBones.map((b) => [b.id, b]));

  function getParentPath(boneId: string): string {
    const b = boneMap.get(boneId);
    if (!b || !b.parentId) return 'Skeleton2D';
    return getParentPath(b.parentId) + '/' + b.parentId;
  }

  for (const bone of sortedBones) {
    const parentPath = getParentPath(bone.id);
    lines.push(`[node name="${bone.name}" type="Bone2D" parent="${parentPath}"]`);
    lines.push(`position = Vector2(${bone.x}, ${bone.y})`);
    if (bone.rotation !== 0) {
      const rad = (bone.rotation * Math.PI) / 180;
      lines.push(`rotation = ${rad.toFixed(4)}`);
    }
    if (bone.length > 0) {
      lines.push(`rest = Transform2D(1, 0, 0, 1, ${bone.x}, ${bone.y})`);
    }
    lines.push('');
  }

  if (data.animations && Object.keys(data.animations).length > 0) {
    lines.push('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]');
    lines.push('');
  }

  return lines.join('\n');
}

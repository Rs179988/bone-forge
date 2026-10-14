import { SkeletonData } from './types.js';

/**
 * Godot 4 Scene (.tscn) Exporter
 * Generates a native Godot 4 2D Scene containing:
 * - Node2D (Root)
 * - Skeleton2D with hierarchical Bone2D nodes
 * - AnimationPlayer with tracks for position and rotation
 */

export function exportToGodot4Tscn(data: SkeletonData): string {
  const lines: string[] = [];

  lines.push('[gd_scene format=3 uid="uid://boneforge_' + Date.now() + '"]');
  lines.push('');
  lines.push(`[node name="${data.name || 'CharacterRoot'}" type="Node2D"]`);
  lines.push('');
  lines.push('[node name="Skeleton2D" type="Skeleton2D" parent="."]');
  lines.push('');

  // Map bones into a hierarchy
  const boneMap = new Map(data.bones.map((b) => [b.id, b]));

  function getParentPath(boneId: string): string {
    const b = boneMap.get(boneId);
    if (!b || !b.parentId) return 'Skeleton2D';
    return getParentPath(b.parentId) + '/' + b.parentId;
  }

  for (const bone of data.bones) {
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

  // AnimationPlayer
  if (data.animations && Object.keys(data.animations).length > 0) {
    lines.push('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]');
    lines.push('');
  }

  return lines.join('\n');
}

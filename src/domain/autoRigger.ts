import { BoneDefinition, MeshAttachment, VertexWeight } from './types.js';

/**
 * Auto-Rigging & Mesh Skinning Generator
 * Creates a deformed mesh grid with smooth distance-based bone weights.
 * Enforces Linear Blend Skinning invariant: sum of weights per vertex = 1.0.
 */

export function generateMeshGrid(
  width: number,
  height: number,
  cols = 4,
  rows = 4
): { vertices: number[]; uvs: number[]; triangles: number[] } {
  const vertices: number[] = [];
  const uvs: number[] = [];
  const triangles: number[] = [];

  const dx = width / cols;
  const dy = height / rows;

  for (let r = 0; r <= rows; r++) {
    for (let c = 0; c <= cols; c++) {
      const x = c * dx - width / 2;
      const y = r * dy - height / 2;
      vertices.push(Math.round(x), Math.round(y));
      uvs.push(Math.round((c / cols) * 100) / 100, Math.round((r / rows) * 100) / 100);
    }
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const p0 = r * (cols + 1) + c;
      const p1 = p0 + 1;
      const p2 = (r + 1) * (cols + 1) + c;
      const p3 = p2 + 1;

      // Two triangles per quad
      triangles.push(p0, p1, p2);
      triangles.push(p1, p3, p2);
    }
  }

  return { vertices, uvs, triangles };
}

export function computeBoneWeights(
  vertices: number[],
  bones: BoneDefinition[]
): VertexWeight[][] {
  const vertexWeights: VertexWeight[][] = [];
  const vertexCount = vertices.length / 2;

  for (let i = 0; i < vertexCount; i++) {
    const vx = vertices[i * 2];
    const vy = vertices[i * 2 + 1];

    const boneInfluences: { boneIndex: number; distance: number; weight: number }[] = [];

    bones.forEach((bone, bIdx) => {
      const bx = bone.x;
      const by = bone.y;
      const dist = Math.sqrt((vx - bx) * (vx - bx) + (vy - by) * (vy - by));
      // Inverse distance squared weighting
      const rawWeight = 1.0 / Math.pow(Math.max(dist, 10), 2);
      boneInfluences.push({ boneIndex: bIdx, distance: dist, weight: rawWeight });
    });

    // Pick top 2 most influential bones
    boneInfluences.sort((a, b) => b.weight - a.weight);
    const topBones = boneInfluences.slice(0, 2);

    const totalWeight = topBones.reduce((sum, b) => sum + b.weight, 0);

    // Normalize weights to guarantee sum = 1.0
    const normalized: VertexWeight[] = topBones.map((b) => ({
      boneIndex: b.boneIndex,
      weight: Math.round((b.weight / totalWeight) * 1000) / 1000,
    }));

    vertexWeights.push(normalized);
  }

  return vertexWeights;
}

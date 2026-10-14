export interface BoneDefinition {
  id: string;
  name: string;
  parentId?: string;
  length: number;
  rotation: number; // in degrees
  x: number;
  y: number;
  scaleX?: number;
  scaleY?: number;
}

export interface SlotDefinition {
  id: string;
  name: string;
  boneId: string;
  color?: string; // e.g. "ffffffff"
  attachmentName?: string;
}

export interface VertexWeight {
  boneIndex: number;
  weight: number;
}

export interface MeshAttachment {
  name: string;
  type: 'mesh';
  width: number;
  height: number;
  vertices: number[]; // flat [x0, y0, x1, y1...] or weighted
  uvs: number[];      // flat [u0, v0, u1, v1...]
  triangles: number[]; // index triplets [0, 1, 2, 2, 3, 0...]
  vertexWeights?: VertexWeight[][]; // per-vertex bone weights
}

export interface RegionAttachment {
  name: string;
  type: 'region';
  x: number;
  y: number;
  rotation: number;
  width: number;
  height: number;
  scaleX?: number;
  scaleY?: number;
}

export type Attachment = RegionAttachment | MeshAttachment;

export interface IKConstraint {
  name: string;
  targetBoneId: string;
  bones: [string, string]; // [parentBoneId, childBoneId] (e.g. [thigh, calf])
  bendDirection: 1 | -1;    // 1 for forward/clockwise, -1 for backward/counter-clockwise
  mix: number;              // 0.0 to 1.0 (influence factor)
}

export interface BoneTimelineFrame {
  time: number; // in seconds
  rotation?: number;
  x?: number;
  y?: number;
  scaleX?: number;
  scaleY?: number;
  curve?: [number, number, number, number]; // Bezier [cx1, cy1, cx2, cy2]
}

export interface AnimationClip {
  name: string;
  duration: number; // in seconds
  boneTimelines: Record<string, BoneTimelineFrame[]>; // key: boneId
}

export interface SkeletonData {
  name: string;
  bones: BoneDefinition[];
  slots: SlotDefinition[];
  ikConstraints?: IKConstraint[];
  attachments?: Record<string, Record<string, Attachment>>; // [slotName][attachmentName]
  animations?: Record<string, AnimationClip>;
}

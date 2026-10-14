/**
 * Analytical Two-Bone Inverse Kinematics (IK) Solver
 * Uses the Law of Cosines to calculate exact joint angles for 2-segment limbs (e.g. Upper Leg + Lower Leg).
 * Eliminates joint flip singularities and guarantees smooth real-time performance.
 */

export interface IKSolveResult {
  parentAngleDeg: number; // e.g. Thigh angle
  childAngleDeg: number;  // e.g. Calf angle relative to parent
  reachable: boolean;
  actualDistance: number;
}

export function solveTwoBoneIK(
  rootX: number,
  rootY: number,
  l1: number,          // Length of bone 1 (parent / upper arm / thigh)
  l2: number,          // Length of bone 2 (child / forearm / calf)
  targetX: number,
  targetY: number,
  bendDirection: 1 | -1 = 1
): IKSolveResult {
  const dx = targetX - rootX;
  const dy = targetY - rootY;
  const distSq = dx * dx + dy * dy;
  const dist = Math.sqrt(distSq);

  // Angle from root to target
  const baseAngle = Math.atan2(dy, dx);

  // Maximum and minimum reach
  const maxReach = l1 + l2;
  const minReach = Math.abs(l1 - l2);

  // Target out of reach (straighten towards target)
  if (dist >= maxReach) {
    return {
      parentAngleDeg: (baseAngle * 180) / Math.PI,
      childAngleDeg: 0,
      reachable: false,
      actualDistance: dist,
    };
  }

  // Target too close (fully fold)
  if (dist <= minReach) {
    return {
      parentAngleDeg: (baseAngle * 180) / Math.PI,
      childAngleDeg: bendDirection * 180,
      reachable: false,
      actualDistance: dist,
    };
  }

  // Law of Cosines:
  // c^2 = a^2 + b^2 - 2ab * cos(C)
  // cos(alpha) for parent bone angle offset
  const cosAlpha = (l1 * l1 + distSq - l2 * l2) / (2 * l1 * dist);
  const clampedCosAlpha = Math.max(-1, Math.min(1, cosAlpha));
  const alpha = Math.acos(clampedCosAlpha);

  // cos(beta) for internal elbow/knee angle
  const cosBeta = (l1 * l1 + l2 * l2 - distSq) / (2 * l1 * l2);
  const clampedCosBeta = Math.max(-1, Math.min(1, cosBeta));
  const beta = Math.acos(clampedCosBeta);

  // Parent absolute angle
  const parentAngleRad = baseAngle - bendDirection * alpha;
  // Child relative angle (relative to parent axis)
  const childAngleRad = bendDirection * (Math.PI - beta);

  return {
    parentAngleDeg: (parentAngleRad * 180) / Math.PI,
    childAngleDeg: (childAngleRad * 180) / Math.PI,
    reachable: true,
    actualDistance: dist,
  };
}

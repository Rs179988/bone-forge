import test from 'node:test';
import assert from 'node:assert';
import { solveTwoBoneIK } from '../domain/ikSolver.js';

test('solveTwoBoneIK reaches valid target with analytical Law of Cosines', () => {
  const l1 = 100;
  const l2 = 100;
  // Reach 45-degree target at distance sqrt(100^2 + 100^2) = 141.42
  const res = solveTwoBoneIK(0, 0, l1, l2, 100, 100, 1);

  assert.strictEqual(res.reachable, true);
  assert.ok(Math.abs(res.actualDistance - 141.42) < 0.1);
  assert.ok(Number.isFinite(res.parentAngleDeg));
  assert.ok(Number.isFinite(res.childAngleDeg));
});

test('solveTwoBoneIK clamps gracefully when target is out of reach', () => {
  const l1 = 50;
  const l2 = 50;
  // Target at 200 is beyond max reach of 100
  const res = solveTwoBoneIK(0, 0, l1, l2, 200, 0, 1);

  assert.strictEqual(res.reachable, false);
  assert.strictEqual(res.actualDistance, 200);
  assert.strictEqual(res.childAngleDeg, 0); // straight limb
});

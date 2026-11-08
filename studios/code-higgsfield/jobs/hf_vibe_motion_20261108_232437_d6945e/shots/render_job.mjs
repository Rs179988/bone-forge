#!/usr/bin/env node
// Stateless Render Job Runner (render_job.mjs)
// Usage: node shots/render_job.mjs [--frames 0-599] [--shot S1] [--layer L2_HeroSubject] [--mode master|preview] [--dry-run]
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const JOB_DIR = path.resolve(HERE, '..');
const PARALLEL_RENDERER = path.resolve(JOB_DIR, '../../backend/renderer/parallel_renderer.py');

const args = process.argv.slice(2);
const res = spawnSync('python3', [PARALLEL_RENDERER, JOB_DIR, ...args], { stdio: 'inherit' });
process.exit(res.status ?? 0);

# Bone-Forge 🦴

> **Autonomous 2D Skeletal Animation, Inverse Kinematics & Mesh Skinning Engine.**  
> *A 100% Free, Local-First, Clean-Room Alternative to Spine 2D Pro & Cascadeur for Indie Game Developers.*

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-blue.svg)](https://www.typescriptlang.org/)
[![Godot 4 Ready](https://img.shields.io/badge/Godot-4.x%20Ready-478cbf.svg)](https://godotengine.org/)
[![Spine 3.8 Compatible](https://img.shields.io/badge/Spine-3.8%20JSON%20Compatible-brightgreen.svg)]()

---

## 🎯 Why Bone-Forge?

Proprietary 2D skeletal animation software charges **$360+ per license** or high monthly subscription fees. This locks out millions of indie game developers, students, and artists in emerging markets.

**Bone-Forge** democratizes 2D skeletal animation:
1. **Free Local Core**: Build bone hierarchies, solve Inverse Kinematics, deform weighted meshes, and animate timelines in your terminal or browser.
2. **Universal Compatibility**: Exports seamlessly to **Godot 4 (`Skeleton2D`)**, **Spine 3.8 JSON** (runs in Unity, PixiJS, Phaser, Raylib, Defold), and **WebGPU/HTML5**.
3. **AI-Ready Architecture**: Exposes Model Context Protocol (MCP) tools so AI agents can autonomously rig characters from raw sprite sheets.

---

## 🚀 Key Features

* **🦴 Analytical 2-Bone IK Solver**: Precise Law-of-Cosines trigonometry for realistic limbs (arms/legs) with customizable bend directions and softness.
* **🎨 Linear Blend Skinning (LBS)**: Automatic distance-based mesh weight calculations ensuring vertex deformation without mesh tearing ($\sum w = 1.0$).
* **🎮 Godot 4 Native Scene Generator**: Directly produces `.tscn` files featuring `Skeleton2D`, `Bone2D`, and `AnimationPlayer` tracks.
* **📦 Standard Spine JSON Exporter**: Output files immediately loadable by any official Spine runtime.
* **🌐 Standalone HTML5 Canvas Previewer**: Generates a self-contained zero-dependency interactive HTML preview player.
* **🤖 Native MCP Server**: Allows AI agents (Cursor, Claude, Gemini, Antigravity) to inspect, solve IK, and rig characters autonomously.

---

## 📦 Quick Start

### Installation
```bash
git clone https://github.com/Rs179988/bone-forge.git
cd bone-forge
npm install
npm run build
```

### CLI Commands
```bash
# 1. Create a boilerplate biped character skeleton
node dist/cli.js init hero-skeleton.json

# 2. Solve 2-Bone Inverse Kinematics for a target coordinate (e.g., reaching for a weapon)
node dist/cli.js solve-ik --upper 100 --lower 90 --target 120,60 --bend 1

# 3. Export to Spine 3.8 JSON for Unity / PixiJS
node dist/cli.js export-spine hero-skeleton.json -o hero-spine.json

# 4. Export directly to Godot 4 .tscn Scene
node dist/cli.js export-godot hero-skeleton.json -o HeroCharacter.tscn

# 5. Generate interactive HTML5 preview
node dist/cli.js preview hero-skeleton.json -o preview.html
```

---

## 💼 Business Model & Monetization

Bone-Forge follows a proven **Open-Core & Managed AI Service Model**:
- **100% Free Core**: CLI, local rigging, IK solver, Godot/Spine exporters.
- **Paid Tier**: Cloud AI Auto-Rigging API (1-click image-to-rigged-skeleton) and Asset Store.
- See [`BUSINESS_MODEL.md`](./BUSINESS_MODEL.md) for full monetization architecture.

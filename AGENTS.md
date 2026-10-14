# Repository Guidelines for Bone-Forge

## Core Philosophy

Bone-Forge is a **Clean-Room 2D Skeletal Animation & Inverse Kinematics Engine**.
It bridges the gap for indie developers, students, and small game studios who cannot afford expensive proprietary licenses (such as Spine 2D Pro or Cascadeur).

1. **Deterministic Kinematics**: Inverse Kinematics (IK) solvers must use exact analytical trigonometry (Law of Cosines) and stable clamping to eliminate joint flips or NaN singularities.
2. **Standard Interoperability**: Skeletons and animations must be 100% compatible with standard Spine 3.8/4.0 JSON schemas and Godot 4 `Skeleton2D` / `Polygon2D` scene hierarchies.
3. **Local-First & Zero-Telemetry Core**: The editor and CLI must run 100% offline with zero required cloud accounts or telemetry.
4. **Mathematical Skinning Invariants**: Vertex weights in linear blend skinning (LBS) must always sum to 1.0 per vertex ($\sum w_i = 1.0$) to prevent mesh tearing or volume collapse.

## Code Quality Standards
- Strict TypeScript with zero `any` shortcuts in public domain interfaces.
- Clear separation between Core Kinematics (`src/domain/`), Exporters (`src/domain/*Exporter.ts`), CLI (`src/cli.ts`), and MCP Server (`src/mcp/`).

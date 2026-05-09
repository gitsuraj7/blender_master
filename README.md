# Blender Master Automation Pipeline

![Blender](https://img.shields.io/badge/blender-4.2-orange?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)

A professional automation and rendering pipeline designed for creating high-fidelity, cinematic 3D scenes in Blender. 

## 🎯 Overview

This repository contains the core scripts and project files for generating complex scenes, such as the "Neon Maze" and "Sacred Cavern". The pipeline utilizes custom Python scripts to handle asset generation, lighting, camera composition, and automated rendering.

### Key Features
- **Procedural Scene Generation:** Automated assembly of architectural elements and environments.
- **Cinematic Lighting Automation:** Scripts to control god-rays, volumetric depth, and focal lighting.
- **Render Management:** Handlers for automated batch rendering of frames and sequences.
- **Agentic Integration:** Components for MCP server communication and AI-driven workflow orchestration.

## 📁 Repository Structure

- `ancient_ruins/` - Project files for the "Sacred Cavern" masterpiece.
- `agents/` - Configurations and scripts for AI integration and MCP servers.
- `*.py` - Python automation scripts for building and rendering scenes.

## 🚀 Getting Started

1. Ensure Blender 4.2+ is installed.
2. Clone this repository.
3. Open the main project `.blend` files or execute the Python scripts via Blender's background mode.

```bash
blender -b ancient_ruins/sacred_cavern_v9_master.blend -P render_encounter.py
```

## 📜 Automation Scripts

- `render_encounter.py` - Main render handler for encounters.
- `render_encounter_anim.py` - Animation specific rendering sequence.
- `run_flicker_animation.py` - Light flicker effect generation.
- `start_mcp_server.py` - Initializes the Model Context Protocol server.

---
*Built for the ultimate "Assembly-First" workflow. Break every straight line.*

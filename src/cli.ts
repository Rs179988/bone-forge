import { Command } from 'commander';
import fs from 'node:fs';
import { solveTwoBoneIK } from './domain/ikSolver.js';
import { exportToSpineJson } from './domain/spineCodec.js';
import { exportToGodot4Tscn } from './domain/godotExporter.js';
import { generateHtmlPreview } from './domain/htmlPlayer.js';
import { SkeletonData } from './domain/types.js';

const program = new Command();

program
  .name('bone-forge')
  .description('Autonomous 2D Skeletal Animation & Inverse Kinematics Engine for Indie Game Devs.')
  .version('1.0.0');

// Command 1: init boilerplate biped
program
  .command('init <output>')
  .description('Create a starter biped character skeleton JSON')
  .action((outputPath) => {
    const starter: SkeletonData = {
      name: 'BipedHero',
      bones: [
        { id: 'root', name: 'root', length: 0, x: 0, y: 0, rotation: 0 },
        { id: 'pelvis', name: 'pelvis', parentId: 'root', length: 30, x: 0, y: -40, rotation: 90 },
        { id: 'torso', name: 'torso', parentId: 'pelvis', length: 70, x: 0, y: 30, rotation: 0 },
        { id: 'head', name: 'head', parentId: 'torso', length: 45, x: 0, y: 70, rotation: 0 },
        // Left Leg
        { id: 'thigh_l', name: 'thigh_l', parentId: 'pelvis', length: 65, x: -20, y: 0, rotation: -90 },
        { id: 'calf_l', name: 'calf_l', parentId: 'thigh_l', length: 60, x: 0, y: 65, rotation: 0 },
        { id: 'foot_l', name: 'foot_l', parentId: 'calf_l', length: 25, x: 0, y: 60, rotation: 90 },
        // Right Leg
        { id: 'thigh_r', name: 'thigh_r', parentId: 'pelvis', length: 65, x: 20, y: 0, rotation: -90 },
        { id: 'calf_r', name: 'calf_r', parentId: 'thigh_r', length: 60, x: 0, y: 65, rotation: 0 },
        { id: 'foot_r', name: 'foot_r', parentId: 'calf_r', length: 25, x: 0, y: 60, rotation: 90 },
      ],
      slots: [
        { id: 'torso_slot', name: 'torso_slot', boneId: 'torso', attachmentName: 'torso_sprite' },
        { id: 'head_slot', name: 'head_slot', boneId: 'head', attachmentName: 'head_sprite' },
      ],
      ikConstraints: [
        { name: 'ik_leg_l', targetBoneId: 'foot_l', bones: ['thigh_l', 'calf_l'], bendDirection: 1, mix: 1.0 },
        { name: 'ik_leg_r', targetBoneId: 'foot_r', bones: ['thigh_r', 'calf_r'], bendDirection: 1, mix: 1.0 },
      ],
    };

    fs.writeFileSync(outputPath, JSON.stringify(starter, null, 2), 'utf-8');
    console.log(`[Bone-Forge] Starter biped skeleton written to ${outputPath}`);
  });

// Command 2: solve-ik
program
  .command('solve-ik')
  .description('Solve analytical 2-bone Inverse Kinematics')
  .requiredOption('--upper <length>', 'Length of upper bone', parseFloat)
  .requiredOption('--lower <length>', 'Length of lower bone', parseFloat)
  .requiredOption('--target <x,y>', 'Target point (e.g. 100,50)')
  .option('--bend <dir>', 'Bend direction (1 or -1)', '1')
  .action((options) => {
    const [tx, ty] = options.target.split(',').map(parseFloat);
    const bend = parseInt(options.bend, 10) === -1 ? -1 : 1;
    const res = solveTwoBoneIK(0, 0, options.upper, options.lower, tx, ty, bend);

    console.log(JSON.stringify(res, null, 2));
  });

// Command 3: export-spine
program
  .command('export-spine <input>')
  .description('Export skeleton to Spine 3.8 JSON format')
  .requiredOption('-o, --output <file>', 'Output JSON file')
  .action((inputPath, options) => {
    const content = fs.readFileSync(inputPath, 'utf-8');
    const skeleton = JSON.parse(content);
    const spineJson = exportToSpineJson(skeleton);
    fs.writeFileSync(options.output, spineJson, 'utf-8');
    console.log(`[Bone-Forge] Exported Spine 3.8 JSON to ${options.output}`);
  });

// Command 4: export-godot
program
  .command('export-godot <input>')
  .description('Export skeleton to Godot 4 .tscn Scene')
  .requiredOption('-o, --output <file>', 'Output .tscn file')
  .action((inputPath, options) => {
    const content = fs.readFileSync(inputPath, 'utf-8');
    const skeleton = JSON.parse(content);
    const tscn = exportToGodot4Tscn(skeleton);
    fs.writeFileSync(options.output, tscn, 'utf-8');
    console.log(`[Bone-Forge] Exported Godot 4 Scene to ${options.output}`);
  });

// Command 5: preview
program
  .command('preview <input>')
  .description('Generate interactive HTML5 canvas animation preview')
  .requiredOption('-o, --output <file>', 'Output HTML file')
  .action((inputPath, options) => {
    const content = fs.readFileSync(inputPath, 'utf-8');
    const skeleton = JSON.parse(content);
    const html = generateHtmlPreview(skeleton);
    fs.writeFileSync(options.output, html, 'utf-8');
    console.log(`[Bone-Forge] Interactive preview written to ${options.output}`);
  });

program.parse(process.argv);

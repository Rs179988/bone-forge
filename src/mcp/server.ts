import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { solveTwoBoneIK } from '../domain/ikSolver.js';
import { exportToSpineJson } from '../domain/spineCodec.js';
import { exportToGodot4Tscn } from '../domain/godotExporter.js';
import { generateMeshGrid, computeBoneWeights } from '../domain/autoRigger.js';
import { SkeletonData } from '../domain/types.js';

const server = new Server(
  {
    name: 'bone-forge-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'solve_two_bone_ik',
        description: 'Calculates exact joint angles for a 2-segment limb (arm or leg) reaching a target using analytical Law of Cosines.',
        inputSchema: {
          type: 'object',
          properties: {
            rootX: { type: 'number', default: 0 },
            rootY: { type: 'number', default: 0 },
            upperBoneLength: { type: 'number', description: 'Length of thigh or upper arm' },
            lowerBoneLength: { type: 'number', description: 'Length of calf or forearm' },
            targetX: { type: 'number' },
            targetY: { type: 'number' },
            bendDirection: { type: 'number', enum: [1, -1], default: 1 },
          },
          required: ['upperBoneLength', 'lowerBoneLength', 'targetX', 'targetY'],
        },
      },
      {
        name: 'export_to_spine',
        description: 'Converts a Bone-Forge skeleton data object into standard Spine 3.8 compatible JSON.',
        inputSchema: {
          type: 'object',
          properties: {
            skeletonData: { type: 'object', description: 'The SkeletonData object' },
          },
          required: ['skeletonData'],
        },
      },
      {
        name: 'export_to_godot4',
        description: 'Converts a Bone-Forge skeleton data object into a native Godot 4 .tscn Scene.',
        inputSchema: {
          type: 'object',
          properties: {
            skeletonData: { type: 'object', description: 'The SkeletonData object' },
          },
          required: ['skeletonData'],
        },
      },
      {
        name: 'auto_rig_mesh',
        description: 'Generates a triangulated 2D mesh grid and computes normalized linear blend skinning weights for a list of bones.',
        inputSchema: {
          type: 'object',
          properties: {
            width: { type: 'number' },
            height: { type: 'number' },
            bones: { type: 'array', items: { type: 'object' } },
          },
          required: ['width', 'height', 'bones'],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === 'solve_two_bone_ik') {
      const a = args as any;
      const res = solveTwoBoneIK(
        a.rootX || 0,
        a.rootY || 0,
        a.upperBoneLength,
        a.lowerBoneLength,
        a.targetX,
        a.targetY,
        a.bendDirection || 1
      );
      return { content: [{ type: 'text', text: JSON.stringify(res, null, 2) }] };
    }

    if (name === 'export_to_spine') {
      const json = exportToSpineJson((args as any).skeletonData as SkeletonData);
      return { content: [{ type: 'text', text: json }] };
    }

    if (name === 'export_to_godot4') {
      const tscn = exportToGodot4Tscn((args as any).skeletonData as SkeletonData);
      return { content: [{ type: 'text', text: tscn }] };
    }

    if (name === 'auto_rig_mesh') {
      const a = args as any;
      const mesh = generateMeshGrid(a.width, a.height);
      const weights = computeBoneWeights(mesh.vertices, a.bones);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ mesh, weightsSample: weights.slice(0, 5) }, null, 2),
          },
        ],
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (err: any) {
    return {
      isError: true,
      content: [{ type: 'text', text: `Error: ${err.message}` }],
    };
  }
});

export async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

/* Generated from corpus/schemas by scripts/sync-contracts.mjs. Do not edit. */

export type RouteAPIV1 = RouteRequest | RoutePlan | Presets | Catalog;
export type Presets = Preset[];

export interface RouteRequest {
  account: AccountV1;
  settings: Settings;
  start: Location;
  destination: Location;
}
/**
 * An account as a player describes it. Names (skills, quests, diaries, unlocks, ...) are the Java enum constant names; GET /v1/catalog lists them with labels.
 */
export interface AccountV1 {
  name: string;
  levels: {
    [k: string]: number;
  };
  questPoints: number;
  completedQuests: string[];
  diaries: {
    [k: string]: "NONE" | "EASY" | "MEDIUM" | "HARD" | "ELITE";
  };
  unlocks: string[];
  spellbook: "STANDARD" | "ANCIENT" | "LUNAR" | "ARCEUUS";
  /**
   * When a minigame teleport was last used, in game minutes; absent means it is ready.
   */
  minigameTeleportUsedAt?: number;
  /**
   * The game clock in minutes; absent means the wall clock.
   */
  nowMinutes?: number;
  inventory: Items;
  runePouch: Items;
  equipment: Items;
  bank: Items;
  house?: House;
  plantedSpiritTrees: string[];
}
/**
 * Quantities by item id.
 */
export interface Items {
  [k: string]: number;
}
export interface House {
  location: string;
  jewelleryBox: "NONE" | "FANCY" | "ORNATE";
  fairyRing: boolean;
  spiritTree: boolean;
  obelisk: boolean;
  mountedGlory: boolean;
  mountedXerics: boolean;
  mountedDigsite: boolean;
  mountedMythical: boolean;
  /**
   * Nexus portal destinations; absent means every portal.
   */
  portals?: string[];
}
/**
 * Plugin settings that differ from the planner's defaults, by ShortestPathConfig method name. GET /v1/catalog lists every setting with its type and default.
 */
export interface Settings {
  [k: string]: boolean | number | string;
}
export interface Location {
  placeId?: string;
  name?: string;
  coordinate: WorldPoint;
}
export interface WorldPoint {
  x: number;
  y: number;
  plane: number;
}
export interface RoutePlan {
  apiVersion: "v1";
  reachable: boolean;
  costTicks: number | null;
  start: Location;
  destination: Location;
  segments: (WalkSegment | TravelSegment | BankSegment)[];
  metadata: {
    worldDataVersion: string;
    accountSchemaVersion: 1;
    routingEngineVersion: "legacy-v1" | "exact-v1";
  };
}
export interface WalkSegment {
  kind: "walk";
  costTicks: number;
  /**
   * @minItems 1
   */
  path: [WorldPoint, ...WorldPoint[]];
}
export interface TravelSegment {
  kind: "teleport" | "transport";
  transportId: string;
  name: string;
  from: WorldPoint;
  to: WorldPoint;
  costTicks: number;
  requirements: Capability[];
}
export interface Capability {
  kind: "quest" | "diary" | "skill" | "item" | "unlock";
  name: string;
}
export interface BankSegment {
  kind: "bank";
  location: WorldPoint;
  costTicks: number;
}
export interface Preset {
  id: string;
  name: string;
  account: AccountV1;
}
export interface Catalog {
  skills: Option[];
  quests: Option[];
  diaries: Option[];
  diaryTiers: Option[];
  unlocks: Option[];
  spellbooks: Option[];
  houseLocations: Option[];
  jewelleryBoxes: Option[];
  portals: Option[];
  plantedSpiritTrees: Option[];
  settings: Setting[];
}
export interface Option {
  id: string;
  name: string;
  group?: string;
}
export interface Setting {
  key: string;
  name: string;
  description: string;
  section: string;
  type: "boolean" | "integer" | "choice";
  choices?: Option[];
  defaultValue: boolean | number | string;
}

/**
 * 数据访问层：加载「探索清单」与「各探索的详情数据」，并提供强类型接口与工具函数。
 * 纯前端，无后端依赖。所有 AI 影响数据均为初步估计（preliminary: true）。
 *
 * 扩展方式：
 *   1. 在 explorations/ 下新增 <id>.json（结构同 0001.json）
 *   2. 在本文件的 dataMap 中加一行 `['<id>']: importXxxJson`
 *   3. 在 explorations-index.json 的 explorations 数组中加一条摘要
 */

import explorationsIndexJson from './explorations-index.json'
import exploration0001Json from './explorations/0001.json'

/** AI 影响定位：position 越接近 0 表示越偏向“完全替代”，越接近 1 表示越偏向“完全增强”。 */
export interface AiImpact {
  position: number
  label: string
  preliminary: boolean
}

/** 市场定性规模。 */
export type MarketScale = '大' | '中' | '小'

/** 功能类别（轴 A：功能角色）。 */
export interface Category {
  id: string
  name: string
  nameEn: string
  definition: string
  examples: string[]
  coreValue: string
  businessModel: string
  moat: string
  marketScale: MarketScale
  /** 创业者切入难度 / 壁垒强度（0=易切入，1=难切入），基于类别壁垒的定性估计。 */
  barrier: number
  step2Question: string
  aiImpact: AiImpact
}

/** 产品假设（机会层）。 */
export interface Hypothesis {
  id: string
  name: string
  /** 对应的功能类别 id，可多个（一个假设可能横跨多个类别）。 */
  category: string[]
  marketLayer: string
  form: string
  status: string
  note: string
}

/** 元数据。 */
export interface Meta {
  title: string
  exploration: string
  generatedAt: string
  description: string
}

/** 单个探索的顶层数据结构（对应 explorations/<id>.json）。 */
export interface TaxonomyData {
  meta: Meta
  categories: Category[]
  hypotheses: Hypothesis[]
}

/** 探索清单（对应 explorations-index.json）。 */
export interface ExplorationSummary {
  id: string
  title: string
  status: string
  startDate: string
  phase: string
  summary: string
  keyInsight: string
  hypothesisCount: number
  categoryCount: number
  accent: string
}

export interface ExplorationsIndex {
  project: {
    name: string
    tagline: string
    generatedAt: string
  }
  explorations: ExplorationSummary[]
}

/** 已加载并类型化的探索清单。 */
export const explorationsIndex: ExplorationsIndex = explorationsIndexJson as ExplorationsIndex

/** id → 探索详情数据。新增探索时在此登记。 */
const dataMap: Record<string, TaxonomyData> = {
  '0001': exploration0001Json as TaxonomyData,
}

/** 取得某探索的详情数据。 */
export function getExplorationData(id: string): TaxonomyData | undefined {
  return dataMap[id]
}

/** 取得某探索的摘要（来自清单）。 */
export function getExplorationSummary(id: string): ExplorationSummary | undefined {
  return explorationsIndex.explorations.find((exp) => exp.id === id)
}

/** 通过 id 在指定数据中快速查找类别。 */
export function findCategory(data: TaxonomyData, id: string): Category | undefined {
  return data.categories.find((category) => category.id === id)
}

/** 取一组类别某字段的平均值（用于假设落点的质心计算）。 */
export function averageOf(
  data: TaxonomyData,
  ids: string[],
  selector: (category: Category) => number,
): number {
  if (ids.length === 0) {
    return 0.5
  }
  const values: number[] = ids
    .map((id) => findCategory(data, id))
    .filter((category): category is Category => category !== undefined)
    .map(selector)
  if (values.length === 0) {
    return 0.5
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

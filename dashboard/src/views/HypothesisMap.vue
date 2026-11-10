<script setup lang="ts">
import { computed } from 'vue'
import { useThemeVars, NText, NTag, NSpace } from 'naive-ui'
import {
  findCategory,
  averageOf,
  type Category,
  type Hypothesis,
  type TaxonomyData,
} from '../data'

const props = defineProps<{ data: TaxonomyData }>()
const themeVars = useThemeVars()

/** 假设高亮配色。 */
const hypothesisColors: string[] = ['#63e2b7', '#2080f0', '#f2c97d', '#e8804d', '#9ccc65']

/** 背景类别点数据：[AI影响, 壁垒强度, 类别]。 */
const categoryPoints = computed<any[]>(() =>
  props.data.categories.map((cat) => ({
    value: [cat.aiImpact.position, cat.barrier],
    category: cat,
  })),
)

/** 假设高亮点数据：取其落点类别的质心作为坐标。 */
const hypothesisPoints = computed<any[]>(() =>
  props.data.hypotheses.map((hypo, index) => {
    const avgPosition = averageOf(props.data, hypo.category, (c) => c.aiImpact.position)
    const avgBarrier = averageOf(props.data, hypo.category, (c) => c.barrier)
    return {
      value: [avgPosition, avgBarrier],
      hypothesis: hypo,
      color: hypothesisColors[index % hypothesisColors.length],
    }
  }),
)

/** 覆盖度分析（由数据动态推导，不写死）。 */
const coveredIds = computed(
  () => new Set(props.data.hypotheses.flatMap((h) => h.category)),
)
const coveredCats = computed(() =>
  props.data.categories.filter((c) => coveredIds.value.has(c.id)),
)
const uncoveredCats = computed(() =>
  props.data.categories.filter((c) => !coveredIds.value.has(c.id)),
)

const option = computed<any>(() => ({
  backgroundColor: 'transparent',
  title: {
    text: '假设落图：AI 影响 × 创业者壁垒强度',
    subtext: 'y 轴 = 创业者切入难度/壁垒强度（0=易切入，1=难切入），基于类别壁垒定性估计',
    left: 'center',
    top: 4,
    textStyle: { color: themeVars.value.textColorBase, fontSize: 18 },
    subtextStyle: { color: themeVars.value.textColor3, fontSize: 12 },
  },
  tooltip: {
    trigger: 'item',
    backgroundColor: '#1c1c20',
    borderColor: themeVars.value.borderColor,
    textStyle: { color: themeVars.value.textColorBase },
    formatter: (params: any) => {
      if (params.seriesName === '功能类别（背景）') {
        const cat: Category = params.data.category
        return [
          `<b>${cat.name}</b> <span style="color:#8a8a92">${cat.nameEn}</span>`,
          `AI 影响定位：${cat.aiImpact.position.toFixed(2)}`,
          `创业者壁垒强度：${cat.barrier.toFixed(2)}`,
          `市场规模：${cat.marketScale}`,
        ].join('<br/>')
      }
      const hypo: Hypothesis = params.data.hypothesis
      const catNames = hypo.category
        .map((id) => findCategory(props.data, id)?.name ?? id)
        .join('、')
      return [
        `<b>${hypo.id} ${hypo.name}</b>`,
        `落点类别：${catNames}`,
        `市场分层：${hypo.marketLayer}`,
        `产品形态：${hypo.form}`,
        `状态：${hypo.status}`,
        `<span style="color:#8a8a92">${hypo.note}</span>`,
      ].join('<br/>')
    },
  },
  legend: {
    top: 56,
    textStyle: { color: themeVars.value.textColor2 },
    data: ['功能类别（背景）', '产品假设（HYP）'],
  },
  grid: { left: 70, right: 60, top: 100, bottom: 60 },
  xAxis: {
    type: 'value',
    min: 0,
    max: 1,
    name: 'AI 影响（替代 ←——→ 增强）',
    nameLocation: 'middle',
    nameGap: 32,
    nameTextStyle: { color: themeVars.value.textColor2, fontSize: 13 },
    axisLabel: {
      color: themeVars.value.textColor2,
      formatter: (value: number) => value.toFixed(1),
    },
    splitLine: { lineStyle: { color: themeVars.value.borderColor, type: 'dashed' } },
    axisLine: { lineStyle: { color: themeVars.value.borderColor } },
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 1,
    name: '创业者壁垒强度',
    nameLocation: 'middle',
    nameGap: 42,
    nameTextStyle: { color: themeVars.value.textColor2, fontSize: 13 },
    axisLabel: {
      color: themeVars.value.textColor2,
      formatter: (value: number) => value.toFixed(1),
    },
    splitLine: { lineStyle: { color: themeVars.value.borderColor, type: 'dashed' } },
    axisLine: { lineStyle: { color: themeVars.value.borderColor } },
  },
  series: [
    {
      name: '功能类别（背景）',
      type: 'scatter',
      symbolSize: 16,
      data: categoryPoints.value,
      itemStyle: {
        color: '#55555f',
        opacity: 0.55,
        borderColor: '#2a2a30',
        borderWidth: 1,
      },
      label: {
        show: true,
        position: 'right',
        distance: 4,
        color: themeVars.value.textColor3,
        fontSize: 10,
        formatter: (params: any) => params.data.category.name,
      },
      z: 1,
    },
    {
      name: '产品假设（HYP）',
      type: 'scatter',
      symbolSize: 22,
      data: hypothesisPoints.value,
      itemStyle: {
        color: (params: any) => params.data.color,
        opacity: 0.95,
        borderColor: '#0e0e12',
        borderWidth: 2,
      },
      label: {
        show: true,
        position: 'top',
        distance: 6,
        color: themeVars.value.textColorBase,
        fontSize: 12,
        fontWeight: 'bold',
        formatter: (params: any) => params.data.hypothesis.id,
      },
      emphasis: {
        itemStyle: { borderColor: '#ffffff', borderWidth: 2 },
      },
      z: 2,
    },
  ],
}))
</script>

<template>
  <div class="map">
    <VChart :option="option" autoresize class="map__chart" />

    <NSpace vertical :size="8" class="map__caption">
      <NText depth="2" class="map__insight">
        <b>覆盖度发现：</b>
        {{ props.data.hypotheses.length }} 个假设（HYP-001~00{{
          props.data.hypotheses.length
        }}）集中在
        <NTag
          v-for="cat in coveredCats"
          :key="cat.id"
          size="small"
          :bordered="false"
          type="warning"
        >
          {{ cat.name }}
        </NTag>
        <b>未覆盖</b>
        <NTag
          v-for="cat in uncoveredCats"
          :key="cat.id"
          size="small"
          :bordered="false"
          type="default"
        >
          {{ cat.name }}
        </NTag>
        区域。这是合理的（创业者应从大厂薄弱处切入），但也意味着我们主动放弃了部分地图的扫描。
      </NText>
      <NText depth="3" class="map__footnote">
        注：假设坐标取其落点类别的质心（AI 影响与壁垒强度的平均值）；背景点为各功能类别本身。
        所有坐标均为初步估计，待 Step 2 取证。
      </NText>
    </NSpace>
  </div>
</template>

<style scoped>
.map {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.map__chart {
  width: 100%;
  height: 520px;
}

.map__caption {
  padding: 4px 2px;
}

.map__insight {
  font-size: 13px;
  line-height: 2;
}

.map__footnote {
  font-size: 12px;
  line-height: 1.6;
}
</style>

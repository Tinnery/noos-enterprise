<script setup lang="ts">
import { computed } from 'vue'
import { useThemeVars, NText } from 'naive-ui'
import { type MarketScale, type Category, type TaxonomyData } from '../data'

const props = defineProps<{ data: TaxonomyData }>()
const themeVars = useThemeVars()

/** 市场规模 → 气泡直径（像素）。 */
const scaleSize: Record<MarketScale, number> = {
  大: 64,
  中: 42,
  小: 26,
}

/**
 * 根据 AI 影响定位着色：
 * 越靠左（替代）越偏橙红，越靠右（增强）越偏绿。
 */
function impactColor(position: number): string {
  if (position <= 0.3) {
    return '#e8804d' // 强替代
  }
  if (position <= 0.5) {
    return '#f2c97d' // 争议/中间
  }
  if (position <= 0.7) {
    return '#9ccc65' // 偏增强
  }
  return '#63e2b7' // 强增强
}

const option = computed<any>(() => ({
  backgroundColor: 'transparent',
  title: {
    text: 'AI 影响光谱',
    subtext:
      '初步估计，待 Step 2 取证 · 气泡越大=市场规模越大 · 越靠左=完全替代，越靠右=完全增强',
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
      const cat: Category = params.data.category
      return [
        `<b>${cat.name}</b> <span style="color:#8a8a92">${cat.nameEn}</span>`,
        `AI 影响定位：${cat.aiImpact.position.toFixed(2)}`,
        `${cat.aiImpact.label}`,
        `市场规模：${cat.marketScale}`,
      ].join('<br/>')
    },
  },
  grid: { left: 120, right: 60, top: 90, bottom: 50 },
  xAxis: {
    type: 'value',
    min: 0,
    max: 1,
    name: '完全替代  ←——  AI 影响定位  ——→  完全增强',
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
    type: 'category',
    inverse: true,
    data: props.data.categories.map((cat) => cat.name),
    axisLabel: { color: themeVars.value.textColorBase, fontSize: 12 },
    axisLine: { lineStyle: { color: themeVars.value.borderColor } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      type: 'scatter',
      symbolSize: (value: any) => scaleSize[value[2] as MarketScale] ?? 40,
      data: props.data.categories.map((cat) => ({
        value: [cat.aiImpact.position, cat.name, cat.marketScale],
        category: cat,
        itemStyle: {
          color: impactColor(cat.aiImpact.position),
          opacity: 0.85,
          borderColor: '#0e0e12',
          borderWidth: 1,
        },
      })),
      label: {
        show: true,
        position: 'right',
        distance: 6,
        color: themeVars.value.textColor2,
        fontSize: 11,
        formatter: (params: any) => params.data.category.aiImpact.position.toFixed(2),
      },
      emphasis: {
        itemStyle: { opacity: 1, borderColor: '#ffffff', borderWidth: 1.5 },
      },
    },
  ],
}))
</script>

<template>
  <div class="spectrum">
    <VChart :option="option" autoresize class="spectrum__chart" />
    <NText depth="3" class="spectrum__note">
      注：本图所有位置均为 Step 1 阶段的方向性初步估计（aiImpact.preliminary = true），
      实际替代/增强程度需 Step 2 结合证据取证后修正。
    </NText>
  </div>
</template>

<style scoped>
.spectrum {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.spectrum__chart {
  width: 100%;
  height: 560px;
}

.spectrum__note {
  font-size: 12px;
  line-height: 1.6;
}
</style>

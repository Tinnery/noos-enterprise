<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NConfigProvider,
  darkTheme,
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NTabs,
  NTabPane,
  NText,
  NTag,
  NButton,
} from 'naive-ui'
import Portfolio from './views/Portfolio.vue'
import Overview from './views/Overview.vue'
import ImpactSpectrum from './views/ImpactSpectrum.vue'
import HypothesisMap from './views/HypothesisMap.vue'
import { explorationsIndex, getExplorationData, getExplorationSummary } from './data'

/** 当前选中的探索 id；null 表示停留在组合首页。 */
const selectedId = ref<string | null>(null)

/** 当前探索的详情数据 + 摘要（二者都存在时才进入详情视图）。 */
const detail = computed(() => {
  if (!selectedId.value) {
    return null
  }
  const data = getExplorationData(selectedId.value)
  const summary = getExplorationSummary(selectedId.value)
  return data && summary ? { data, summary } : null
})

/** 从组合首页点进某个探索。 */
function openExploration(id: string) {
  selectedId.value = id
}

/** 返回组合首页。 */
function backToPortfolio() {
  selectedId.value = null
}
</script>

<template>
  <NConfigProvider :theme="darkTheme">
    <NLayout class="app-layout">
      <NLayoutHeader bordered class="app-header">
        <!-- 组合首页头部 -->
        <template v-if="!detail">
          <div class="app-header__title">
            <h1 class="app-header__h1">{{ explorationsIndex.project.name }}</h1>
            <NTag size="small" :bordered="false" type="info">探索看板</NTag>
            <NText depth="3" class="app-header__date">
              生成于 {{ explorationsIndex.project.generatedAt }}
            </NText>
          </div>
          <NText depth="3" class="app-header__desc">
            {{ explorationsIndex.project.tagline }}
          </NText>
        </template>

        <!-- 探索详情头部 -->
        <template v-else>
          <div class="app-header__title">
            <NButton size="small" quaternary @click="backToPortfolio" class="app-header__back">
              ← 全部探索
            </NButton>
            <span class="app-header__id" :style="{ color: detail.summary.accent }">
              {{ detail.summary.id }}
            </span>
            <h1 class="app-header__h1">{{ detail.summary.title }}</h1>
            <NTag size="small" :bordered="false" type="success">{{ detail.summary.status }}</NTag>
          </div>
          <NText depth="3" class="app-header__desc">
            {{ detail.data.meta.description }}
          </NText>
        </template>
      </NLayoutHeader>

      <NLayoutContent class="app-content">
        <!-- 组合首页 -->
        <Portfolio v-if="!detail" @select="openExploration" />

        <!-- 探索详情：三视图 -->
        <template v-else>
          <NTabs type="line" animated class="app-tabs" default-value="overview">
            <NTabPane name="overview" tab="分类图谱总览">
              <Overview :data="detail.data" />
            </NTabPane>
            <NTabPane name="spectrum" tab="AI 影响光谱">
              <ImpactSpectrum :data="detail.data" />
            </NTabPane>
            <NTabPane name="map" tab="假设落图">
              <HypothesisMap :data="detail.data" />
            </NTabPane>
          </NTabs>
        </template>
      </NLayoutContent>
    </NLayout>
  </NConfigProvider>
</template>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  background-color: #101014;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}
</style>

<style scoped>
.app-layout {
  min-height: 100vh;
  background-color: #101014;
}

.app-header {
  padding: 18px 28px;
  background-color: #18181c;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.app-header__title {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 12px;
}

.app-header__h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #e0e0e6;
}

.app-header__id {
  font-size: 16px;
  font-weight: 700;
}

.app-header__date {
  font-size: 12px;
}

.app-header__desc {
  font-size: 13px;
  line-height: 1.6;
  max-width: 900px;
}

.app-header__back {
  align-self: center;
}

.app-content {
  padding: 20px 28px 40px;
}

.app-tabs {
  margin-top: 4px;
}
</style>

<script setup lang="ts">
import {
  NGrid,
  NGi,
  NCard,
  NTag,
  NSpace,
  NText,
  NButton,
  NStatistic,
} from 'naive-ui'
import { explorationsIndex, type ExplorationSummary } from '../data'

const emit = defineEmits<{ (e: 'select', id: string): void }>()

function select(exp: ExplorationSummary) {
  emit('select', exp.id)
}
</script>

<template>
  <div class="portfolio">
    <NText depth="3" class="portfolio__intro">
      本看板汇总 Noos Enterprise 的全部探索。点击任意探索卡片进入其详细视图（分类图谱 /
      AI 影响光谱 / 假设落图）。
    </NText>

    <NGrid :cols="2" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
      <NGi
        v-for="exp in explorationsIndex.explorations"
        :key="exp.id"
        span="2 m:1"
      >
        <NCard
          size="small"
          hoverable
          class="exp-card"
          :style="{ borderLeft: `3px solid ${exp.accent}` }"
        >
          <template #header>
            <div class="exp-card__header">
              <span class="exp-card__id" :style="{ color: exp.accent }">{{ exp.id }}</span>
              <span class="exp-card__title">{{ exp.title }}</span>
            </div>
          </template>
          <template #header-extra>
            <NTag
              size="small"
              :bordered="false"
              :type="exp.status === '进行中' ? 'success' : 'default'"
            >
              {{ exp.status }}
            </NTag>
          </template>

          <NSpace vertical :size="10">
            <NText depth="3" class="exp-card__phase">
              {{ exp.phase }} · 启动 {{ exp.startDate }}
            </NText>
            <NText class="exp-card__summary">{{ exp.summary }}</NText>
            <NText depth="3" class="exp-card__insight">
              <span class="label">关键洞察：</span>{{ exp.keyInsight }}
            </NText>

            <div class="exp-card__stats">
              <NStatistic label="功能类别" :value="exp.categoryCount" />
              <NStatistic label="产品假设" :value="exp.hypothesisCount" />
            </div>

            <NButton size="small" type="primary" secondary @click="select(exp)">
              查看详情 →
            </NButton>
          </NSpace>
        </NCard>
      </NGi>
    </NGrid>
  </div>
</template>

<style scoped>
.portfolio__intro {
  font-size: 13px;
  line-height: 1.7;
  max-width: 900px;
}

.exp-card {
  background-color: #1c1c20;
}

.exp-card__header {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.exp-card__id {
  font-size: 15px;
  font-weight: 700;
}

.exp-card__title {
  font-size: 15px;
  font-weight: 600;
  color: #e0e0e6;
}

.exp-card__phase {
  font-size: 12px;
}

.exp-card__summary {
  font-size: 13px;
  line-height: 1.7;
  color: #d0d0d6;
}

.exp-card__insight {
  font-size: 12px;
  line-height: 1.6;
}

.exp-card__insight .label {
  color: #8a8a92;
}

.exp-card__stats {
  display: flex;
  gap: 28px;
}
</style>

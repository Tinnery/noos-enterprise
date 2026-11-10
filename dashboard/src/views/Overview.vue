<script setup lang="ts">
import { NGrid, NGi, NCard, NTag, NSpace, NText, NDivider } from 'naive-ui'
import { type MarketScale, type TaxonomyData } from '../data'

const props = defineProps<{ data: TaxonomyData }>()

/** 市场规模 → 标签颜色。 */
const scaleType: Record<MarketScale, 'success' | 'warning' | 'error'> = {
  大: 'success',
  中: 'warning',
  小: 'error',
}
</script>

<template>
  <div class="overview">
    <NSpace vertical :size="14">
      <NText depth="3" class="overview__count">
        共 {{ props.data.categories.length }} 个功能类别 · 分类图谱为 Step 1 成果
      </NText>

      <NGrid :cols="2" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
        <NGi v-for="cat in props.data.categories" :key="cat.id" span="2 m:1">
          <NCard :title="cat.name" size="small" hoverable class="category-card">
            <template #header-extra>
              <NTag :type="scaleType[cat.marketScale]" size="small" :bordered="false">
                {{ cat.marketScale }}市场
              </NTag>
            </template>

            <NSpace vertical :size="10">
              <NText depth="3" class="category-card__en">{{ cat.nameEn }}</NText>
              <NText class="category-card__def">{{ cat.definition }}</NText>

              <NDivider style="margin: 2px 0" />

              <div class="category-card__examples">
                <NTag
                  v-for="ex in cat.examples"
                  :key="ex"
                  size="small"
                  :bordered="false"
                  class="example-tag"
                >
                  {{ ex }}
                </NTag>
              </div>

              <NText depth="3" class="category-card__moat">
                <span class="label">壁垒：</span>{{ cat.moat }}
              </NText>
            </NSpace>
          </NCard>
        </NGi>
      </NGrid>
    </NSpace>
  </div>
</template>

<style scoped>
.category-card {
  background-color: #1c1c20;
}

.category-card__en {
  font-size: 12px;
  letter-spacing: 0.3px;
}

.category-card__def {
  font-size: 13px;
  line-height: 1.7;
  color: #d0d0d6;
}

.category-card__examples {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.example-tag {
  background-color: #2a2a30;
  color: #b8b8c0;
}

.category-card__moat {
  font-size: 12px;
  line-height: 1.6;
}

.category-card__moat .label {
  color: #8a8a92;
}
</style>

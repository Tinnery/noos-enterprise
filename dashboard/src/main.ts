import { createApp } from 'vue'
import App from './App.vue'

// Naive UI 暗色主题
import { darkTheme } from 'naive-ui'

// ECharts 按需注册（仅引入用到的图表与组件，减小打包体积）
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { ScatterChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

// 注册 ECharts 模块
use([
  CanvasRenderer,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

const app = createApp(App)

// 全局注册 ECharts 组件，方便各视图直接使用 <VChart />
app.component('VChart', VChart)

// 将暗色主题挂载到全局属性，供需要读取主题色的地方使用
app.config.globalProperties.$darkTheme = darkTheme

app.mount('#app')

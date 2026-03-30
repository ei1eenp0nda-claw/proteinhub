<template>
  <div class="waterfall-container" ref="containerRef">
    <div
      v-for="(column, colIndex) in columns"
      :key="colIndex"
      class="waterfall-column"
      :style="{ width: `${columnWidth}px` }"
    >
      <slot
        v-for="item in column"
        :key="item.id"
        :item="item"
      ></slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    required: true,
  },
  columnCount: {
    type: Number,
    default: 4,
  },
  columnWidth: {
    type: Number,
    default: 280,
  },
  gap: {
    type: Number,
    default: 16,
  },
})

const containerRef = ref(null)
const currentColumnCount = ref(props.columnCount)

// 根据容器宽度动态计算列数
const calculateColumns = () => {
  if (!containerRef.value) return
  
  const containerWidth = containerRef.value.clientWidth
  const possibleColumns = Math.floor((containerWidth + props.gap) / (props.columnWidth + props.gap))
  currentColumnCount.value = Math.max(1, Math.min(possibleColumns, props.columnCount))
}

// 将项目分配到各列
const columns = computed(() => {
  const cols = Array.from({ length: currentColumnCount.value }, () => [])
  const columnHeights = new Array(currentColumnCount.value).fill(0)
  
  props.items.forEach((item) => {
    // 找到高度最小的列
    const minHeightIndex = columnHeights.indexOf(Math.min(...columnHeights))
    cols[minHeightIndex].push(item)
    // 模拟高度增加（实际使用时可以根据图片比例计算）
    columnHeights[minHeightIndex] += 300 + Math.random() * 200
  })
  
  return cols
})

const columnWidth = computed(() => {
  if (!containerRef.value) return props.columnWidth
  const containerWidth = containerRef.value.clientWidth
  const totalGap = (currentColumnCount.value - 1) * props.gap
  return (containerWidth - totalGap) / currentColumnCount.value
})

// 监听窗口大小变化
let resizeObserver

onMounted(() => {
  calculateColumns()
  resizeObserver = new ResizeObserver(() => {
    calculateColumns()
  })
  if (containerRef.value) {
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

// 监听items变化
watch(() => props.items, () => {
  nextTick(() => calculateColumns())
}, { deep: true })
</script>

<style scoped>
.waterfall-container {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.waterfall-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (max-width: 768px) {
  .waterfall-container {
    gap: 8px;
  }
  
  .waterfall-column {
    gap: 8px;
  }
}
</style>
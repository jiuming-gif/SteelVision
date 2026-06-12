<template>
<div>
  <h2 class="text-2xl font-bold mb-6"><i class="fa-solid fa-layer-group mr-2 text-blue-500"></i>批量检测</h2>

  <!-- 上传区 -->
  <div v-if="files.length === 0" class="dropzone p-12 text-center" :class="{ active: dragging }"
    @dragover.prevent="dragging=true" @dragleave="dragging=false" @drop.prevent="onDrop">
    <input type="file" accept="image/*" multiple ref="batchInput" @change="onFileSelect" class="hidden" />
    <div @click="batchInput.click()" class="cursor-pointer">
      <i class="fa-solid fa-images text-5xl text-gray-300 dark:text-gray-600 mb-4 block"></i>
      <p class="text-lg font-medium text-gray-500 dark:text-gray-400">拖拽多张图片，或点击选择</p>
      <p class="text-sm text-gray-400 mt-2">支持批量选择 PNG / JPG</p>
    </div>
  </div>

  <!-- 已选择文件 + 检测中 -->
  <div v-else class="space-y-6">
    <div class="flex items-center gap-4 flex-wrap">
      <button @click="batchInput.click()" class="btn btn-ghost">
        <i class="fa-solid fa-rotate"></i> 重新选择
      </button>
      <input type="file" accept="image/*" multiple ref="batchInput" @change="onFileSelect" class="hidden" />
      <button v-if="!running && !finished" @click="startBatch" class="btn btn-primary">
        <i class="fa-solid fa-play"></i> 开始批量检测
      </button>
      <button v-if="running" @click="stopBatch" class="btn btn-danger">
        <i class="fa-solid fa-stop"></i> 停止
      </button>
      <span v-if="running" class="text-sm text-gray-500">
        进度: {{ currentIndex }} / {{ files.length }}
      </span>
    </div>

    <!-- 进度条 -->
    <div v-if="running || finished" class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>

    <!-- 结果表格 -->
    <div v-if="results.length > 0" class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="table-wp">
          <thead>
            <tr>
              <th>图片名称</th>
              <th>检测结果</th>
              <th>用时 (ms)</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in results" :key="i">
              <td class="font-medium">{{ r.name }}</td>
              <td>
                <span v-for="cls in r.classes" :key="cls" class="badge mr-1" :class="classBadge(cls)">{{ cls }}</span>
                <span v-if="r.classes.length === 0" class="badge badge-green">无缺陷</span>
              </td>
              <td>{{ r.time_ms.toFixed(1) }}</td>
              <td>
                <span v-if="r.error" class="badge badge-red">{{ r.error }}</span>
                <span v-else class="badge badge-green">成功</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 完成后跳转图表 -->
    <div v-if="finished" class="card p-6 text-center">
      <p class="text-lg font-medium mb-4">批量检测已完成，共 {{ results.length }} 张图片</p>
      <router-link to="/charts" class="btn btn-primary">
        <i class="fa-solid fa-chart-pie"></i> 查看统计图表
      </router-link>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAppStore } from '../stores'

const store = useAppStore()
const dragging = ref(false)
const files = ref([])
const results = ref([])
const running = ref(false)
const finished = ref(false)
const currentIndex = ref(0)
const stopRequested = ref(false)
const batchInput = ref(null)

const progressPercent = computed(() => {
  if (files.value.length === 0) return 0
  return (currentIndex.value / files.value.length) * 100
})

function classBadge(cls) {
  if (cls.includes('夹杂物')) return 'badge-red'
  if (cls.includes('补丁')) return 'badge-green'
  if (cls.includes('划痕')) return 'badge-blue'
  return 'badge-yellow'
}

function onFileSelect(e) {
  files.value = Array.from(e.target.files)
  results.value = []
  finished.value = false
  currentIndex.value = 0
}

function onDrop(e) {
  dragging.value = false
  files.value = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))
}

async function startBatch() {
  running.value = true
  finished.value = false
  stopRequested.value = false
  results.value = []
  for (currentIndex.value = 0; currentIndex.value < files.value.length; currentIndex.value++) {
    if (stopRequested.value) break
    const file = files.value[currentIndex.value]
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await axios.post('/predict', form)
      const classes = (data.detection_result && data.detection_result !== '无缺陷')
        ? data.detection_result.split(',').map(s => s.trim()) : []
      results.value.push({
        name: file.name,
        classes,
        time_ms: data.model_time_ms,
        error: null,
      })
      const mask = data.mask
      if (mask) {
        const flat = mask.flat()
        store.detectResults.push(...flat)
      }
    } catch (e) {
      results.value.push({
        name: file.name,
        classes: [],
        time_ms: 0,
        error: e.response?.data?.detail || e.message,
      })
    }
  }
  running.value = false
  finished.value = !stopRequested.value
}

function stopBatch() {
  stopRequested.value = true
}
</script>

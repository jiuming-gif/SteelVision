<template>
<div>
  <h2 class="text-2xl font-bold mb-6"><i class="fa-solid fa-camera mr-2 text-blue-500"></i>摄像头实时检测</h2>

  <div class="grid grid-cols-2 gap-6">
    <!-- 摄像头画面 -->
    <div class="card p-4">
      <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide">摄像头画面</h3>
      <div class="rounded-xl overflow-hidden bg-black flex items-center justify-center min-h-[360px] relative">
        <video ref="video" autoplay playsinline class="w-full max-h-[480px] object-contain" :class="{ hidden: !streaming }"></video>
        <div v-if="!streaming" class="text-gray-400 text-center p-8">
          <i class="fa-solid fa-video-slash text-4xl block mb-3"></i>
          摄像头未开启
        </div>
      </div>
    </div>

    <!-- 检测结果叠加 -->
    <div class="card p-4">
      <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide">检测叠加</h3>
      <div class="rounded-xl bg-black flex items-center justify-center min-h-[360px] relative">
        <canvas ref="overlayCanvas" class="max-w-full max-h-[480px] object-contain" :class="{ hidden: !streaming }"></canvas>
        <div v-if="!streaming" class="text-gray-400 text-center p-8">
          <i class="fa-solid fa-eye-slash text-4xl block mb-3"></i>
          等待摄像头开启
        </div>
      </div>
    </div>
  </div>

  <!-- 控制栏 -->
  <div class="mt-6 flex items-center gap-4">
    <button v-if="!streaming" @click="startCamera" class="btn btn-primary">
      <i class="fa-solid fa-play"></i> 打开摄像头
    </button>
    <button v-else @click="stopCamera" class="btn btn-danger">
      <i class="fa-solid fa-stop"></i> 关闭摄像头
    </button>
    <div v-if="streaming" class="flex items-center gap-3">
      <label class="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" v-model="detectEnabled" class="w-4 h-4 accent-blue-500" />
        <span class="text-sm">启用实时检测</span>
      </label>
      <span class="text-sm text-gray-500">检测间隔: {{ intervalMs }}ms</span>
    </div>
  </div>

  <!-- 检测日志 -->
  <div v-if="log.length > 0" class="mt-6 card p-4 max-h-48 overflow-y-auto">
    <h4 class="font-semibold text-sm mb-2 text-gray-500">检测日志</h4>
    <div v-for="(entry, i) in log.slice(-20)" :key="i" class="text-xs text-gray-600 dark:text-gray-400 py-0.5 font-mono">
      [{{ entry.time }}] {{ entry.result }}
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, nextTick, onBeforeUnmount } from 'vue'
import axios from 'axios'

const video = ref(null)
const overlayCanvas = ref(null)
const streaming = ref(false)
const detectEnabled = ref(true)
const detectTimer = ref(null)
const intervalMs = ref(500)
const log = ref([])
const mediaStream = ref(null)

async function startCamera() {
  try {
    mediaStream.value = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
    const vid = video.value
    vid.srcObject = mediaStream.value
    streaming.value = true
    await nextTick()
    vid.play()
    startDetectionLoop()
  } catch (e) {
    alert('无法打开摄像头: ' + e.message)
  }
}

function stopCamera() {
  if (detectTimer.value) clearTimeout(detectTimer.value)
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(t => t.stop())
    mediaStream.value = null
  }
  streaming.value = false
}

function startDetectionLoop() {
  if (!streaming.value || !detectEnabled.value) return
  detectFrame()
}

async function detectFrame() {
  if (!streaming.value) return
  const vid = video.value
  const canvas = document.createElement('canvas')
  canvas.width = vid.videoWidth || 640
  canvas.height = vid.videoHeight || 480
  const ctx = canvas.getContext('2d')
  ctx.drawImage(vid, 0, 0)
  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8))
  try {
    const form = new FormData()
    form.append('file', blob, 'camera.jpg')
    const { data } = await axios.post('/predict', form)
    const now = new Date().toLocaleTimeString()
    log.value.push({ time: now, result: data.detection_result || '无缺陷' })
    drawOverlay(data.mask, canvas.width, canvas.height)
  } catch (e) {
    // 静默失败
  }
  if (streaming.value && detectEnabled.value) {
    detectTimer.value = setTimeout(() => detectFrame(), intervalMs.value)
  }
}

function drawOverlay(mask, w, h) {
  const oCanvas = overlayCanvas.value
  if (!oCanvas) return
  oCanvas.width = w
  oCanvas.height = h
  const octx = oCanvas.getContext('2d')
  octx.drawImage(video.value, 0, 0, w, h)
  const colors = { 0: [0,0,0,0], 1: [255,0,0,120], 2: [0,255,0,120], 3: [0,0,255,120] }
  const imageData = octx.getImageData(0, 0, w, h)
  for (let y = 0; y < Math.min(mask.length, h); y++) {
    for (let x = 0; x < Math.min((mask[y]?.length || 0), w); x++) {
      const cls = mask[y][x]
      const color = colors[cls] || colors[0]
      if (color[3] > 0) {
        const idx = (y * w + x) * 4
        const a = color[3] / 255
        imageData.data[idx]     = imageData.data[idx]     * (1 - a) + color[0] * a
        imageData.data[idx + 1] = imageData.data[idx + 1] * (1 - a) + color[1] * a
        imageData.data[idx + 2] = imageData.data[idx + 2] * (1 - a) + color[2] * a
      }
    }
  }
  octx.putImageData(imageData, 0, 0)
}

onBeforeUnmount(() => {
  stopCamera()
})
</script>

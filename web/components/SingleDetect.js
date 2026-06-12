SingleDetect = {
  template: `
<div>
  <h2 class="text-2xl font-bold mb-6"><i class="fa-solid fa-magnifying-glass mr-2 text-blue-500"></i>单图检测</h2>

  <!-- 无图片时显示上传区 -->
  <div v-if="!selectedImage" class="dropzone p-12 text-center" :class="{ active: dragging }"
    @dragover.prevent="dragging=true" @dragleave="dragging=false" @drop.prevent="onDrop">
    <input type="file" accept="image/*" ref="fileInput" @change="onFileSelect" class="hidden" />
    <div @click="$refs.fileInput.click()" class="cursor-pointer">
      <i class="fa-solid fa-cloud-arrow-up text-5xl text-gray-300 dark:text-gray-600 mb-4 block"></i>
      <p class="text-lg font-medium text-gray-500 dark:text-gray-400">拖拽图片到此处，或点击选择</p>
      <p class="text-sm text-gray-400 mt-2">支持 PNG / JPG / JPEG</p>
    </div>
  </div>

  <!-- 已选择图片 -->
  <div v-else class="space-y-6">
    <!-- 操作栏 -->
    <div class="flex items-center gap-4">
      <button @click="$refs.fileInput.click()" class="btn btn-ghost">
        <i class="fa-solid fa-rotate"></i> 重新选择
      </button>
      <input type="file" accept="image/*" ref="fileInput" @change="onFileSelect" class="hidden" />
      <button @click="startDetection" :disabled="detecting" class="btn btn-primary animate-glow">
        <i class="fa-solid" :class="detecting ? 'fa-spinner fa-spin' : 'fa-magnifying-glass'"></i>
        {{ detecting ? '检测中...' : '开始检测' }}
      </button>
    </div>

    <!-- 双图展示 -->
    <div class="grid grid-cols-2 gap-6">
      <!-- 原图 -->
      <div class="card p-4">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide">原始图片</h3>
        <div class="rounded-xl overflow-hidden bg-gray-100 dark:bg-slate-800 flex items-center justify-center min-h-[300px]">
          <img :src="imageUrl" class="max-w-full max-h-[500px] object-contain" />
        </div>
      </div>
      <!-- 检测结果 -->
      <div class="card p-4">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide">检测结果</h3>
        <div v-if="!result" class="rounded-xl bg-gray-100 dark:bg-slate-800 flex items-center justify-center min-h-[300px] text-gray-400">
          点击"开始检测"查看结果
        </div>
        <canvas v-else ref="resultCanvas" class="max-w-full max-h-[500px] object-contain rounded-xl"></canvas>
      </div>
    </div>

    <!-- 结果卡片 -->
    <div v-if="result" class="grid grid-cols-2 gap-6 animate-fadeIn">
      <!-- 检测信息 -->
      <div class="card p-5 space-y-3">
        <h4 class="font-bold text-lg"><i class="fa-solid fa-circle-info mr-2 text-blue-500"></i>检测信息</h4>
        <div class="flex flex-wrap gap-2">
          <span v-for="cls in result.detected_classes" :key="cls" class="badge" :class="classBadge(cls)">{{ cls }}</span>
          <span v-if="result.detected_classes.length === 0" class="badge badge-green">无缺陷</span>
        </div>
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div class="bg-gray-50 dark:bg-slate-800 rounded-lg p-3">
            <span class="text-gray-500 dark:text-gray-400">推理耗时</span>
            <p class="font-bold text-lg">{{ result.model_time_ms.toFixed(1) }} ms</p>
          </div>
          <div class="bg-gray-50 dark:bg-slate-800 rounded-lg p-3">
            <span class="text-gray-500 dark:text-gray-400">文件名</span>
            <p class="font-bold text-sm truncate">{{ fileName }}</p>
          </div>
        </div>
      </div>

      <!-- 维修建议 -->
      <div v-if="result.advice_content" class="card p-5 space-y-3" :class="result.advice_type === 'DIY' ? 'border-t-4 border-green-500' : 'border-t-4 border-orange-500'">
        <h4 class="font-bold text-lg flex items-center gap-2">
          <i :class="result.advice_type === 'DIY' ? 'fa-solid fa-wrench text-green-500' : 'fa-solid fa-shop text-orange-500'"></i>
          {{ result.advice_type === 'DIY' ? '建议 DIY 修复' : '建议前往汽修店' }}
        </h4>
        <div class="text-sm leading-relaxed whitespace-pre-line text-gray-600 dark:text-gray-300 markdown-content" v-html="renderMarkdown(result.advice_content)"></div>
      </div>
    </div>
  </div>
</div>`,
  data() {
    return {
      dragging: false,
      selectedImage: null,
      imageUrl: '',
      fileName: '',
      detecting: false,
      result: null,
    };
  },
  methods: {
    classBadge(cls) {
      if (cls.includes('夹杂物')) return 'badge-red';
      if (cls.includes('补丁')) return 'badge-green';
      if (cls.includes('划痕')) return 'badge-blue';
      return 'badge-yellow';
    },
    renderMarkdown(text) {
      // 简单 Markdown 渲染：加粗、列表
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-gray-900 dark:text-white">$1</strong>')
        .replace(/^- (.*)$/gm, '<li class="ml-4 list-disc">$1</li>')
        .replace(/(?:<\/li>)\n(?!<li>)/g, '$1</li></ul>')
        .replace(/(?<!<\/li>)\n<li/g, '<ul><li')
        .replace(/(\d+)\.\s(.*)/g, '<li class="ml-4 list-decimal">$2</li>');
    },
    onFileSelect(e) {
      const file = e.target.files[0];
      if (file) this.loadImage(file);
    },
    onDrop(e) {
      this.dragging = false;
      const file = e.dataTransfer.files[0];
      if (file) this.loadImage(file);
    },
    loadImage(file) {
      this.fileName = file.name;
      this.result = null;
      const reader = new FileReader();
      reader.onload = (ev) => {
        this.imageUrl = ev.target.result;
        this.selectedImage = file;
      };
      reader.readAsDataURL(file);
    },
    async startDetection() {
      if (!this.selectedImage) return;
      this.detecting = true;
      this.result = null;
      try {
        const form = new FormData();
        form.append('file', this.selectedImage);
        const { data } = await axios.post('/predict', form);
        this.result = {
          mask: data.mask,
          model_time_ms: data.model_time_ms,
          detected_classes: this.parseClasses(data.detection_result),
          advice_type: data.advice_type,
          advice_content: data.advice_content,
        };
        this.$nextTick(() => this.drawOverlay());
      } catch (e) {
        alert('检测失败: ' + (e.response?.data?.detail || e.message));
      } finally {
        this.detecting = false;
      }
    },
    parseClasses(resultStr) {
      if (!resultStr || resultStr === '无缺陷') return [];
      return resultStr.split(',').map(s => s.trim()).filter(Boolean);
    },
    drawOverlay() {
      const canvas = this.$refs.resultCanvas;
      if (!canvas || !this.result) return;
      const img = new Image();
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        // 叠加 mask 颜色
        const colors = { 0: [0,0,0,0], 1: [255,0,0,120], 2: [0,255,0,120], 3: [0,0,255,120] };
        const mask = this.result.mask;
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        for (let y = 0; y < mask.length && y < canvas.height; y++) {
          for (let x = 0; x < (mask[y]?.length || 0) && x < canvas.width; x++) {
            const cls = mask[y][x];
            const color = colors[cls] || colors[0];
            if (color[3] > 0) {
              const idx = (y * canvas.width + x) * 4;
              const alpha = color[3] / 255;
              imageData.data[idx]     = imageData.data[idx]     * (1 - alpha) + color[0] * alpha;
              imageData.data[idx + 1] = imageData.data[idx + 1] * (1 - alpha) + color[1] * alpha;
              imageData.data[idx + 2] = imageData.data[idx + 2] * (1 - alpha) + color[2] * alpha;
            }
          }
        }
        ctx.putImageData(imageData, 0, 0);
      };
      img.src = this.imageUrl;
    },
  },
};

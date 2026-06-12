ResultCharts = {
  template: `
<div>
  <h2 class="text-2xl font-bold mb-6"><i class="fa-solid fa-chart-pie mr-2 text-blue-500"></i>检测结果统计</h2>

  <div class="grid grid-cols-2 gap-6">
    <!-- 柱状图 -->
    <div class="card p-5">
      <h3 class="font-semibold text-gray-500 dark:text-gray-400 mb-4 uppercase text-sm tracking-wide">缺陷种类数量统计</h3>
      <div ref="barChart" style="height: 360px;"></div>
    </div>
    <!-- 饼图 -->
    <div class="card p-5">
      <h3 class="font-semibold text-gray-500 dark:text-gray-400 mb-4 uppercase text-sm tracking-wide">缺陷种类占比</h3>
      <div ref="pieChart" style="height: 360px;"></div>
    </div>
  </div>

  <!-- 摘要卡片 -->
  <div class="grid grid-cols-4 gap-4 mt-6">
    <div class="card p-4 text-center">
      <p class="text-3xl font-bold text-red-500">{{ counts[1] || 0 }}</p>
      <p class="text-sm text-gray-500 mt-1">夹杂物 (红色)</p>
    </div>
    <div class="card p-4 text-center">
      <p class="text-3xl font-bold text-green-500">{{ counts[2] || 0 }}</p>
      <p class="text-sm text-gray-500 mt-1">补丁 (绿色)</p>
    </div>
    <div class="card p-4 text-center">
      <p class="text-3xl font-bold text-blue-500">{{ counts[3] || 0 }}</p>
      <p class="text-sm text-gray-500 mt-1">划痕 (蓝色)</p>
    </div>
    <div class="card p-4 text-center">
      <p class="text-3xl font-bold text-gray-500">{{ totalDetected }}</p>
      <p class="text-sm text-gray-500 mt-1">总计检测像素</p>
    </div>
  </div>
</div>`,
  data() {
    return {
      barInstance: null,
      pieInstance: null,
    };
  },
  computed: {
    counts() {
      const c = { 0: 0, 1: 0, 2: 0, 3: 0 };
      for (const v of store.detectResults) {
        if (c[v] !== undefined) c[v]++;
      }
      return c;
    },
    totalDetected() {
      return this.counts[1] + this.counts[2] + this.counts[3];
    },
  },
  methods: {
    renderCharts() {
      const categories = ['无缺陷', '夹杂物', '补丁', '划痕'];
      const values = [this.counts[0], this.counts[1], this.counts[2], this.counts[3]];
      const colors = ['#94a3b8', '#ef4444', '#22c55e', '#3b82f6'];

      // 柱状图
      if (!this.barInstance) {
        this.barInstance = echarts.init(this.$refs.barChart, store.darkMode ? 'dark' : null);
      }
      this.barInstance.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: categories },
        yAxis: { type: 'value' },
        series: [{ type: 'bar', data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [6,6,0,0] } })) }],
        grid: { top: 20, right: 20, bottom: 40, left: 50 },
      });

      // 饼图
      if (!this.pieInstance) {
        this.pieInstance = echarts.init(this.$refs.pieChart, store.darkMode ? 'dark' : null);
      }
      this.pieInstance.setOption({
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie', radius: ['45%', '75%'],
          data: categories.map((name, i) => ({ name, value: values[i], itemStyle: { color: colors[i] } })),
          label: { formatter: '{b}\n{d}%' },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' } },
        }],
      });
    },
  },
  mounted() {
    this.$nextTick(() => this.renderCharts());
  },
  watch: {
    'store.detectResults'() {
      this.$nextTick(() => this.renderCharts());
    },
  },
  beforeUnmount() {
    if (this.barInstance) this.barInstance.dispose();
    if (this.pieInstance) this.pieInstance.dispose();
  },
};

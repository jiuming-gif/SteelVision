/* ── 全局 Store ────────────────────── */
const store = Vue.reactive({
  darkMode: localStorage.getItem('theme') === 'dark' || false,
  user: null,
  detectResults: [],   // 批量检测累计结果
});

// Axios 默认配置
axios.defaults.baseURL = '';

/* ── Vue Router（组件已在 index.html 中提前加载）── */
const routes = [
  { path: '/',              redirect: '/single' },
  { path: '/single',        component: SingleDetect,  name: 'single' },
  { path: '/batch',         component: BatchDetect,   name: 'batch' },
  { path: '/camera',        component: CameraDetect,  name: 'camera' },
  { path: '/chat',          component: AIChat,        name: 'chat' },
  { path: '/charts',        component: ResultCharts,  name: 'charts' },
  { path: '/admin',         component: AdminPanel,    name: 'admin' },
  { path: '/community',     component: Community,     name: 'community' },
];

const router = VueRouter.createRouter({
  history: VueRouter.createWebHashHistory(),
  routes,
});

/* ── Vue App ─────────────────────── */
const App = {
  data() {
    return {
      menuItems: [
        { path: '/single',  label: '单图检测', icon: 'fa-solid fa-magnifying-glass' },
        { path: '/batch',   label: '批量检测', icon: 'fa-solid fa-layer-group' },
        { path: '/camera',  label: '摄像头检测', icon: 'fa-solid fa-camera' },
        { path: '/chat',    label: 'AI 对话', icon: 'fa-solid fa-robot' },
        { path: '/charts',  label: '检测结果', icon: 'fa-solid fa-chart-pie' },
        { path: '/admin',   label: '管理面板', icon: 'fa-solid fa-shield-halved' },
        { path: '/community', label: '社区', icon: 'fa-solid fa-users' },
      ],
    };
  },
  computed: {
    themeIcon()  { return store.darkMode ? 'fa-solid fa-sun' : 'fa-solid fa-moon'; },
    themeLabel() { return store.darkMode ? '浅色模式' : '深色模式'; },
  },
  methods: {
    toggleTheme() {
      store.darkMode = !store.darkMode;
      localStorage.setItem('theme', store.darkMode ? 'dark' : 'light');
      document.documentElement.classList.toggle('dark', store.darkMode);
    },
  },
  mounted() {
    // 初始化主题
    if (store.darkMode || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      store.darkMode = true;
      document.documentElement.classList.add('dark');
    }
  },
};

const app = Vue.createApp(App);
app.use(router);
app.mount('#app');

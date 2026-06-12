AdminPanel = {
  template: `
<div>
  <h2 class="text-2xl font-bold mb-6"><i class="fa-solid fa-shield-halved mr-2 text-blue-500"></i>管理面板</h2>

  <div class="grid grid-cols-2 gap-6">
    <!-- 用户列表 -->
    <div class="card p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-500 dark:text-gray-400 uppercase text-sm tracking-wide">用户管理</h3>
        <button @click="showAddDialog = true" class="btn btn-primary text-sm py-1.5 px-3">
          <i class="fa-solid fa-plus"></i> 添加用户
        </button>
      </div>
      <div class="overflow-x-auto">
        <table class="table-wp">
          <thead>
            <tr><th>用户名</th><th>角色</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td class="font-medium">{{ user.username }}</td>
              <td><span class="badge" :class="user.role === 'admin' ? 'badge-red' : 'badge-blue'">{{ user.role }}</span></td>
              <td><span class="badge badge-green">活跃</span></td>
              <td>
                <button @click="editUser(user)" class="text-blue-500 hover:text-blue-700 mr-2"><i class="fa-solid fa-pen"></i></button>
                <button @click="deleteUser(user.id)" class="text-red-500 hover:text-red-700"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            <tr v-if="users.length === 0">
              <td colspan="4" class="text-center text-gray-400 py-8">暂无用户数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 添加/编辑用户表单 -->
    <div class="card p-5">
      <h3 class="font-semibold text-gray-500 dark:text-gray-400 uppercase text-sm tracking-wide mb-4">
        {{ editingUser ? '编辑用户' : '新增用户' }}
      </h3>
      <form @submit.prevent="saveUser" class="space-y-4">
        <div>
          <label class="text-sm font-medium text-gray-600 dark:text-gray-400 block mb-1">用户名</label>
          <input v-model="form.username" class="input" required placeholder="请输入用户名" />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-600 dark:text-gray-400 block mb-1">密码</label>
          <input v-model="form.password" class="input" type="password" required placeholder="请输入密码" />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-600 dark:text-gray-400 block mb-1">角色</label>
          <select v-model="form.role" class="input">
            <option value="user">用户</option>
            <option value="admin">管理员</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary w-full justify-center">
          <i class="fa-solid fa-check"></i> {{ editingUser ? '保存修改' : '创建用户' }}
        </button>
        <button v-if="editingUser" type="button" @click="cancelEdit" class="btn btn-ghost w-full justify-center">
          取消
        </button>
      </form>

      <!-- 使用说明 -->
      <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-sm text-blue-700 dark:text-blue-300">
        <h4 class="font-semibold mb-1"><i class="fa-solid fa-circle-info mr-1"></i>提示</h4>
        <p>用户数据存储在 SQLite 数据库中。管理员可管理用户，普通用户仅可使用检测功能。</p>
      </div>
    </div>
  </div>
</div>`,
  data() {
    return {
      users: [],
      form: { username: '', password: '', role: 'user' },
      editingUser: null,
      showAddDialog: false,
    };
  },
  methods: {
    async loadUsers() {
      try {
        // 简化：本地维护用户列表（Demo 阶段）
        // 实际可调用 GET /users 端点
        this.users = this.users.length ? this.users : [];
      } catch (e) {
        console.error(e);
      }
    },
    async saveUser() {
      try {
        if (this.editingUser) {
          // 更新用户 (本地模拟)
          const idx = this.users.findIndex(u => u.id === this.editingUser.id);
          if (idx >= 0) {
            this.users[idx] = { ...this.users[idx], ...this.form };
          }
        } else {
          // 调用注册 API
          const { data } = await axios.post('/register', this.form);
          this.users.push(data);
        }
        this.form = { username: '', password: '', role: 'user' };
        this.editingUser = null;
      } catch (e) {
        alert('操作失败: ' + (e.response?.data?.detail || e.message));
      }
    },
    editUser(user) {
      this.editingUser = user;
      this.form = { username: user.username, password: '', role: user.role };
    },
    cancelEdit() {
      this.editingUser = null;
      this.form = { username: '', password: '', role: 'user' };
    },
    deleteUser(id) {
      if (!confirm('确定删除此用户？')) return;
      this.users = this.users.filter(u => u.id !== id);
    },
  },
  mounted() {
    this.loadUsers();
  },
};

AIChat = {
  template: `
<div>
  <h2 class="text-2xl font-bold mb-6"><i class="fa-solid fa-robot mr-2 text-blue-500"></i>AI 智能对话</h2>
  <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">基于 DeepSeek 大模型的钢材缺陷检测助手</p>

  <div class="card flex flex-col" style="height: calc(100vh - 280px);">
    <!-- 聊天区域 -->
    <div class="flex-1 overflow-y-auto p-6 space-y-4" ref="chatArea">
      <div v-if="messages.length === 0" class="text-center text-gray-400 mt-20">
        <i class="fa-solid fa-comments text-5xl block mb-4"></i>
        <p>开始与 AI 助手对话，询问关于缺陷检测的问题</p>
      </div>

      <div v-for="(msg, i) in messages" :key="i" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        <div class="chat-bubble" :class="msg.role">
          <div v-if="msg.role === 'assistant'" class="text-xs text-gray-400 mb-1">
            <i class="fa-solid fa-robot mr-1"></i>DeepSeek
          </div>
          <div class="whitespace-pre-wrap" v-html="renderContent(msg.content)"></div>
          <div v-if="msg.loading" class="flex gap-1 mt-2">
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0s"></span>
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0.2s"></span>
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0.4s"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="border-t border-gray-200 dark:border-slate-700 p-4">
      <div class="flex gap-3">
        <input v-model="inputText" @keyup.enter="sendMessage"
          class="input flex-1" placeholder="输入消息，例如：划痕缺陷应该怎么修复？"
          :disabled="loading" />
        <button @click="sendMessage" :disabled="loading || !inputText.trim()" class="btn btn-primary">
          <i :class="loading ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-paper-plane'"></i>
          {{ loading ? '思考中' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</div>`,
  data() {
    return {
      messages: [
        { role: 'system', content: '你是一个钢材缺陷检测助手。' },
        { role: 'assistant', content: '你好！我是钢材缺陷检测 AI 助手。你可以向我咨询：\n\n• 缺陷类型分析（夹杂物、补丁、划痕等）\n• 修复方案建议（DIY 或专业维修）\n• 修复材料和步骤\n• 汽车零部件养护知识\n\n请问有什么可以帮助你的？' },
      ],
      inputText: '',
      loading: false,
      // 只保留最近的消息用于 API 上下文
      apiHistory: [
        { role: 'system', content: '你是一个钢材缺陷检测助手，用中文回答，专业且简洁。' },
      ],
    };
  },
  methods: {
    renderContent(text) {
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    },
    async sendMessage() {
      const text = this.inputText.trim();
      if (!text || this.loading) return;
      this.inputText = '';
      this.messages.push({ role: 'user', content: text });
      this.apiHistory.push({ role: 'user', content: text });

      // 添加 loading 消息
      const loadingMsg = { role: 'assistant', content: '', loading: true };
      this.messages.push(loadingMsg);

      this.loading = true;
      this.$nextTick(() => this.scrollToBottom());

      try {
        const { data } = await axios.post('/api/chat', {
          messages: this.apiHistory,
        });
        // 移除 loading
        this.messages.pop();
        const reply = data.reply || '抱歉，我暂时无法回答。';
        this.messages.push({ role: 'assistant', content: reply });
        this.apiHistory.push({ role: 'assistant', content: reply });
        // 限制上下文长度
        if (this.apiHistory.length > 20) {
          this.apiHistory = [this.apiHistory[0], ...this.apiHistory.slice(-19)];
        }
      } catch (e) {
        this.messages.pop();
        const errMsg = '抱歉，AI 服务暂时不可用: ' + (e.response?.data?.detail || e.message);
        this.messages.push({ role: 'assistant', content: errMsg });
      } finally {
        this.loading = false;
        this.$nextTick(() => this.scrollToBottom());
      }
    },
    scrollToBottom() {
      const el = this.$refs.chatArea;
      if (el) el.scrollTop = el.scrollHeight;
    },
  },
};

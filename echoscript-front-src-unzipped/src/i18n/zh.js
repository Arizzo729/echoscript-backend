// src/i18n/zh.js
export default {
  purchase: {
    perMonth: "/月",
    free: "免费",
    getStarted: "开始使用",
    processing: "正在处理...",
    assistant: {
      title: "需要帮助选择？",
      body: "选择计划时可以考虑以下几点。",
      tips: [
        "入门计划适合尝试使用。",
        "专业版提供高级转录和更快速度。"
      ],
      note: "这些是基于使用模式的一般建议。",
      show: "显示助手",
      hide: "隐藏助手"
    },
    footer: {
      secure: "安全结账",
      privacy: "不存储敏感数据"
    },
    plans: {
      starter: {
        name: "入门",
        features: ["基础转录", "上传受限"],
        suggested: "适合轻度使用"
      },
      pro: {
        name: "专业版",
        features: ["无限转录", "快速排队", "AI 总结"],
        suggested: "非常适合创作者"
      },
      enterprise: {
        name: "企业版",
        price: "定制",
        features: ["专属支持", "本地部署", "团队访问"],
        suggested: "适用于团队或公司"
      }
    }
  }
};


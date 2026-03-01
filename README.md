# 📡 AMS 论文每日推送

自动追踪 AMS（美国气象学会）旗下期刊的最新论文，筛选与**热带气旋、温带气旋、双台风**等相关的文章，每天早上 8 点通过微信推送，并附带 **AI 中文总结**。

---

## ✨ 功能特性

- 📰 **自动抓取** JAS / MWR / WAF 三本期刊的最新 RSS
- 🔍 **关键词过滤**：tropical cyclone、fujiwhara effect、binary interaction 等
- 🤖 **AI 中文总结**：调用 DeepSeek，对每篇命中文章生成 3-4 句中文摘要
- 📲 **微信推送**：通过 Server酱 推送到你的微信
- 🔁 **自动去重**：已推送过的文章不会重复出现
- ⏰ **全自动定时**：基于 GitHub Actions，每天北京时间 08:00 运行，无需自己电脑开着

---

## 📋 覆盖期刊

| 缩写 | 全称 |
|------|------|
| JAS | Journal of the Atmospheric Sciences |
| MWR | Monthly Weather Review |
| WAF | Weather and Forecasting |

---

## 🔍 默认关键词

**短语关键词**（出现即命中）：
- tropical cyclone
- extratropical cyclone
- binary typhoon
- fujiwhara / fujiwhara effect
- twin typhoon
- binary interaction
- cyclone-cyclone interaction

**缩写关键词**（需与 cyclone / typhoon / hurricane / storm 同时出现）：
- TC
- ETC

---

## 🚀 快速开始

### 第 1 步：准备账号和 API Key

| 服务 | 用途 | 费用 |
|------|------|------|
| [Server酱](https://sct.ftqq.com) | 微信推送 | 免费（每天 5 条） |
| [DeepSeek](https://platform.deepseek.com) | AI 中文摘要 | 极低（每篇约 ¥0.001） |
| GitHub 账号 | 运行定时任务 | 免费 |

- **Server酱**：微信扫码登录 → 复制 SendKey → 关注"方糖"公众号
- **DeepSeek**：注册 → 创建 API Key → 充值 ¥10（够用很久）

---

### 第 2 步：Fork 或克隆本仓库

点击右上角 **Fork**，把仓库复制到你自己的 GitHub 账号下。

---

### 第 3 步：配置 Secrets

进入你 Fork 后的仓库：

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

添加以下两个：

| Secret 名称 | 填入的值 |
|---|---|
| `SERVERCHAN_SENDKEY` | 你的 Server酱 SendKey |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key |

---

### 第 4 步：开启 Actions 写入权限

`Settings` → `Actions` → `General` → `Workflow permissions`

选择 **`Read and write permissions`** → `Save`

---

### 第 5 步：手动触发测试

`Actions` → `Daily Paper Push` → `Run workflow`

等待约 1-2 分钟，微信收到推送即代表配置成功。

**之后每天北京时间 08:00 全自动运行，无需任何操作。**

---

## 📁 文件结构

```
paper-push/
├── paper_push.py            # 主脚本
├── requirements.txt         # Python 依赖
├── seen.json                # 去重记录（自动维护）
└── .github/
    └── workflows/
        └── paper_push.yml   # GitHub Actions 定时配置
```

---

## ⚙️ 自定义关键词

打开 `paper_push.py`，修改以下两个列表：

```python
PHRASE_KEYWORDS = [
    "tropical cyclone",
    "extratropical cyclone",
    # 在这里添加你想追踪的短语
]

ABBREV_KEYWORDS = ["TC", "ETC"]  # 缩写关键词
```

修改后提交到仓库，下次运行自动生效。

---

## ⚙️ 自定义推送时间

打开 `.github/workflows/paper_push.yml`，修改 cron 表达式：

```yaml
- cron: "0 0 * * *"   # UTC 时间，当前 = 北京时间 08:00
```

例如改为北京时间 09:00：
```yaml
- cron: "0 1 * * *"
```

---

## 📲 推送效果示例


<img width="1994" height="1196" alt="image" src="https://github.com/user-attachments/assets/afa67dea-c045-48c6-8e3a-a5e8e2da2b5e" />


---

## ❓ 常见问题

**Q：每天推送的是当天发表的论文吗？**  
A：推送的是"自上次运行以来新出现在 RSS 里的文章"。第一次运行会推送 RSS 中所有命中文章，之后每次只推新增的，不会重复。

**Q：没收到消息怎么办？**  
A：进入仓库 `Actions` 页面查看当天运行日志，绿色 ✅ 表示正常，红色 ❌ 表示出错，把报错内容截图发给我排查。

**Q：DeepSeek 调用失败会影响推送吗？**  
A：不会。AI 总结是可选项，调用失败会跳过，论文标题和链接照常推送。

**Q：免费额度够用吗？**  
A：Server酱 免费版每天 5 条，对每日 1 条 digest 完全够用。DeepSeek 每月花费通常不超过 ¥1。

---

## 🔒 隐私说明

- 所有敏感信息（SendKey、API Key）均通过 GitHub Secrets 存储，不会出现在代码里
- 建议将仓库设为 **Private**（私有），避免他人看到你的配置

---

## 🙏 依赖项目

- [feedparser](https://github.com/kurtmckee/feedparser)
- [Server酱](https://sct.ftqq.com)
- [DeepSeek API](https://platform.deepseek.com)
- [GitHub Actions](https://github.com/features/actions)

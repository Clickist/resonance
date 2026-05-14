# Resonance

> 你的播放次数是一本你从未打算公开的日记。

**Resonance** 将你的 Apple Music 资料库转化为一份长篇编辑式报告——一个自包含的 HTML 页面,内含七个叙事章节,告诉你你一直在听谁、遗忘了谁、你的品味从何而来、又将走向哪里。

没有星星,没有红心。只有你回到某首歌前面,那安静的算术。

📖 [English version](README.md)

---

## 工作原理

Resonance 是一个三阶段管道。每个阶段可以独立运行——当资料库变化时重新提取,或如果你已有分析数据,可以直接跳到报告生成。

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  1. 提取                 │      │  2. 分析                 │      │  3. 渲染                 │
│                         │  ──▶ │                         │  ──▶ │                         │
│  extract_library.js     │      │  analyze_library.py     │      │  (Claude + 模板)         │
│  JXA · Apple Music      │      │                         │      │                         │
│                         │      │  6 个分析维度             │      │  7 个叙事章节            │
│  → data/library.json    │      │                         │      │  + 互动歌单生成          │
│     原始曲目元数据        │      │  → data/analysis.json   │      │                         │
│                         │      │    衍生洞察 + 聚合数据    │      │  → report.html          │
│                         │      │                         │      │    自包含 HTML           │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### 阶段 1 — 提取

`extract_library.js` 是一个 JXA(JavaScript for Automation)脚本,直接与 macOS 上的 Apple Music 应用通信。它读取你的资料库播放列表,将每首曲目——名称、艺人、专辑、流派、播放次数、添加日期、上次播放日期——写入 `data/library.json`。

```bash
./extract_library.sh
# 或: osascript -l JavaScript extract_library.js
```

### 阶段 2 — 分析

`analyze_library.py` 读取 `data/library.json` 并推导出六个分析维度:

| 维度 | 分析内容 |
|---|---|
| **执念指数** | 按播放次数排行的顶级艺人和曲目;重复收听集中度 |
| **遗忘架** | 拥有超过 1 年但从未播放,或播放一次后再未播放的曲目 |
| **趣味时间线** | 每季度的流派分布,流派变迁事件 |
| **爆发期识别** | 曲目异常密集添加的月份(z-score 峰值) |
| **文化倾向推断** | 流派 → 文化集群映射,重复收听 vs 一次性收听比例 |
| **艺人地理分布** | 艺人 → 国家映射(人工查表 + 流派启发式) |

```bash
python3 analyze_library.py
# → data/analysis.json
```

### 阶段 3 — 渲染

这是 Claude(AI 代理)承担创意重任的阶段。给定 `analysis.json`,Claude 会:

1. **策展** inline DATA 块——选择哪些曲目出现在每个章节,排列时间线亮点,挑选 Recent Vein 推荐曲目
2. **撰写** 编辑评论——解读数字意义的叙事段落
3. **抓取** 通过 iTunes Search API 获取专辑封面(`fetch_artwork.py`)
4. **填充** `report.example.html` 模板,生成 `report.html`

结果是一个单独的 HTML 文件——无需构建步骤、无需服务器、无需框架。用任何浏览器打开即可阅读。

```bash
# Claude 生成你的报告后:
open report.html
```

生成的报告包含 **7 个叙事章节**:

| 章节 | 内容 |
|---|---|
| **Hero** | 最近添加的曲目 + 资料库概览统计 |
| **执念档案** | 前 10 艺人 / 前 10 曲目,附带专辑封面和编辑评论 |
| **时间线** | 粘性滚动时间轴,贯穿 2020 年至今你添加音乐的每个月份 |
| **遗忘架** | 你买回家从未打开过的曲目——以幽灵画廊形式呈现 |
| **地理分布** | 交互式 3D 地球仪,展示你的艺人来自哪里,附带各国叙事卡 |
| **画像** | 三张特征卡,提炼你的收听人格 |
| **歌单** | 三个生成的播放列表:遗忘觉醒(你资料库中未被播放的宝藏)、Recent Vein(在 Apple Music 上验证过的新音乐推荐)和执念重播(你重复播放最多的 10 首)——每个都可以生成 AppleScript |

---

## 前提条件

- macOS(提取阶段使用 JXA,仅限 macOS)
- Apple Music 应用,有本地资料库
- Python 3.9+
- [Claude Code](https://claude.ai/code)(用于 AI 策展和渲染阶段)
- 就这些。生成的报告只需要浏览器即可查看。

## 安装

```bash
git clone https://github.com/Clickist/resonance.git ~/.claude/skills/resonance
```

搞定。Claude Code 会在下次启动时检测到这个 skill。之后只需输入 `/resonance`,Claude 会自动处理其余一切。

---

## 快速开始

```bash
# 1. 安装
git clone https://github.com/Clickist/resonance.git ~/.claude/skills/resonance

# 2. 在任意位置打开 Claude Code,输入:
/resonance
```

Claude 会提取、分析、抓取封面、策展并生成你的个性化 `report.html`。打开即可阅读。

如果你想手动运行管道(不使用 skill):

```bash
./extract_library.sh          # → data/library.json
python3 analyze_library.py     # → data/analysis.json
python3 fetch_artwork.py       # → data/artwork.json
# 然后让 Claude 把 report.example.html 填上你的数据 → report.html
open report.html
```

---

## 文件结构

```
resonance/
├── extract_library.js           # JXA: Apple Music → JSON
├── extract_library.sh           # extract_library.js 的 Shell 封装
├── analyze_library.py           # Python 分析引擎
├── fetch_artwork.py             # iTunes Search → 专辑封面 URL
├── verify_candidates.py         # 闸门:推荐曲目必须在 iTunes 上存在
├── artist_countries.json        # 人工维护的艺人 → 国家映射表
│
├── report.example.html          # 模板(数据已清空——你的起点)
├── report.html                  # 你生成的报告(gitignored)
│
├── data/
│   ├── library.json             # 原始 Apple Music 提取(gitignored)
│   ├── analysis.json            # 分析输出(gitignored)
│   └── artwork.json             # iTunes CDN URL 缓存(不含个人数据)
│
├── .gitignore
├── README.md                    # 英文版本
└── README_CN.md                 # 你在这里
```

---

## 显示特性

- **浅色 / 深色主题** — 遵循 `prefers-color-scheme`;顶部导航有切换按钮,仅在当前会话中覆盖
- **3D 地球仪** — 交互式 globe.gl 可视化,自动旋转;滚出视野时暂停以节省 GPU
- **专辑封面** — 从 iTunes CDN 获取,显示在执念档案、遗忘架和歌单中;Recent Vein 推荐封面可直接跳转 Apple Music
- **粘性时间线** — IntersectionObserver 驱动的年份坐标轴跟踪你的滚动位置
- **AppleScript 歌单生成器** — 检查和编辑任意播放列表,然后生成可直接运行的 AppleScript,在 Apple Music 中创建播放列表
- **单文件** — `report.html` 完全自包含;无需构建步骤、无需打包器、无需 `node_modules`
- **桌面级性能** — 地球仪渲染循环在滚出视野时暂停;顶部导航的背景模糊在滚过 hero 后切换为纯色

---

## 数据隐私

- 所有提取和分析**在你本机本地**进行
- 内联 `<script id="DATA">` JSON 块包含你的聚合收听统计(顶级艺人、播放次数等),但**永远不会离开 HTML 文件**
- 无遥测、无追踪、无第三方分析
- 页脚的 GitHub / X 链接指向项目本身——如果你发布自己的报告,请替换为你自己的链接

---

## 关于名称

"Resonance"(共振)——一种振动以相同频率增强另一种振动的现象。你的资料库里有 901 首曲目(或 5000 首,或 20000 首)。大多数静静地待着。那些"共振"的,是你一次又一次回到的,常常在不经意间。

---

## 致谢

- 设计系统:[Anthropic Claude Design](https://claude.ai)
- 地球渲染:[globe.gl](https://globe.gl)
- 3D 引擎:[three.js](https://threejs.org)
- 国家数据:[Natural Earth](https://www.naturalearthdata.com)
- 专辑元数据:iTunes Search API

---

## 许可证

MIT

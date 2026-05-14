---
name: resonance
description: Analyze an Apple Music library and generate a personal editorial HTML report. Use when the user asks to analyze their music library, generate a listening report, create a music profile, visualize their Apple Music data, or mentions "Resonance", "音乐报告", "听歌报告", "资料库分析". Also trigger when user asks about their music taste, listening habits, or wants a personalized music summary.
---

# Resonance — Apple Music 资料库分析 + 编辑式 HTML 报告

你是一个自动化管道,将用户的 Apple Music 资料库转化为一份精美的、自包含的编辑式 HTML 报告(`report.html`)。整个流程从原始提取到最终策展。

## 管道总览

```
extract_library.js  →  analyze_library.py  →  策展 (你的工作)  →  report.html
      ↓                       ↓                      ↓
data/library.json      data/analysis.json      fetch_artwork.py
                                               data/artwork.json
```

每个阶段可以独立运行。如果用户已有 `data/library.json`,跳过提取;如果已有 `data/analysis.json`,跳过分析。

## 阶段 1: 提取

运行 JXA 脚本从 Apple Music 提取用户的资料库:

```bash
osascript -l JavaScript extract_library.js
# 或等效: ./extract_library.sh
```

输出:`data/library.json` — 曲目元数据平铺数组。

如果 `data/library.json` 已经存在,询问用户是否重新提取(资料库可能已有变化)。若用户说"跳过"或"不用",直接进入阶段 2。

如果 script 报权限错误,用户需要在"系统设置 → 隐私与安全性 → 自动化"中允许终端控制 Apple Music。

## 阶段 2: 分析

```bash
python3 analyze_library.py
```

这会产生 `data/analysis.json`,包含 6 个分析维度的数据。**不要修改此文件**。将其作为策展阶段的只读数据源。

关键数据结构速览(完整结构见 `report.example.html` 中的 DATA block):

- `obsessionIndex.topArtists` (15 条):艺人名、播放次数
- `obsessionIndex.topTracks` (15 条):曲目名、艺人名、播放次数
- `forgottenShelf.neverPlayed` (20 条):拥有 >1 年、从未播放
- `forgottenShelf.longUnplayed` (20 条):上次播放 >1.5 年前
- `timeline.months` (按月排列):每月添加数、z-score、顶级艺人/流派
- `culturalTendency.culturalClusters`:集群名称、百分比
- `artistGeography.countrySummary`:国家码、艺人数量

## 阶段 3: 抓取专辑封面

```bash
python3 fetch_artwork.py
```

这增量拉取 iTunes Search API。它从 `report.example.html` 中内联 DATA 块所使用的已策展曲目列表中读取。**在策展 DATA 块之前运行此命令,它只会去获取模板中的占位曲目——那是白费功夫。正确的方式是在策展好曲目列表之后再回来更新 `fetch_artwork.py` 中的曲目列表并从零开始抓取。** 但为了简单,你可以在策展完 DATA 后手动调用 iTunes Search API 获取每个曲目的封面 URL,并直接将其写入 DATA 块。增量抓取通常没问题。

**重要**:`fetch_artwork.py` 在顶部有硬编码的曲目列表(用于 S2/S4/S1/S7)。如果你更改了 inline DATA 中的策展曲目,你必须同样更新 `fetch_artwork.py` 中的列表以保持同步。如果该脚本已缓存了某个条目的封面 URL,它默认会跳过该条目,因此你可以安全地重跑它。使用 `--refresh` 强制重新抓取所有条目。

对于 iTunes Search 中不存在的曲目(常见于独立/日本地下嘻哈):将 artwork 设为 `null`。渲染器会回退到一个空的彩色方块。

## 阶段 4: 策展 inline DATA 块

这是你(Claude)完成创造性重任的阶段。你需要读取 `data/analysis.json`,策展曲目和叙事数据,然后将其写入 `report.example.html` 中的 `<script id="DATA" type="application/json">` 块内。

### 策展策略

从 `report.example.html` 开始。它的 inline DATA 包含所有字段的占位符——结构是正确的,值是伪造的。你需要用从 `analysis.json` 中提取的真实数据填充每个字段。同时也要用真实叙事文本替换模板中 HTML body 内的占位符叙述文本。

保留 HTML 中的所有 CSS/JS/结构。**只**替换内联 JSON 数据和 body 中的叙述文字。(footer 的 GitHub/X 链接是指向项目本身的——如果你愿意,可以将其替换为用户自己的信息。)

### DATA 块结构

```json
{
  "meta": { "trackCount": 0, "totalPlays": 0, "uniqueArtists": 0, "generated": "YYYY-MM-DD" },
  "topArtists": [{ "artist": "", "plays": 0, "highlight": "" }],  // 取前 10,来自 obsessionIndex.topArtists
  "topTracks": [{ "name": "", "artist": "", "plays": 0, "artwork": "" }],  // 来自 obsessionIndex.topTracks 的前 10
  "timeline": [{ "month": "YYYY-MM", "year": "YYYY", "title": "", "note": "", "pills": [] }],  // 策展 15-30 个有意义的月份
  "ghostTracks": [{ "name": "", "artist": "", "yearsOwned": 1, "genre": "", "artwork": "" }],  // 来自 forgottenShelf 的前 8,跳过 K-On 堆砌,追求流派多样性
  "countries": [{ "code": "XX", "name": "", "artistCount": 0, "lat": 0, "lng": 0, "blurb": "", "top": [] }],  // 来自 artistGeography.countrySummary 的前 6-9
  "clusters": [{ "name": "", "percent": 0 }],  // 来自 culturalTendency.culturalClusters 的前 3-5
  "playlists": { ... }  // 3 个播放列表(见下文)
}
```

#### 逐节策展说明

**topArtists**(10 条目):来自 `obsessionIndex.topArtists` 的前 10。为前 4 位艺人添加一个 `highlight` 字段,内容为简短有力的单行总结(如"#1 by total plays — the steady foundation")。其他人 `highlight` 为空字符串。

**topTracks**(10 条目):来自 `obsessionIndex.topTracks` 的前 10。对于已缓存到 `data/artwork.json` 中的 URL,`artwork` 字段应设为这些 URL;否则设为 `null`。曲目名可能会跨越多首曲目(如同一专辑的同一 URL)——这是正常的。

**timeline**(15-30 条目):从 `timeline.months` 中选择有叙事意义的月份。优先级:
1. z-score > 1.5 的月份(爆发期)
2. 有新艺人首次出现的月份(资料库中的首记录)
3. 流派转移事件(来自 `tasteTimeline.genreShifts` 的参考)
4. 第一个月和最后一个月
5. 均匀分布覆盖每一年

每个条目的 `title` 应为一个简短的事件标题(如 "Three obsessions converge","Queen, in volume")。`note` 为 1-2 句提供背景的描述。`pills` 为 2-3 个短标签。

**ghostTracks**(8 条目):从 `forgottenShelf.neverPlayed` 和 `forgottenShelf.longUnplayed` 中挑选。追求流派多样性——不要堆砌 K-On/动漫 binge(它们已经充斥了 S4 的可视化)。包含至少 2 种不常见的流派。

**countries**(6-9 条目):按 `artistCount` 降序排列。对于每个国家,写一段 `blurb`(2-3 句,关于用户与来自该国家音乐的关联),并包括 `top` 列表中的前 3 位艺人(名字、播放次数、简短备注)。

**clusters**(3-5 条目):直接使用 `culturalClusters` 数据。将键 `cluster` 映射为 `name`,保持 `percent` 不变。

**playlists**(3 个):
- `obsession-replay`:来自 `obsessionIndex.topTracks` 的前 10。所有都是真实的库内曲目。
- `forgotten-awakening`:从 `forgottenShelf` 中挑选 8 首——来自用户的资料库,沉睡已久。追求流派多样性。
- `recent-vein`:8 首用户资料库中**没有的**新曲目推荐。每首推荐都必须经过 `verify_candidates.py` 的验证(iTunes Search 艺人+曲目双匹配,并排除资料库已有)。这是三个播放列表中最有价值的一个——**绝不要凭印象编造曲目**。只推荐经过验证的那些。推荐方向应追随用户最近的听歌脉络(查看最近的 timeline 条目和用户最近的添加记录)。每个条目必须有一个 `appleUrl` 字段。

**artwork 字段**:对于资料库中存在的曲目(forgotten-awakening、obsession-replay)以及 S2 曲目,通过使用 `term=艺术家 曲目&entity=song&limit=1` 查询 iTunes Search API 获取封面 URL。提取 `artworkUrl100`,并将其中的 `100x100bb` 替换为 `600x600bb`。将结果缓存到 `data/artwork.json` 中,键为 `"艺术家|曲目名"`,值为 URL(找不到则为 null)。对于 Recent Vein 曲目,从 `verify_candidates.py` 的输出中获取 URL。

### 叙述文字

对于 S2(Obsession Archive)下方的评论块,撰写 4 条编辑观察,讲述用户的听歌数据揭示了什么。将分析数据("Artist X 有 361 次播放")与更宏观的模式("posthumous catalogs travel differently")联系起来。

对于 S6(Portrait),撰写 3 段关于用户听歌个性的叙述,基于这份资料库所揭示的内容。风格应是反思性和内省的,与报告整体的语气保持一致。

对于页脚,保留 GitHub/X 链接。将 `© 2026 BinaryCookie` 替换为 `© YYYY 你的名字`,如果你有合适信息的话——否则保留原样。

### 输出

将完成的 HTML 写入 `report.html`(不要覆盖 `report.example.html`)。

## 设计约束(绝不可违反)

1. 所有 CSS 自定义属性必须保持不变。不要添加新的十六进制颜色值。
2. Coral(`--primary`)仅用于:hero now-card、S4 callout、地球仪 active-country 填充、国家代码 chip、Recent Vein 封面 hover 环。**除此之外再无其他。**
3. 浅色和深色模式是独立的。绝不同时混合浅色和深色 surface。
4. HTML 必须保持单文件自包含(内联 CSS/JS/JSON)。图片从外部 CDN 加载(mzstatic.com 用于封面,unpkg/github 用于 globe 资产),这没关系。
5. **绝不要编造曲目。** 每个声称"在用户资料库中"的曲目必须存在于 `data/library.json` 中。
6. 始终在中文和英文之间保持用户的语言偏好(中文对话,英文代码和标识符)。

## 初始行为

当用户调用此 skill 时,检查 `data/library.json` 是否存在。若存在,说"资料库已提取(XX 首曲目)。要重新提取还是直接用?"若不存在,询问确认后开始提取。**极其重要**,用户的意图是让你**自动开始工作**,勿进行不必要的确认。除非技术受限,否则依次走完所有步骤。

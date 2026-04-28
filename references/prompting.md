# Gemini TTS 进阶提示词指南（Director's Chair Prompting）

Gemini 3.1 Flash TTS 与传统 TTS 最大的区别：它由 LLM 驱动，**能"理解"风格描述**而不只是机械朗读。这份指南教你怎么写好的 prompt，把模型当成"虚拟配音演员"来调度。

## 三个层级的 prompt 复杂度

### Level 1：极简风格指令（适合 1-2 句台词）

```
Say cheerfully: 祝你今天过得愉快！
```

```
Say in a spooky voice: 黑夜中，他听见了脚步声。
```

特点：一行解决，结构清晰，不容易被 prompt classifier 误读。

### Level 2：简化导演式（推荐用于段落级别）

```
You are a calm and warm documentary narrator.
Speak slowly, with measured pacing and a gentle British accent.

Now read the following script:
"In the dense canopy of the Amazon, a thousand species awaken at dawn..."
```

特点：包含 Profile + Style + Pacing + Accent + Transcript 的精简版本，约 80% 场景够用。

### Level 3：完整导演式（适合复杂表演场景）

参考 Google 官方示例：

```
# AUDIO PROFILE: Jaz R.
## "The Morning Hype"

## THE SCENE: The London Studio
It is 10:00 PM in a glass-walled studio overlooking the moonlit London skyline,
but inside, it is blindingly bright. The red "ON AIR" tally light is blazing.
Jaz is standing up, not sitting, bouncing on the balls of their heels to the
rhythm of a thumping backing track.

### DIRECTOR'S NOTES
Style:
* The "Vocal Smile": You must hear the grin in the audio. The soft palate is
always raised to keep the tone bright, sunny, and explicitly inviting.
* Dynamics: High projection without shouting. Punchy consonants and elongated
vowels on excitement words (e.g., "Beauuutiful morning").

Pace: Speaks at an energetic pace, keeping up with the fast music. Speaks
with a "bouncing" cadence. High-speed delivery with fluid transitions —
no dead air, no gaps.

Accent: Jaz is from Brixton, London.

### SAMPLE CONTEXT
Jaz is the industry standard for Top 40 radio, high-octane event promos.

### TRANSCRIPT
[excitedly] Yes, massive vibes in the studio! You are locked in and it is
absolutely popping off in London right now. [shouting] Turn this up!
```

## 完整结构的 6 个组成部分

### 1. Audio Profile（角色身份）

给角色取名 + 一句 archetype 概括，能让模型把"演出"做得更具一致性。

```
# AUDIO PROFILE: Monica A.
## "The Beauty Influencer"
```

```
# AUDIO PROFILE: Captain James Hartwell
## "Retired Royal Navy Officer"
```

**为什么有效**：模型学过大量"角色 → 表演特征"的语料，给一个具体身份（DJ / 影响者 / 退役军官）比抽象描述（"开朗女声"）唤起更精准的演技。

### 2. Scene（场景设定）

描述地点 + 氛围 + 角色当时的状态：

```
## THE SCENE: Late-night radio studio in Tokyo
It's 2:47 AM. Rain is streaming down the window beside the booth. The host
is alone, leaning toward the mic with their hands wrapped around a cooling
cup of tea. The studio is dimly lit, with only the warm glow of the on-air
sign for company.
```

**为什么有效**：场景把"为什么这样说话"的动机给到模型——深夜独白自然就慢、就轻、就近距离麦克风。

### 3. Director's Notes（导演备注）

最关键的部分。包含三大要素 + 任意补充：

#### Style（风格 / 演法）

| 抽象（不推荐） | 具体（推荐） |
|---------------|-------------|
| Energetic | "Infectious enthusiasm. The listener should feel like they're part of a massive event." |
| Sad | "Restrained grief. Words come out softly, with small pauses where breath catches." |
| Confident | "Quiet confidence — no need to push, the authority is already established." |

行业术语也能用，比如 "vocal smile"、"chest voice"、"forward placement"——模型大多能理解。

#### Pacing（节奏）

| 简单 | 进阶 |
|------|------|
| "Speak slowly" | "Deliberate pacing with extra space between sentences for the listener to absorb." |
| "Fast" | "Rapid-fire delivery, no dead air, like a salesperson in flow." |
| "Variable" | "Slow and weighty for the setup, accelerating into excitement at the punchline." |

#### Accent（口音）

越具体越好：

| 模糊 | 精确 |
|------|------|
| "British accent" | "Received Pronunciation, like a BBC newsreader from the 1990s" |
| "American" | "Mid-Atlantic accent of a 1940s film star" |
| "Southern" | "Slow Texan drawl from rural East Texas" |

> 文档原话：**"Accents should be triggered by style prompts, not by the language setting."**

#### 自由补充

补充演员需要注意的细节：

```
Breathing: Audible breath intake before key emphasis words.
Smile: Maintain a slight smile throughout for warmth.
Inflection: Rising tone at the end of statements (uptalk).
```

### 4. Sample Context（上下文起点）

给一个"角色刚才在做什么 / 接下来要说这段话的情境"，帮模型自然进入：

```
### SAMPLE CONTEXT
Anya has just looked up from her notes after listening to a caller's question
about climate policy. She takes a thoughtful breath before answering.
```

### 5. Transcript（台词本身）

**关键陷阱**：必须用清晰的分隔让模型知道"哪里开始是要念出来的台词"，否则 prompt classifier 可能把上面的导演备注也当成台词读出来。

✅ 推荐做法：
```
### TRANSCRIPT

"In the heart of the city, where neon meets shadow..."
```

或：
```
Read the following speech aloud:

"In the heart of the city, where neon meets shadow..."
```

### 6. Audio Tags（内嵌精细控制）

在 transcript 中插入 `[whispers]`、`[short pause]`、`[laughs]` 等标签做局部微调。详见 `audio_tags.md`。

```
### TRANSCRIPT

I know right, [sarcastically] I couldn't believe it. [whispers] She should
have totally left at that point. [cough] Well, [sighs] I guess it doesn't
matter now.
```

## 提示词的"对齐原则"（最重要的一条）

文档原话：**"The style prompt, the text content, and any tags should all point in the same direction."**

也就是说：
- ✅ 风格 = scared，台词 = "I just heard a window break"，标签 = `[trembling]` —— 一致
- ❌ 风格 = scared，台词 = "Today's weather is lovely"，标签 = `[panicked]` —— 矛盾，模型会输出怪怪的折中

写 prompt 时三个都改，不要只改一个。

## 不要过度规定（Don't Overspecify）

文档另一条原则：**"Don't overspecify. The model fills in gaps naturally."**

- ❌ 把每句话的每个词的语调都标出来 → 反而僵硬
- ✅ 给一个清晰的整体方向 + 几个关键节点的标签 → 自然流畅

类比：你跟一个好演员说"你是个累了一天的母亲，刚发现孩子还没睡，语气想发火又心疼"——这一句话他/她就能演出戏。如果你逐字标"这里高一点、那里停 0.3 秒"，反而约束了表演。

## 多角色场景的 prompt 设计

双角色对话时，最好给每个角色一段独立的 director's note：

```
The following is a conversation between Speaker1 (Anya) and Speaker2 (Liam).

Make Anya sound tired and contemplative, speaking slowly with frequent pauses.
Make Liam sound excited and curious, with rapid-fire questions.

Anya: [tired] So... [yawn] you really want to talk about herpetology at this hour?
Liam: [excited] Yes! Did you know there's a frog that can survive being frozen?
```

注意：脚本里"Anya:" "Liam:" 的名字必须与 API 的 `speakers` 参数中 `name` 字段**完全一致**。

## 完整模板（拿来就改）

下面这个模板适合直接复制修改：

```
# AUDIO PROFILE: [角色名]
## "[一句话身份概括]"

## THE SCENE: [一句话地点]
[2-3 句场景细节，包括时间、氛围、角色此刻状态]

### DIRECTOR'S NOTES
Style: [整体风格描述]
Pace: [节奏说明]
Accent: [口音说明]

### TRANSCRIPT

"[实际台词，可以含 [audio tags]]"
```

## 中文场景的本地化建议

虽然 prompt 主体用英文（模型对英文指令最敏感），台词可以是中文。混合写法示例：

```
You are a warm Chinese audiobook narrator named Lin Yi. Speak slowly with
emotional warmth, like reading a bedtime story to a child. Pause briefly
between sentences.

Read the following passage aloud:

"夜色已深，[short pause] 月光透过窗棂洒在书页上。[sighs] 老人合上书，
轻声说道：[whispers] 故事还没结束。"
```

## 调试 prompt 的优先级

当输出不满意时，按这个优先级调整：

1. **检查台词内容是否支持目标情绪**（最容易被忽略的一点）
2. **明确分隔指令与台词**（避免被读出来）
3. **加 1-2 个关键音频标签**（局部微调）
4. **改 director's notes**（整体方向）
5. **换声音**（最后的手段，因为风格 prompt 比声音名能解决更多问题）

## 常见错误样本

❌ **指令被当成台词读出来**：
```
calm narrator slow pacing
In the dense canopy of the Amazon...
```
模型可能输出："Calm narrator slow pacing in the dense canopy of the Amazon..."

✅ 正确分隔：
```
You are a calm narrator. Read slowly. Now read the following:

"In the dense canopy of the Amazon..."
```

---

❌ **prompt 与声音矛盾**：
- 选了 Algenib (Gravelly)，prompt 写 "young cheerful girl" → 模型挣扎
- 文档警告："To avoid mismatched tones (such as a deep male voice attempting to speak like a young girl), ensure your prompt's written tone and context align naturally with the selected speaker's profile."

✅ 选 Leda (Youthful) 配 "young cheerful girl"

---

❌ **过度具体**：
```
Stress the word "happy" with rising intonation. Pause for 0.4 seconds.
Slightly emphasize the second syllable of "amazing"...
```

✅ 抽象方向：
```
Energetic and infectious enthusiasm, with natural emphasis on positive words.
```

## 把 Gemini 当 prompt 写作助手

文档建议："**Have Gemini help you build your prompt**, just give it a blank outline of the format below and ask it to sketch out a character for you."

如果你（Claude）自己也卡壳，可以这样思考：模拟一个剧本指导写性格描述——"这个角色是谁？他/她现在在哪？心情怎样？语速会快还是慢？"——把答案串成 prompt 就成了。

# Gemini TTS 音频标签（Audio Tags）完整参考

Gemini 3.1 Flash TTS 支持 **200+** 内联音频标签来精细控制语音表现。Google 没有公布完整列表，**鼓励创造性使用**。本文档梳理已知的可靠标签 + 实战使用模式。

## 基本规则

1. **格式**：`[tag]` —— 必须用方括号包裹
2. **位置**：插入到希望产生效果的位置（前置作用于后续整段，或局部插入作用于附近）
3. **间距**：标签前后**必须有文字或标点**，**不要**把两个标签紧挨着写：
   - ❌ `[whispers][sad] hello` 
   - ✅ `[whispers] [sad] hello`（仍然不推荐）
   - ✅ `[whispers] hello, [sad] sorry`（推荐）
4. **语言**：标签**只用英文**——这是文档的明确建议。可以与中文/日文等台词混用：
   ```
   [excitedly] 大家好！[short pause] 今天天气真不错。
   ```
5. **口音控制**：用风格 prompt 描述（"London Cockney accent"），**不要**靠 BCP-47 language code 强切

## 已验证可用的标签（按用途）

### 情绪类（Emotions）

放在句子开头，作用于整句：

| 标签 | 效果 |
|------|------|
| `[excited]` / `[excitedly]` | 兴奋、激动 |
| `[happy]` | 开心 |
| `[sad]` | 悲伤 |
| `[angry]` | 愤怒 |
| `[bored]` | 无聊、提不起劲 |
| `[reluctantly]` | 勉强、不情愿 |
| `[amazed]` | 惊叹 |
| `[curious]` | 好奇 |
| `[serious]` | 严肃 |
| `[mischievously]` | 调皮、淘气 |
| `[sarcastic]` / `[sarcastically]` | 讽刺 |
| `[panicked]` | 慌张 |
| `[trembling]` | 颤抖 |
| `[tired]` | 疲惫 |
| `[crying]` | 哭腔 |
| `[fearful]` / `[scared]` | 恐惧 |
| `[disgusted]` | 厌恶 |
| `[surprised]` | 惊讶 |
| `[cautious]` | 谨慎 |
| `[confident]` | 自信 |
| `[nervous]` | 紧张 |

### 音量类（Volume）

| 标签 | 效果 |
|------|------|
| `[whispers]` / `[whisper]` | 低声、私语 |
| `[shouting]` / `[shouts]` | 喊叫 |
| `[loud]` | 大声 |
| `[quiet]` | 小声（比 whispers 略大） |

### 语速 / 节奏类（Pacing）

| 标签 | 效果 |
|------|------|
| `[very fast]` | 极快 |
| `[fast]` | 快速 |
| `[very slow]` | 极慢 |
| `[slow]` | 缓慢 |
| `[short pause]` | 短停顿 |
| `[long pause]` | 长停顿（少数情况下识别为 [pause]） |

### 非言语声音（Non-verbal）

直接当作"声音事件"插入，会被合成为对应的人声效果：

| 标签 | 效果 |
|------|------|
| `[sighs]` / `[sigh]` | 叹气 |
| `[gasp]` / `[gasps]` | 倒吸气 |
| `[laughs]` / `[laugh]` | 大笑 |
| `[giggles]` | 咯咯笑 |
| `[chuckles]` | 轻笑 |
| `[cough]` / `[coughs]` | 咳嗽 |
| `[clears throat]` | 清嗓子 |
| `[yawn]` / `[yawns]` | 打哈欠 |
| `[hums]` | 哼唱 |
| `[sniffs]` | 抽鼻子 |
| `[snorts]` | 哼鼻子（笑） |

### 角色化 / 模仿类（Persona Imitation）

文档示例显示这类创造性标签也能识别：

| 模式 | 示例 |
|------|------|
| `[like a XXX]` | `[like a cartoon dog]`、`[like dracula]`、`[like a news anchor]`、`[like a wise old man]` |
| `[in a XXX voice]` | `[in a robotic voice]`、`[in a british accent]`、`[in a child-like voice]` |
| 复合风格 | `[sarcastically, one painfully slow word at a time]` |

> 这类标签是 Gemini 比传统 TTS 强很多的地方——可以临时切换"演法"。

## 组合使用模式

### 模式 1：前置情绪 + 内嵌停顿

```
[excitedly] 我有个超棒的消息要告诉你！[short pause] 你绝对猜不到！
```

### 模式 2：分段切换

```
[whispers] 那个秘密一直藏在这里。
[shouting] 但今天，我要把它告诉全世界！
[whispers] 你准备好了吗？
```

### 模式 3：复合风格描述

把多个修饰词放在一个标签里：

```
[sarcastically, slowly] 哦——这——真——是——好——极——了。
```

```
[whispering, scared, trembling] 它…它就在那扇门后面…
```

### 模式 4：非言语 + 台词无缝衔接

```
[laughs] 哈哈哈，这太搞笑了！[sighs] 不过说真的，我累了。
```

## 创造性标签实验

文档原话："There is no exhaustive list on what tags do and don't work, **we recommend experimenting**."

可以大胆尝试这类描述性标签（出错最差就是被忽略）：

- `[like a dramatic shakespeare actor]`
- `[in a theatrical british accent]`
- `[muttering under breath]`
- `[as if telling a bedtime story]`
- `[in a sleepy morning voice]`
- `[announcing as a sports commentator]`
- `[in a sing-song voice]`
- `[barely holding back tears]`

## 经验法则

1. **少即是多**：一段 30 秒的台词用 2-4 个标签足够，标签太多反而让模型困惑。
2. **标签 + 内容要一致**：`[scared]` 配合的台词内容也要有惧怕的感觉，不要 `[scared] 今天天气真好` 这种矛盾组合——文档原话："The style prompt, the text content, and any tags should all point in the same direction."
3. **用富有情感的台词内容**：`"I just heard a window break"` 比 `"Something happened"` 更能激发逼真的恐惧感。
4. **非言语不要塞太密**：连续三个 `[sigh]` 会很假；隔几句一个最自然。
5. **优先用通用标签**：常见标签（whispers/excited/laughs 等）成功率最高；冷僻创造性标签可能被忽略，但不会报错——值得一试。
6. **跨语言注意**：中文台词混英文标签时，标签影响不会丢失，但口音 / 节奏的细节会受底层声音特质更大影响。

## 常见错误

❌ 两个标签连写：
```
[excited][whispers] hello
```
✅ 中间加文字或换标签：
```
[excited] Hello! [whispers] Listen carefully.
```

❌ 标签放在词中间：
```
he[laughs]llo
```
✅ 标签放在词与词之间：
```
[laughs] hello
```

❌ 中文标签：
```
[兴奋地] 大家好！
```
✅ 英文标签：
```
[excitedly] 大家好！
```

❌ 标签和台词矛盾：
```
[crying] 哈哈哈这真好笑！
```
✅ 一致：
```
[laughs] 哈哈哈这真好笑！
```

## 调试建议

如果生成出来的语音情绪不到位：
1. 先确认标签拼写正确、用了英文方括号 `[]` 而不是中文 `【】`
2. 检查台词内容是否支持目标情绪（"I'm so happy" 比 "I'm here" 更适合 [excited]）
3. 检查标签前后有没有文字 / 标点分隔
4. 试试复合标签 `[scared, trembling, whispering]` 替代单个 `[scared]`
5. 升级到风格 prompt 控制——标签是局部的微调，整体气质还是 prompt 决定

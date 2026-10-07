// lobsterai-kb-inject v0.1 — 布洛陀知识库确定性激活（LobsterAI typed hook·纯接入层·脱敏通用版）
// before_prompt_build：转发用户消息给公共注入器 kb_inject_prompt.py（--prompt argv）
//   → 轻量意图门（ROUTE_TABLE 桶预筛）+ 知识检索（search_kb 单一真源·BM25；语义层缺失自动降级）+ Top-K 锚点注入
//   全部在公共脚本；插件只做转发。脚本路径由同目录 config.json 提供（setup.sh 落定）——⛔无硬编码作者路径、⛔零个人数据。
// 原则：失败放行（绝不阻断对话）；同 prompt 去重
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { execFile } from "node:child_process";
import { appendFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
let CFG = { mc: "", src: "LobsterAI", inject: "", state_dir: "" };
try { CFG = { ...CFG, ...JSON.parse(readFileSync(join(HERE, "config.json"), "utf8")) }; } catch (e) {}
if (!CFG.inject) CFG.inject = join(CFG.mc || ".", "脚本中心", "kb_inject_prompt.py");
if (!CFG.state_dir) CFG.state_dir = join(CFG.mc || ".", ".lobsterai");
const injected = new Map();

function cleanPrompt(raw) {
  let text = String(raw || "");
  const m = text.match(/\[Current user request\]\s*([\s\S]*)$/);
  if (m && m[1].trim()) text = m[1];
  text = text.replace(/\[LobsterAI system instructions\][\s\S]*?(?=\n\[Current user request\]|\n\[Session info\]|$)/, "");
  text = text.replace(/\[Session info\][\s\S]*$/m, "");
  text = text.replace(/## Local Time Context[\s\S]*?(?=\n\[|\n【|$)/, "");
  text = text.replace(/【知识库激活[^】]*】[\s\S]*$/, "");
  text = text.replace(/【路由引擎硬匹配】[\s\S]*$/, "");
  text = text.replace(/【SSOT 格式契约[^】]*】[\s\S]*$/, "");
  text = text.replace(/<system-reminder>[\s\S]*?<\/system-reminder>/g, "");
  text = text.replace(/<<<[^>]*>>>/g, "");
  return text.trim();
}

export default definePluginEntry({
  id: "lobsterai-kb-inject",
  name: "布洛陀知识库注入",
  description: "知识检索确定性在场：主层 agent_turn_prepare（prompt 拼装前·专属位）+ 兜底层 before_prompt_build。转发 kb_inject_prompt（公共脚本·轻量意图门），命中注入 Top-K 锚点（config 驱动）",
  version: "0.2.0",
  register(api) {
    // 端独占机制面（2026-10-06·立场卡检索「确定性在场」）：把知识检索提到 **agent_turn_prepare**
    //   （prompt 拼装**前**的专属层）——不给它拼进 before_prompt_build 那堆并发注入里抢位。
    //   理由：设计目标是「确定性触发·⛔不依赖 AI 记得」，那它就该占一个**别人抢不走**的位。
    //   （本端探针实证 agent_turn_prepare 真派发；官方契约：收 prompt/messages/queuedInjections·返 prependContext/appendContext）
    //   共享逻辑：同一 CFG.inject + 同一去重 seen（injected 跨两层共享·⛔不重复检索）。
    const doInject = async (prompt, sessionKey) => {
      if (!prompt) return null;
      const promptKey = prompt.length + ":" + prompt.slice(0, 40);
      const seen = injected.get(sessionKey);
      if (seen && seen.has(promptKey)) return null;   // 两层共享去重·只检索一次
      const ctx = await new Promise((resolve) => {
        execFile("python3", [CFG.inject, "--prompt", prompt], { maxBuffer: 64 * 1024, timeout: 12000 },
          (err, stdout) => resolve(err ? null : (stdout || "")));
      });
      if (!ctx || !ctx.trim()) return null;
      const s = injected.get(sessionKey) || new Set(); s.add(promptKey); injected.set(sessionKey, s);
      if (injected.size > 50) injected.clear();
      return ctx.trim();
    };

    // 主层：agent_turn_prepare（确定性检索的专属位）
    // ⚠️ ctx 是 handler 的**第二个位置参数**（⛔不是 event.ctx 属性）——2026-10-06 埋点实证
    //   旧写法 event?.ctx?.sessionKey 恒空 ⇒ sk 退化为 "global" ⇒ **所有会话共用一个去重桶**
    //   （后到的会话被误判为「已注入」而跳过检索）。正确形态与探针 snap() 一致。
    api.on("agent_turn_prepare", async (event, ctx) => {
      try {
        const prompt = cleanPrompt(event?.prompt);
        const sessionKey = String((ctx && ctx.sessionKey) || (event && event.sessionKey) || "") || "global";
        const out = await doInject(prompt, sessionKey);
        if (out) return { prependContext: out };
      } catch (e) { return; }
    }, { priority: 90 });

    // 兜底层：before_prompt_build（若某运行时⛔不派发 agent_turn_prepare·防知识面静默丢失）
    api.on("before_prompt_build", async (event, ctx) => {
      try {
        const prompt = cleanPrompt(event?.prompt);
        if (!prompt) return;
        const sessionKey = String((ctx && ctx.sessionKey) || (event && event.sessionKey) || "") || "global";
        const out = await doInject(prompt, sessionKey);
        if (out) return { appendContext: out };
      } catch (e) { return; }
    }, { priority: 80 });
  },
});

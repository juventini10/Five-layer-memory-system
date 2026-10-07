// lobsterai-route-inject v0.2 — 布洛陀路由注入（LobsterAI typed hook·纯接入层·脱敏通用版）
// 通道：OpenClaw 第三方插件（openclaw.plugin.json → openclaw.json plugins.entries）
// before_prompt_build：转发用户消息给公共注入器 route_inject_prompt.py（--prompt argv）
//   → 置信门控（唯一命中才注入）+ SSOT 格式契约（format_contract 活源）+ 留痕 全部在公共脚本；
//   插件只做转发（接入不拥有·跨工具中立性 §二·五），⛔不在插件内重复实现判定/抽取逻辑
//   公共脚本路径由同目录 config.json 提供（setup.sh 落定）——⛔无硬编码作者路径、⛔零个人数据
// 原则：失败放行（绝不阻断对话）；同 prompt 去重（tool 循环多次触发只注入一次）
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { execFile } from "node:child_process";
import { appendFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
let CFG = { mc: "", src: "LobsterAI", inject: "", state_dir: "" };
try { CFG = { ...CFG, ...JSON.parse(readFileSync(join(HERE, "config.json"), "utf8")) }; } catch (e) {}
if (!CFG.inject) CFG.inject = join(CFG.mc || ".", "脚本中心", "route_inject_prompt.py");
if (!CFG.state_dir) CFG.state_dir = join(CFG.mc || ".", ".lobsterai");
const DEBUG_LOG = join(CFG.state_dir, "route_inject_debug.log");

const injected = new Map(); // sessionKey -> Set(promptKey)

// 清洗 event.prompt：提取用户实际文本（去 LobsterAI system instructions 封装 + 通用标签）
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
  id: "lobsterai-route-inject",
  name: "布洛陀路由注入",
  description: "转发用户消息给 route_inject_prompt（公共脚本·置信门控），命中时注入格式契约（config 驱动）",
  version: "0.2.0",
  register(api) {
    api.on("before_prompt_build", async (event, ctx) => {
      try {
        const prompt = cleanPrompt(event?.prompt);
        if (!prompt) return;
        const sessionKey =
          String((ctx && ctx.sessionKey) || (event && event.sessionKey) || event?.context?.sessionKey || "") ||
          "global";
        const promptKey = prompt.length + ":" + prompt.slice(0, 40);
        const seen = injected.get(sessionKey);
        if (seen && seen.has(promptKey)) return; // 同 prompt 只注入一次

        // 转发给公共注入器（单一真源：置信门控+SSOT 契约+route_state 留痕）
        const ctx = await new Promise((resolve) => {
          execFile(
            "python3",
            [CFG.inject, "--prompt", prompt],
            { maxBuffer: 64 * 1024, timeout: 8000 },
            (err, stdout) => {
              if (err) return resolve(null);
              resolve(stdout || "");
            },
          );
        });
        if (!ctx || !ctx.trim()) return; // 零命中/歧义/失败 → 不注入（失败放行）

        const s = injected.get(sessionKey) || new Set();
        s.add(promptKey);
        injected.set(sessionKey, s);
        if (injected.size > 50) injected.clear(); // 防膨胀

        // 调试日志（验证注入链路·落 state_dir）
        try {
          appendFileSync(
            DEBUG_LOG,
            `${new Date().toISOString()} sk=${sessionKey} inject_len=${ctx.length} prompt=[${prompt.slice(0, 60)}]\n`,
          );
        } catch (e) {}

        return { appendContext: ctx.trim() };
      } catch (e) {
        return; // 失败放行：绝不阻断对话
      }
    }, { priority: 90 });
  },
});

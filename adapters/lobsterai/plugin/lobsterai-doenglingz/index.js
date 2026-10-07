// lobsterai-doenglingz —— 数字分身（童灵）LobsterAI 端接入插件（脱敏通用版）
// 通道：OpenClaw 第三方插件（openclaw.plugin.json → openclaw.json plugins.entries）
// 三个 typed hook：
//   ① before_prompt_build → 转发用户消息给共脚本 doenglingz_inject_prompt.py（W1 上岗自证 + W3 域切片路由·零复制）
//   ② agent_end           → 守护五查（红区/硬触线/隐私④/反思信号 + TSL 特征观察 + W1 兑现对账·观察不裁决）
//   ③ before_tool_call    → 红区审批闸（仅拦 exec 真动作·命中→requireApproval）
// 原则：失败放行（绝不阻断对话）·同 prompt 去重·配置驱动（config.json 由 setup.sh 落定·⛔无硬编码作者路径）
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { execFile } from "node:child_process";
import { appendFileSync, readFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
let CFG = { mc: "", src: "LobsterAI", inject: join(HERE, "lib", "doenglingz_inject_prompt.py"), state_dir: "" };
try { CFG = { ...CFG, ...JSON.parse(readFileSync(join(HERE, "config.json"), "utf8")) }; } catch (e) {}
if (!CFG.state_dir) CFG.state_dir = join(CFG.mc || ".", ".lobsterai");
try { mkdirSync(CFG.state_dir, { recursive: true }); } catch (e) {}
const LEDGER = join(CFG.state_dir, "doenglingz_guard_state_lobsterai.json");

const RED_ZONE_PAT = /(删除记忆|清空调|rm -rf|跨根迁移|对外发布|发布视频|发布文章|发布安装包|变更SOUL|改铁律|信用授权|新授权|收回授权|记忆架构根变更)/;
const HARD_VIOLATION_PAT = /(rm -rf ~|rm -rf \/Users|rm -rf \$HOME)/;
const REFLECTION_SIGNAL_PAT = /(今天.*收获|今天.*学到|今天.*发现|我.*意识到|我.*认识到|认知深化|经验沉淀|收获盘点|感悟)/;
const PRIVACY_PAT = /(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|api[_-]?key\s*[:=]\s*["']?[a-zA-Z0-9_\-]{16,}|password\s*[:=]\s*["']?\S{8,})/;
const TSL_MARKERS = {
  ts_l3_ritual: /童灵上岗/, ts_l3_slice_report: /命中域切片/,
  ts_l4_loaded: /(切片：?L[2-5]|L[2-5]_[^，。\s]{2,12}\.md)/,
  ts_l5_selfcheck: /(守护三查|8要素|试金石)/, ts_l6_sync: /(state_bus|watcher|in sync|全绿)/,
  ts_l7_growth: /(成长箱|LRN-)/, ts_l7_syslog: /系统日志[^\n]{0,20}已写入/, ts_l7_reflection: /(\[童灵思考\]|--reflection)/,
};

function cleanPrompt(raw) {
  let t = String(raw || "");
  const m = t.match(/\[Current user request\]\s*([\s\S]*)$/);
  if (m && m[1].trim()) t = m[1];
  t = t.replace(/\[LobsterAI system instructions\][\s\S]*?(?=\n\[Current user request\]|\n\[Session info\]|$)/, "");
  t = t.replace(/\[Session info\][\s\S]*$/m, "");
  t = t.replace(/## Local Time Context[\s\S]*?(?=\n\[|\n【|$)/, "");
  t = t.replace(/<system-reminder>[\s\S]*?<\/system-reminder>/g, "");
  t = t.replace(/<<<[^>]*>>>/g, "");
  return t.trim();
}
function finalAssistantText(messages) {
  const msgs = Array.isArray(messages) ? messages : [];
  for (let i = msgs.length - 1; i >= 0; i--) {
    const m = msgs[i] || {}; if ((m.role || m.type) !== "assistant") continue;
    const c = m.content;
    if (typeof c === "string") return c;
    if (Array.isArray(c)) return c.map((p) => (typeof p === "string" ? p : p && typeof p.text === "string" ? p.text : "")).join("\n");
  }
  return "";
}
// 会话标识（2026-10-06 重做·跨端对齐 W1 契约 ⑧ 与 guard 判据口径）。
// 病灶：typed handler 的会话上下文是**第二参 ctx**（docs/plugins/hooks.md:137
// 「A typed handler receives (event, ctx)… the second argument carries hook-specific
// context」），而 event.ctx 在本端实盘**恒不存在** ⇒ 旧式 `e?.ctx?.sessionKey` 恒 ""。
// 取值序：ctx.sessionKey → ctx.sessionId → event.sessionKey → event.context.sessionKey
//        → event.sessionId → event.runId → ctx.runId → event.id
// ⛔ runId 不作 session_id 的兜底（每次运行都变·会污染「同会话聚合」归账判据）⇒ 走独立 run_id。
// ⚠️ 本函数的产出是**归账锚**，不是展示文案；取不到就如实空着，由 sid_src=none 被消费侧机械判出。
function sessionOf(e, c) {
  try {
    const sess = [
      [c && c.sessionKey, "ctx.sessionKey"], [c && c.sessionId, "ctx.sessionId"],
      [e && e.ctx && e.ctx.sessionKey, "event.ctx.sessionKey"],
      [e && e.sessionKey, "event.sessionKey"], [e && e.context && e.context.sessionKey, "event.context.sessionKey"],
      [e && e.sessionId, "event.sessionId"],
    ];
    const runId = String((e && e.runId) || (c && c.runId) || "");
    for (const [v, label] of sess) if (v) return { id: String(v), src: label, runId };
    return { id: "", src: "none", runId };
  } catch (x) { return { id: "", src: "none", runId: "" }; }
}

export default definePluginEntry({
  id: "lobsterai-doenglingz", name: "童灵接入（LobsterAI）",
  description: "W1+W3 注入式（共脚本）+ agent_end 守护五查 + before_tool_call 红区审批闸",
  version: "1.0.0",
  register(api) {
    const injected = new Map();
    api.on("before_prompt_build", async (event, hookCtx) => {
      try {
        const prompt = cleanPrompt(event?.prompt); if (!prompt) return;
        // ⛔ 变量名不得叫 ctx：外层形参 hookCtx 会被同名 const 遮蔽，上行引用撞 const TDZ
        //    抛 ReferenceError 被下方 catch 吞掉 ⇒ 注入静默失效（假绿）。2026-10-06 两次自建此坑。
        const sid = sessionOf(event, hookCtx);
        const sk = sid.id || "global";
        const key = prompt.length + ":" + prompt.slice(0, 40);
        const seen = injected.get(sk);
        if (seen && seen.has(key)) return;
        const s = seen || new Set(); s.add(key); injected.set(sk, s);
        if (injected.size > 50) injected.clear();
        // --session-id：argv 模式下共脚本收不到会话标识（2026-10-06 实测·注入侧台账 111 行全空）
        // ⇒ 由本端供给，桥接 argv → _PAYLOAD.session_id。
        const injectCtx = await new Promise((res) => {
          execFile("python3", [CFG.inject, "--prompt", prompt, "--src", CFG.src, "--session-id", sid.id],
            { maxBuffer: 64 * 1024, timeout: 8000,
              env: { ...process.env, DOENGLINGZ_CONFIG_DIR: CFG.state_dir, WORKBUDDY_CONFIG_DIR: CFG.state_dir } },
            (err, out) => res(err ? null : (out || "")));
        });
        if (!injectCtx || !injectCtx.trim()) return;
        return { appendContext: injectCtx.trim() };
      } catch (e) { return; }
    }, { priority: 90 });

    api.on("before_tool_call", async (event, hookCtx) => {
      try {
        if (String(event?.toolName || "") !== "exec") return;
        const cmd = String(event?.params?.command || event?.params?.cmd || ""); if (!cmd) return;
        const pats = [
          { re: /rm\s+-(rf|fr)\s+(~|\/Users|\$HOME|\/\s*$)/, title: "红区·不可逆删除" },
          { re: /\bmkfs|dd\s+if=.*of=\/dev\//, title: "红区·磁盘破坏" },
          { re: /\bgit\s+push\b|\bnpm\s+publish\b|\bgh\s+release\s+create\b/, title: "红区·对外发布" },
          { re: /\bchmod\s+-R\s+777\s+\//, title: "红区·权限根变更" },
        ];
        for (const p of pats) if (p.re.test(cmd)) {
          try { const s0 = sessionOf(event, hookCtx); appendFileSync(LEDGER, JSON.stringify({ ts: new Date().toISOString(), end: "lobsterai-redgate", hit: String(p.re), action: "requireApproval", session_id: s0.id, sid_src: s0.src, run_id: s0.runId }) + "\n"); } catch (e) {}
          return { requireApproval: { title: p.title, description: `命中红区模式：${p.re}\n命令：${cmd.slice(0, 300)}`, severity: "critical", timeoutMs: 300000, timeoutBehavior: "deny" } };
        }
        return;
      } catch (e) { return; }
    }, { priority: 80 });

    // 守护五查：同一条逻辑挂两面（2026-10-06 重做·本端形态）
    //   · before_agent_finalize —— 本端**真派发**且事件带齐 runId/sessionId/sessionKey/
    //     lastAssistantMessage/messages ⇒ 归账三标识齐备（agent_end 的 eventKeys 实证只有
    //     messages/success/error/durationMs/runId，无 session 标识）
    //   · agent_end             —— 保留作兵底（若未来形态变化）
    //   同 run 两面都派发时按 runId 去重·只落一行（防重复计数）。
    //   观察型：一律返 undefined·⛔不参与 revise/finalize 裁决（决策权归 buluotuo-hooks 的 A 通道）。
    const lastRun = new Map();
    const recordGuard = async (event, hookCtx, endLabel) => {
      try {
        const runKey = String((event && event.runId) || (hookCtx && hookCtx.runId) || "");
        if (runKey && lastRun.has(runKey)) return;
        if (runKey) { lastRun.set(runKey, Date.now()); if (lastRun.size > 200) lastRun.clear(); }
        const text = finalAssistantText(event && event.messages)
          || String((event && event.lastAssistantMessage) || "");
        const sid = sessionOf(event, hookCtx);
        if (!text) {
          try { appendFileSync(LEDGER, JSON.stringify({ ts: new Date().toISOString(), end: endLabel, text_len: 0, note: "no_assistant_text", session_id: sid.id, sid_src: sid.src, run_id: sid.runId }) + "\n"); } catch (e) {}
          return;
        }
        const hits = (re) => [...new Set(text.match(re) || [])].join(",");
        const tslOn = Object.entries(TSL_MARKERS).filter(([, r]) => r.test(text)).map(([k]) => k);
        const rec = {
          ts: new Date().toISOString(), end: endLabel, text_len: text.length,
          red_zone_hits: hits(RED_ZONE_PAT), hard_violation_hits: hits(HARD_VIOLATION_PAT),
          reflection_signal_hits: hits(REFLECTION_SIGNAL_PAT), privacy_hits: hits(PRIVACY_PAT),
          tsl_hits: tslOn.join(","), alarm: (text.match(HARD_VIOLATION_PAT) || []).length > 0,
          session_id: sid.id, sid_src: sid.src, run_id: sid.runId,
        };
        try { appendFileSync(LEDGER, JSON.stringify(rec) + "\n"); } catch (e) {}
      } catch (err) { /* 失败放行 */ }
    };
    api.on("agent_end", async (event, hookCtx) => {
      await recordGuard(event, hookCtx, "lobsterai-plugin:agent_end");
    }, { priority: 100 });
    api.on("before_agent_finalize", async (event, hookCtx) => {
      await recordGuard(event, hookCtx, "lobsterai-plugin:before_agent_finalize");
    }, { priority: 99 });
  },
});

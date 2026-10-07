// lobsterai-buluotuo-hooks v0.1 — 布洛陀脚本体系·LobsterAI 运行面（数据驱动·纯转发·脱敏通用版）
// 通道：OpenClaw 第三方插件 typed hooks（本端无 settings.json·非标准 hook 端·capability.hooks_alternative）。
//
// 定位：把 WB 端 settings.json 钩子的「脚本体系」按**事件类**翻译成本端 OpenClaw typed hook——
//   即「根据系统特性做到最好的适配」的机制层，而不是逐条硬搬。
//
// 语义映射（事件类 → OpenClaw 载体 → 返回语义）：
//   UserPromptSubmit → before_prompt_build → stdout 非空则 appendContext（预注入）
//   Stop             → agent_end           → 观察型·脚本 stdout/stderr 落 state_dir 日志
//                                            （⛔ OpenClaw agent_end 不可注入·语义边界如实登记）
//   PreToolUse       → before_tool_call    → 脚本 exit 2 → { block: true, blockReason }
//   SessionStart     → session_start       → 观察型·落日志
//
// 单一数据源：ROSTER 表（与 install_scripts.py 的 ROSTER 同构）。新增/停用钩子只改这里。
// 脚本路径：由同目录 config.json 提供（setup.sh 落定）——⛔无硬编码作者路径、⛔零个人数据。
// 缺件跳过·失败放行（绝不阻断对话）·同 prompt 去重。
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { execFile } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
let CFG = { mc: "", scripts_dir: "", dt_devtools: "", state_dir: "" };
try { CFG = { ...CFG, ...JSON.parse(readFileSync(join(HERE, "config.json"), "utf8")) }; } catch (e) {}
if (!CFG.scripts_dir) CFG.scripts_dir = join(CFG.mc || ".", "脚本中心");
if (!CFG.dt_devtools) CFG.dt_devtools = join(CFG.mc || ".", "数字分身", "devtools");
if (!CFG.state_dir) CFG.state_dir = join(CFG.mc || ".", ".lobsterai");
try { mkdirSync(CFG.state_dir, { recursive: true }); } catch (e) {}
const LOG = join(CFG.state_dir, "buluotuo_hooks.log");

// ── 钩子总表（唯一数据源·与 install_scripts.py ROSTER 同构）──────────────
// cls: ups=UserPromptSubmit · stop=Stop · pre=PreToolUse · session=SessionStart
// dt : true → 脚本落在 [记忆中心]/数字分身/devtools/（否则 [记忆中心]/脚本中心/）
// tools: pre 类触发用的 OpenClaw 工具名（空=全部·减少无关 spawn）
const ROSTER = [
  { cls: "ups", f: "rule_fragment_inject.py" },          // 铁律硬墙·命中条件预注入条文
  { cls: "ups", f: "secret_key_guard.py" },              // 密钥/Token 粘贴提醒
  { cls: "ups", f: "ttl_expiry_guard.py" },              // 规则文件过期提醒
  { cls: "ups", f: "session_tail_inject.py" },           // 新会话注入上次收工与欠账
  { cls: "stop", f: "route_unknown_unknown.py" },        // 未知未知兜底·盲区登记
  { cls: "stop", f: "rule_three_layer_guard.py" },       // 回复格式契约校验
  { cls: "stop", f: "systemlog_stophook_check.py" },     // 今日系统日志收口检查
  { cls: "stop", f: "reply_tail_guard.py" },             // 回复"留尾巴"提醒
  { cls: "stop", f: "post_change_guard.py" },            // 改 A 漏更新 B/C/D 检测
  { cls: "stop", f: "delivery_boundary_guard.py" },      // 交付里没说清的静默取舍
// tsl_closeout_guard（2026-10-06 补挂·L5 红的真因）
//   实证：tsl_verify 判 L5 🔴「上轮 Stop 痕检=MISS」⇒ eight_check.log 全盘不存在
//   ⇒ tsl_closeout_guard（该账本的唯一生产者）**从未挂进 LobsterAI 端**——不是配置漂移·是缺件。
//   契约：吃 Stop stdin JSON（须 transcript_path）·stdout 仅违规时告警 ·退出码不阻断。
//   ⛔ 同批 ROSTER·纯转发·不复制其内部逻辑（真相归属=公共脚本）。
  { cls: "stop", f: "tsl_closeout_guard.py", dt: true },

  { cls: "stop", f: "twin_verdict_ledger.py", dt: true },// 数字分身·裁决台账
  { cls: "stop", f: "twin_changelog_guard.py", dt: true },// 数字分身·规格书同步守卫
  { cls: "pre", f: "edit_heading_guard.py", tools: ["edit", "write", "apply_patch"] },
  { cls: "pre", f: "skill_write_gate_guard.py", tools: ["edit", "write", "apply_patch", "exec"] },
  { cls: "pre", f: "skill_spec_read_guard.py", tools: ["read", "grep", "glob", "edit", "write", "apply_patch"] },
  { cls: "pre", f: "grep_sandbox_guard.py", tools: ["exec"] },
  { cls: "session", f: "crossend_guard.py" },            // 跨端家目录污染检测
];

function pathOf(e) {
  const d = e.dt ? CFG.dt_devtools : CFG.scripts_dir;
  const p = join(d, e.f);
  return existsSync(p) ? p : null;
}

// D1 档位声明守卫定位（既成守卫=SSOT·本处只消费其 verdict·⛔不重复实现判据）
function d1GuardPath() {
  const mc = CFG.mc || ".";
  const cands = [
    join(mc, "数字分身", "数字分身脚本", "doenglingz_level_declare_guard.py"),
    join(mc, "数字分身", "devtools", "doenglingz_level_declare_guard.py"),
    join(CFG.scripts_dir || ".", "doenglingz_level_declare_guard.py"),
  ];
  for (const p of cands) { try { if (existsSync(p)) return p; } catch (e) {} }
  return null;
}

function logLine(o) {
  try { appendFileSync(LOG, JSON.stringify({ ts: new Date().toISOString(), ...o }) + "\n"); } catch (e) {}
}

// 转发脚本：argv + stdin JSON(payload)，返回 {code, stdout, stderr}。失败放行（不 throw）。
function run(script, argv, payload, timeout) {
  return new Promise((resolve) => {
    let settled = false;
    const done = (v) => { if (!settled) { settled = true; resolve(v); } };
    try {
      const p = execFile(
        "python3",
        [script, ...argv],
        { maxBuffer: 256 * 1024, timeout, env: { ...process.env, WORKBUDDY_CONFIG_DIR: CFG.state_dir } },
        (err, stdout, stderr) => {
          const code = err && typeof err.code === "number" ? err.code : (err ? 1 : 0);
          done({ code, stdout: stdout || "", stderr: stderr || "" });
        },
      );
      try { p.stdin.write(JSON.stringify(payload)); p.stdin.end(); } catch (e) { try { p.stdin.end(); } catch (e2) {} }
    } catch (e) { done({ code: 1, stdout: "", stderr: String(e && e.message || e) }); }
  });
}

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
  text = text.replace(/【童灵[^】]*】[\s\S]*?$/m, "");
  text = text.replace(/<system-reminder>[\s\S]*?<\/system-reminder>/g, "");
  text = text.replace(/<<<[^>]*>>>/g, "");
  return text.trim();
}

function msgText(c) {
  if (typeof c === "string") return c;
  if (Array.isArray(c)) return c.map((p) => (typeof p === "string" ? p : (p && typeof p.text === "string" ? p.text : ""))).join("\n");
  return "";
}

function assistantText(messages) {
  const msgs = Array.isArray(messages) ? messages : [];
  for (let i = msgs.length - 1; i >= 0; i--) {
    const m = msgs[i] || {};
    if ((m.role || m.type) !== "assistant") continue;
    const t = msgText(m.content);
    if (t) return t;
  }
  return "";
}

// 把本回合消息写成 CC 风格 JSONL（供 Stop 类脚本按 transcript_path 解析）
function writeTranscript(messages, sessionKey) {
  const msgs = Array.isArray(messages) ? messages : [];
  const lines = [];
  for (const m of msgs) {
    const role = m && (m.role || m.type);
    if (role !== "user" && role !== "assistant") continue;
    const text = msgText(m.content);
    if (!text) continue;
    lines.push(JSON.stringify({ type: role, role, content: text }));
  }
  const safe = String(sessionKey || "s").replace(/[^a-zA-Z0-9_-]/g, "").slice(-24) || "s";
  const p = join(CFG.state_dir, `hook_transcript_${safe}.jsonl`);
  try { writeFileSync(p, lines.join("\n") + (lines.length ? "\n" : ""), "utf8"); return p; } catch (e) { return ""; }
}

const sessionOf = (e) => String(e?.ctx?.sessionKey || e?.sessionKey || e?.context?.sessionKey || "") || "global";

export default definePluginEntry({
  id: "lobsterai-buluotuo-hooks",
  name: "布洛陀脚本体系（LobsterAI）",
  description: "WB 端 settings.json 钩子的本端等价载体：UserPromptSubmit→before_prompt_build · Stop→agent_end · PreToolUse→before_tool_call · SessionStart→session_start（config 驱动·数据驱动 ROSTER）",
  version: "0.1.0",
  register(api) {
    const seen = new Map(); // sessionKey -> Set(promptKey)（UserPromptSubmit 去重）

    api.on("before_prompt_build", async (event) => {
      try {
        const prompt = cleanPrompt(event?.prompt);
        if (!prompt) return;
        const sk = sessionOf(event);
        const key = prompt.length + ":" + prompt.slice(0, 40);
        const s = seen.get(sk);
        if (s && s.has(key)) return;
        const ns = s || new Set(); ns.add(key); seen.set(sk, ns);
        if (seen.size > 50) seen.clear();

        const ctxs = [];
        for (const e of ROSTER) {
          if (e.cls !== "ups") continue;
          const sp = pathOf(e); if (!sp) continue;
          const r = await run(sp, ["--prompt", prompt],
            { hook_event_name: "UserPromptSubmit", session_id: sk, prompt, cwd: process.cwd() }, 8000);
          const out = (r.stdout || "").trim();
          if (out) ctxs.push(out);
          if ((r.stderr || "").trim()) logLine({ cls: "ups", f: e.f, code: r.code, stderr: r.stderr.trim().slice(0, 500) });
        }
        if (ctxs.length) return { appendContext: ctxs.join("\n") };
      } catch (e) { return; }
    }, { priority: 80 });

    api.on("before_tool_call", async (event) => {
      try {
        const tool = String(event?.toolName || "");
        const sId = sessionOf(event);
        for (const e of ROSTER) {
          if (e.cls !== "pre") continue;
          if (e.tools && !e.tools.includes(tool)) continue;
          const sp = pathOf(e); if (!sp) continue;
          const params = (event && event.params) || {};
          // 工具名 + 参数做本端→CC 语义垫片（守卫按 CC 名与字段判定）
          const shim = shimToolInput(tool, params);
          const r = await run(sp, [],
            { hook_event_name: "PreToolUse", session_id: sId, tool_name: shim.tool_name, tool_input: shim.tool_input }, 8000);
          if (r.code === 2) {
            const reason = (r.stdout || r.stderr || "").trim() || `${e.f} 命中拦截`;
            logLine({ cls: "pre", f: e.f, code: 2, blocked: true, tool });
            return { block: true, blockReason: reason };
          }
        }
        return;
      } catch (e) { return; }
    }, { priority: 80 });

    api.on("agent_end", async (event) => {
      try {
        const msgs = event?.messages;
        const sk = sessionOf(event);
        const tp = writeTranscript(msgs, sk);
        const txt = assistantText(msgs);
        const payload = {
          hook_event_name: "Stop", session_id: sk,
          transcript_path: tp, stop_hook_active: false,
          text: txt, last_assistant_message: txt, response: txt,
        };
        for (const e of ROSTER) {
          if (e.cls !== "stop") continue;
          const sp = pathOf(e); if (!sp) continue;
          const r = await run(sp, [], payload, 12000);
          if ((r.stdout || "").trim() || (r.stderr || "").trim()) {
            logLine({ cls: "stop", f: e.f, code: r.code,
              out: (r.stdout || "").trim().slice(0, 800), err: (r.stderr || "").trim().slice(0, 400) });
          }
        }
      } catch (e) { /* 失败放行 */ }
    }, { priority: 80 });

// 端独占机制面（2026-10-06 立·LobsterAI 独占·WB 端无此面·条文22 同族）
// · message_sending = 发送那一刻拿到 content 正文本体 → 可改可取消（Modify/gate）
//   实证：本端每轮真派发（探针 hook_probe.jsonl 16/16）；WB settings.json 端 Stop 钩子做不到（回复已出）
// · before_agent_finalize = 末段可令模型再跑一轮（见 A 通道）
api.on("message_sending", async (event) => {
  try {
    const sp = pathOf({ cls: "sending", f: "delivery_boundary_sending_guard.py" });
    if (!sp) return;
    const r = await run(sp, [], {
      hook_event_name: "MessageSending",
      to: event?.to ?? "", content: event?.content ?? null,
      replyToId: event?.replyToId ?? "", threadId: event?.threadId ?? "",
    }, 8000);
    if ((r.stdout || "").trim()) logLine({ cls: "sending", f: "delivery_boundary_sending_guard.py", code: r.code, out: r.stdout.trim().slice(0, 500) });
  } catch (e) { /* 失败放行·⛔守卫故障绝不阻断对话 */ }
}, { priority: 90 });

    // ── 会话标题统一（2026-10-06·跨端对齐④·补哲学点名而漏做的一块）────────────
    // 算：公共原语 session_title_utils（⛔不复制实现）｜写：sessions.patch.label（原生字段·⛔不造旁路）
    // 触发：首轮（非命令首条）·fire-and-forget·⛔不 await（⛔标题是旁路·⛔不拖慢主链）
    // 覆盖纪律：已有 label ⛔永不覆盖（对齐 WB 先例·⛔不洗掉用户手命名）
    // ⚠️ 落库不在此完成——插件无 sessions 写面（官方未列 label 字段）⇒ 输出到台账 + 由 agent 面补写
    // ── resolve_exec_env：路径契约注入（端独占机制面·2026-10-06）────────────
    // 把「记忆中心在哪里」从「每个脚本硬编码/各自探测」变成「环境契约·机制给」——
    // 对**本会话所有 exec** 生效（含我自己动手跑的），⛔不只限插件自己 spawn 的。
    // 战略意义：往后新写的脚本默认读 env（⛔不硬编码）⇒ 路径成为可移植契约；
    // 存量 148 处硬编码走**机械替换**逐步收敛（⛔不逐个手改·不改公共层判据）。
    // 官方契约：返 Record<string,string> 合并进 exec 环境；PATH/LD_*/DYLD_*/NODE_OPTIONS/
    //          代理/TLS 类危险键由宿主过滤·⛔无需本层防护（⛔不重复实现）。
    // 定位仅作信息（非拦截）：本 hook ⛔不返回 block——它只能给环境变量，⛔做不到拦。
    api.on("resolve_exec_env", async (event) => {
      try {
        if (String(event?.toolName || "") !== "exec") return;
        const env = {};
        if (CFG.mc) env.BULUOTUO_MC = CFG.mc;
        if (CFG.state_dir) env.BULUOTUO_STATE_DIR = CFG.state_dir;
        if (CFG.scripts_dir) env.BULUOTUO_SCRIPTS = CFG.scripts_dir;
        return Object.keys(env).length ? env : undefined;
      } catch (e) { return; }
    }, { priority: 90 });

    // ── A 通道（2026-10-06·末段“修正型”·地基=探针实证 before_agent_finalize 真派发）──
    // 把 Stop 档从“只看（agent_end·观察型）”升级为“能纪（可令模型再跑一轮）”。
    // 源①：D1 档位声明缺失（既成守卫 doenglingz_level_declare_guard 为 SSOT·本处只消费 verdict）
    // 源②：stop-ROSTER 守卫 stdout 行首 `REVISE:`
    // 安全：同 run 只纪一次（防循环·runner 另有 ≤3 上限）；⛔不复用正则猜（防 L3 “误判污染”覆辙）。
    const revisedRuns = new Set();
    api.on("before_agent_finalize", async (event) => {
      try {
        const runId = String(event?.runId || "");
        if (runId && revisedRuns.has(runId)) return;
        const sk = sessionOf(event);
        const txt = String(event?.lastAssistantMessage || "");
        if (!txt) return;
        const payload = {
          hook_event_name: "Stop", session_id: sk,
          transcript_path: String(event?.transcriptPath || ""),
          stop_hook_active: !!event?.stopHookActive,
          text: txt, last_assistant_message: txt, response: txt,
        };
        const doRevise = (reason) => {
          if (runId) revisedRuns.add(runId);
          if (revisedRuns.size > 200) revisedRuns.clear();
          return { action: "revise", reason: String(reason).slice(0, 300) };
        };
        const dg = d1GuardPath();
        if (dg) {
          const r = await run(dg, ["--check"], payload, 8000);
          const out = (r.stdout || "");
          if (/"alarm"\s*:\s*true/.test(out)) {
            let why = "缺档位声明";
            try { why = JSON.parse(out).reason || why; } catch (e) {}
            logLine({ cls: "finalize", f: "doenglingz_level_declare_guard", code: r.code, revise: why });
            return doRevise("首段照拄本回合注入的童灵档位标签（如【童灵·D1 常驻模式（非全量，仅人格基底）】）· " + why);
          }
        }
        for (const e of ROSTER) {
          if (e.cls !== "stop") continue;
          const sp = pathOf(e); if (!sp) continue;
          const r = await run(sp, [], payload, 12000);
          const line = (r.stdout || "").split("\n").map((l) => l.trim()).find((l) => l.startsWith("REVISE:"));
          if (line) {
            logLine({ cls: "finalize", f: e.f, code: r.code, revise: line.slice(0, 300) });
            return doRevise(line.slice(7).trim());
          }
        }
        return;
      } catch (e) { return; }
    }, { priority: 90 });

    api.on("session_start", async (event) => {
      try {
        const sk = sessionOf(event);
        const payload = { hook_event_name: "SessionStart", session_id: sk,
          source: String(event?.source || event?.reason || "startup") };
        for (const e of ROSTER) {
          if (e.cls !== "session") continue;
          const sp = pathOf(e); if (!sp) continue;
          const r = await run(sp, [], payload, 8000);
          if ((r.stdout || "").trim()) logLine({ cls: "session", f: e.f, code: r.code, out: r.stdout.trim().slice(0, 500) });
        }
      } catch (e) { /* 失败放行 */ }
    }, { priority: 80 });
  },
});

// 本端工具名/参数 → CC 语义（守卫据此判定；未知形态原样透传，守卫自会忽略）
function shimToolInput(tool, params) {
  const p = params || {};
  const filePath = p.file_path || p.path || "";
  if (tool === "exec") {
    return { tool_name: "Bash", tool_input: { command: String(p.command || p.cmd || "") } };
  }
  if (tool === "read") return { tool_name: "Read", tool_input: { file_path: filePath } };
  if (tool === "grep") return { tool_name: "Grep", tool_input: { pattern: String(p.pattern || ""), path: filePath } };
  if (tool === "glob") return { tool_name: "Glob", tool_input: { pattern: String(p.pattern || "") } };
  if (tool === "write") return { tool_name: "Write", tool_input: { file_path: filePath, content: String(p.content || "") } };
  if (tool === "edit") {
    let oldS = "", newS = "";
    const edits = Array.isArray(p.edits) ? p.edits : [];
    if (edits.length) { oldS = String(edits[0].oldText || ""); newS = String(edits[0].newText || ""); }
    else { oldS = String(p.oldText || p.old_string || ""); newS = String(p.newText || p.new_string || ""); }
    return { tool_name: "Edit", tool_input: { file_path: filePath, old_string: oldS, new_string: newS } };
  }
  if (tool === "apply_patch") {
    // apply_patch 无 old/new_string 分离语义 → 以增删行近似新旧串（edit_heading_guard 依赖此判定）
    const patch = String(p.patch || p.input || "");
    const removed = patch.split("\n").filter((l) => l.startsWith("-")).map((l) => l.slice(1)).join("\n");
    const added = patch.split("\n").filter((l) => l.startsWith("+")).map((l) => l.slice(1)).join("\n");
    return { tool_name: "Edit", tool_input: { file_path: filePath, old_string: removed, new_string: added } };
  }
  return { tool_name: tool, tool_input: p };
}

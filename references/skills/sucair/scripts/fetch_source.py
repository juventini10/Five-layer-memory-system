#!/usr/bin/env python3
"""
fetch_source.py — sucair Step 1 格式归一化工具（v4.5.1 · 2026-08-12 补降级路径）

统一入口：URL → 抓取（crawl4ai 本地无头 Chromium）；文件 → 转 MD（markitdown）。
⛔本地执行，不走云服务——隐私底线（方案 D5 拍板）。
依赖缺失降级（v4.5.1）：markitdown 缺时 .md/.markdown/.txt 直读；crawl4ai 缺时友好报错提示安装（⛔不裸 Traceback）。
用法：
  python3 fetch_source.py <URL或文件路径> [输出.md]   # 不给输出则打印 stdout
实测记录（2026-08-07）：飞书站点抓取✅（本地Chromium·4790字MD）/ txt转MD✅；2026-08-12 Loop：依赖缺失三态（md直读/非md报错/URL报错）✅。
⚠️ 已知特性：首次抓取冷启动约30-70秒（浏览器启动+渲染等待），属正常。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os

def fetch_url(url: str) -> str:
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    except ImportError:
        raise RuntimeError(
            f"URL 抓取依赖 crawl4ai 未安装——请先 `pip install crawl4ai` 再抓 {url}（⛔不走云服务）"
        )
    async def run():
        bc = BrowserConfig(headless=True, verbose=False)
        async with AsyncWebCrawler(config=bc) as crawler:
            r = await crawler.arun(url, config=CrawlerRunConfig(only_text=True))
            if not r.success:
                raise RuntimeError(f"抓取失败 status={r.status_code}，请改存本地文件再蒸")
            return r.markdown.raw_markdown or ""
    return asyncio.run(run())

def convert_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    try:
        from markitdown import MarkItDown
        return MarkItDown().convert(path).text_content
    except ImportError:
        # 降级①：依赖缺失（v4.5.1 既有）——纯文本直读，其余报错提示安装
        if ext in (".md", ".markdown", ".txt"):
            # 纯文本格式无需转换——依赖缺失降级直读（⛔不因转换器缺失阻塞本就无需转换的源）
            return open(path, encoding="utf-8", errors="replace").read()
        raise RuntimeError(
            f"格式转换依赖 markitdown 未安装——请先 `pip install markitdown` 再转 {path}（⛔不走云服务）"
        )
    except Exception as e:
        # 降级②（v4.10.0 清零批#15）：依赖已装但转换失败（损坏PDF/异常编码等）——
        # 纯文本格式直读容错兜底（errors=replace 不裸 Traceback），其余带原因报错
        if ext in (".md", ".markdown", ".txt"):
            print(f"⚠️ markitdown 转换失败（{type(e).__name__}: {e}）——.md/.txt 源直读降级", file=sys.stderr)
            return open(path, encoding="utf-8", errors="replace").read()
        raise RuntimeError(
            f"markitdown 转换失败（{type(e).__name__}: {e}）——请检查文件完整性或改存文本格式后再转 {path}"
        ) from e

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    src = sys.argv[1]
    md = fetch_url(src) if src.startswith(("http://", "https://")) else convert_file(src)
    if len(sys.argv) > 2:
        open(sys.argv[2], "w", encoding="utf-8").write(md)
        print(f"✅ 已转换 {len(md)} 字 → {sys.argv[2]}")
    else:
        print(md)

if __name__ == "__main__":
    main()

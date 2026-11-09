# -*- coding: utf-8 -*-
"""生成合并版补充截图与《补充验收记录.docx》。"""
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "results" / "screenshots"
OUT = ROOT / "deliverables" / "补充验收记录.docx"
MONO = r"C:\Windows\Fonts\consola.ttf"
CJK = r"C:\Windows\Fonts\msyh.ttc"

JOBS = [
    ("merged_nodes.txt", "38_第四节点增删.png", "副本集第四节点增删（rs.add → SECONDARY → rs.remove）"),
    ("merged_readprobe.txt", "39_故障转移读探针.png", "故障转移期间读探针（secondaryPreferred）"),
    ("single_auth.txt", "40_单机认证.png", "单机 28117 认证与三账号权限验证"),
]


def wrap(line, cols=104):
    out, cur, width = [], "", 0
    for ch in line:
        cw = 1 if ord(ch) < 128 else 2
        if width + cw > cols:
            out.append(cur)
            cur, width = "", 0
        cur += ch
        width += cw
    out.append(cur)
    return out


def render(text, out_png, title):
    lines = []
    for raw in text.splitlines():
        lines.extend(wrap(raw) if raw else [""])
    cw, fs, lh, pad = 7, 11, 17, 14
    w = pad * 2 + 104 * cw
    h = pad * 2 + 28 + len(lines) * lh
    img = Image.new("RGB", (w, h), (30, 33, 38))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 26], fill=(52, 58, 64))
    d.text((pad, 4), title, font=ImageFont.truetype(CJK, 12), fill=(220, 220, 220))
    fm = ImageFont.truetype(MONO, fs)
    fc = ImageFont.truetype(CJK, fs)
    y = pad + 26
    for line in lines:
        x = pad
        for ch in line:
            if ord(ch) < 128:
                d.text((x, y), ch, font=fm, fill=(212, 218, 220))
                x += cw
            else:
                d.text((x, y - 1), ch, font=fc, fill=(212, 218, 220))
                x += cw * 2
        y += lh
    img.save(out_png)


def set_cn(run, name="宋体", size=10.5, bold=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if color:
        run.font.color.rgb = color


def para(doc, text, size=10.5, bold=False, indent=True, space=4):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space)
    pf.line_spacing = 1.25
    if indent:
        pf.first_line_indent = Pt(size * 2)
    set_cn(p.add_run(text), "宋体", size, bold)
    return p


def head(doc, text, size=14):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    set_cn(p.add_run(text), "黑体", size, True, RGBColor(0x1F, 0x3B, 0x4D))


def image(doc, path, cap, width=13.0):
    iw, ih = Image.open(path).size
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Cm(min(width, 16.0 * iw / ih)))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cn(c.add_run(cap), "宋体", 9, False, RGBColor(0x44, 0x44, 0x44))


def table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cn(p.add_run(h), "黑体", 9, True, RGBColor(0xFF, 0xFF, 0xFF))
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "2A6F6B")
        c._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            set_cn(p.add_run(str(v)), "宋体", 9)
    para(doc, "", indent=False, space=2)


def main():
    shots = {}
    for src, png, title in JOBS:
        text = (ROOT / "results" / src).read_text(encoding="utf-8")
        out = SHOTS / png
        render(text, out, title[:38])
        shots[png] = title
        print("saved", out)

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.4)
    sec.top_margin = sec.bottom_margin = Cm(2.2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cn(p.add_run("智慧图书馆数字资源平台 · 补充验收记录"), "黑体", 16, True, RGBColor(0x1F, 0x3B, 0x4D))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cn(p.add_run("合并版新增：Compass 图形化验收、副本集节点增删、故障转移读探针、单机认证"),
           "楷体", 9.5, False, RGBColor(0x55, 0x55, 0x55))

    head(doc, "1  Compass 图形化验收")
    para(doc, "用 MongoDB Compass 1.50 连接 mongodb://127.0.0.1:28117/smart_library，集合列表显示 books 50、readers 30、"
              "borrow_logs 3K、category_stats 6、fs.files 6（audit_logs 条数随操作增长），与命令行 countDocuments 一致；"
              "在 books 的过滤框输入 {price: {$gt: 80}} 可返回与脚本相同的结果集。")
    image(doc, SHOTS / "37_Compass集合列表.png", "图 1  Compass 连接 smart_library 的集合列表（真实窗口截图）")

    head(doc, "2  副本集第四节点增删")
    para(doc, "在 libraryRS（28217—28219，keyFile 认证）运行中加入 28220 节点：replSetReconfig 后状态变为 SECONDARY，"
              "成员数 3→4；随后移除该节点，成员数回到 3，主节点不变。操作记录见图 2。")
    image(doc, SHOTS / "38_第四节点增删.png", "图 2  第四节点增删记录（运行日志可视化，非窗口截图）")
    table(doc, ["阶段", "成员数", "状态"], [["加入前", "3", "28217/28218/28219"],
                                            ["加入后", "4", "28220 变为 SECONDARY"],
                                            ["移除后", "3", "恢复三节点"]])

    head(doc, "3  故障转移期间的读探针")
    para(doc, "以 secondaryPreferred 每 0.3 秒读取一次，同时对主节点执行 replSetStepDown：选举耗时 8.55 秒，"
              "读请求 45 次全部成功、0 次失败，说明从节点在此期间继续提供读服务；写操作仍需应用重试（见 results/replica.json）。")
    image(doc, SHOTS / "39_故障转移读探针.png", "图 3  故障转移读探针（运行日志可视化，非窗口截图）")

    head(doc, "4  单机环境认证与权限")
    para(doc, "单机 28117 以 --auth 启动，创建 labAdmin（root）、libReader（read）、libWriter（readWrite）；"
              "验证结果：匿名读取 code 13、libReader 读 50 条但写入被拒、libWriter 写 audit_logs 成功。")
    image(doc, SHOTS / "40_单机认证.png", "图 4  单机账号权限验证（运行日志可视化，非窗口截图）")

    head(doc, "5  结论与批次说明")
    para(doc, "本次补充验收与 01—36 号页面截图、single_node/replica/sharding 记录在同一批次重跑："
              "单机 28117、副本集 28217—28219、分片 28300—28302/28417 全部重新初始化后一次产出，未拼接历史批次。")
    para(doc, "补充后：任务三的权限验证回到单机环境，任务五补齐节点增删与读取连续性证据，任务七补上 Compass 图形化核对；"
              "分片分布为 1300/1700 条（43.3%/56.7%）。")

    doc.save(OUT)
    print("saved", OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()

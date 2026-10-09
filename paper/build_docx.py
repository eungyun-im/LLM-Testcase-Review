"""Put the paper into the KSAE template.

    python paper/build_docx.py TEMPLATE.docx OUT.docx

The template supplies the page, the columns, the fonts and the look of every
kind of paragraph. This script takes the formatting of the template's own
paragraphs (title, authors, abstract, headings, body, captions, references)
and fills it with the text of paper_text.py. The instructional comments of the
template are removed, as the template asks.
"""

import json
import re
import struct
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import paper_text  # noqa: E402

EMU_PER_CM = 360000
COLUMN_CM = 7.4
TABLE_WIDTH = 4240  # twips, one column of the template


def grab(paragraphs, index):
    """The pPr and the first run's rPr of a template paragraph."""
    paragraph = paragraphs[index]
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", paragraph, re.S).group(0)
    run = re.search(r"<w:r[ >].*?</w:r>", paragraph, re.S)
    rpr = re.search(r"<w:rPr>.*?</w:rPr>", run.group(0), re.S).group(0) if run else ""
    return ppr, rpr


def strip_color(xml):
    return re.sub(r'<w:color w:val="0000FF"/>', "", xml)


def rpr_of(base, bold=False, italic=False, sup=False, size=None):
    """Rebuild an rPr with the flags in schema order."""
    fonts = re.search(r"<w:rFonts[^>]*/>", base)
    spacing = re.search(r"<w:spacing w:val=\"[-0-9]+\"/>", base)
    sz = size or (re.search(r'<w:sz w:val="(\d+)"/>', base).group(1) if re.search(r'<w:sz w:val="(\d+)"/>', base) else None)
    parts = []
    if fonts:
        parts.append(re.sub(r' w:hint="[^"]*"', "", fonts.group(0)))
    if bold or ("<w:b/>" in base and not sup):
        parts.append("<w:b/><w:bCs/>")
    if italic or "<w:i/>" in base:
        parts.append("<w:i/><w:iCs/>")
    if spacing:
        parts.append(spacing.group(0))
    if sz:
        parts.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    if sup:
        parts.append('<w:vertAlign w:val="superscript"/>')
    return "<w:rPr>" + "".join(parts) + "</w:rPr>"


def run(text, rpr):
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


CITATION = re.compile(r"\[\[([0-9,\-]+)\]\]")
TAG = re.compile(r"(<b>.*?</b>|<i>.*?</i>|\[\[[0-9,\-]+\]\])")


def cite_text(spec):
    """'2-4' -> '2)-4)', '1,5' -> '1),5)', '3' -> '3)'."""
    return ",".join("-".join(part + ")" for part in chunk.split("-")) for chunk in spec.split(","))


def runs(text, base):
    """Runs for text with <b>, <i> and [[citation]] marks."""
    out = []
    for piece in TAG.split(text):
        if not piece:
            continue
        if piece.startswith("<b>"):
            out.append(run(piece[3:-4], rpr_of(base, bold=True)))
        elif piece.startswith("<i>"):
            out.append(run(piece[3:-4], rpr_of(base, italic=True)))
        elif piece.startswith("[["):
            out.append(run(cite_text(CITATION.match(piece).group(1)), rpr_of(base, sup=True)))
        else:
            out.append(run(piece, base))
    return "".join(out)


def paragraph(ppr, content):
    return f"<w:p>{ppr}{content}</w:p>"


def png_size(path):
    data = Path(path).read_bytes()
    return struct.unpack(">II", data[16:24])


class Package:
    def __init__(self, template):
        self.zip = zipfile.ZipFile(template)
        self.files = {name: self.zip.read(name) for name in self.zip.namelist()}
        self.images = []

    def text(self, name):
        return self.files[name].decode("utf-8")

    def set_text(self, name, value):
        self.files[name] = value.encode("utf-8")


def image_paragraph(package, path, number):
    width, height = png_size(path)
    cx = int(COLUMN_CM * EMU_PER_CM)
    cy = int(cx * height / width)
    rid = f"rIdFig{number}"
    name = f"media/paper_fig{number}.png"
    package.files["word/" + name] = Path(path).read_bytes()
    package.images.append((rid, name))
    ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    drawing = (
        f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="{100 + number}" name="Figure {number}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="{ns}" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic xmlns:a="{ns}"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr>'
        f'<pic:cNvPr id="0" name="paper_fig{number}.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill>'
        f'<a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm>'
        f'<a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f"</pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>"
    )
    ppr = '<w:pPr><w:keepNext/><w:spacing w:before="60" w:after="20" w:line="240" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr>'
    return paragraph(ppr, f"<w:r><w:rPr><w:noProof/></w:rPr>{drawing}</w:r>")


def table_xml(header, rows, widths, bold_rows=(), size=15):
    borders = "".join(f'<w:{side} w:val="single" w:sz="2" w:space="0" w:color="000000"/>'
                      for side in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)

    def cell(text, width, bold, align):
        rpr = f'<w:rPr>{"<w:b/><w:bCs/>" if bold else ""}<w:spacing w:val="-6"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
        ppr = f'<w:pPr><w:spacing w:before="10" w:after="10" w:line="{size * 13}" w:lineRule="exact"/><w:jc w:val="{align}"/>{rpr}</w:pPr>'
        return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p>{ppr}{runs(text, rpr)}</w:p></w:tc>')

    body = []
    for index, row in enumerate([header] + rows):
        bold = index == 0 or (index - 1) in bold_rows
        cells = "".join(cell(text, widths[j], bold, "left" if j == 0 else "center") for j, text in enumerate(row))
        body.append(f'<w:tr><w:trPr><w:cantSplit/>{"<w:tblHeader/>" if index == 0 else ""}</w:trPr>{cells}</w:tr>')
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{borders}</w:tblBorders>'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="35" w:type="dxa"/><w:right w:w="35" w:type="dxa"/></w:tblCellMar>'
            f'<w:tblLook w:val="0000"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(body)}</w:tbl>')


def build(template, out, numbers_path, fig_dir):
    package = Package(template)
    xml = package.text("word/document.xml")
    head = xml[: xml.index("<w:body>") + len("<w:body>")]
    body = xml[len("".join([head])):]
    tail_sect = re.findall(r"<w:sectPr.*?</w:sectPr>", body, re.S)[-1]
    paragraphs = re.findall(r"<w:p[ >].*?</w:p>", body, re.S)
    first_section = re.search(r"<w:p [^>]*>(?:(?!</w:p>).)*?<w:sectPr.*?</w:sectPr></w:pPr></w:p>", body, re.S).group(0)
    first_section = re.sub(r' w14:paraId="[0-9A-F]+" w14:textId="[0-9A-F]+"', "", first_section)

    numbers = json.loads(Path(numbers_path).read_text(encoding="utf-8"))
    doc = paper_text.compose(numbers)

    title_ppr, title_rpr = grab(paragraphs, 3)
    author_ppr, author_rpr = grab(paragraphs, 5)
    aff_ppr, aff_rpr = grab(paragraphs, 6)
    en_title_ppr, en_title_rpr = grab(paragraphs, 8)
    en_author_ppr, en_author_rpr = grab(paragraphs, 9)
    en_aff_ppr, en_aff_rpr = grab(paragraphs, 10)
    abstract_ppr, abstract_rpr = grab(paragraphs, 14)
    keywords_ppr, _ = grab(paragraphs, 16)
    h1_ppr, h1_rpr = grab(paragraphs, 33)
    body_ppr, body_rpr = grab(paragraphs, 35)
    h2_ppr, h2_rpr = grab(paragraphs, 43)
    h3_ppr, h3_rpr = grab(paragraphs, 44)
    caption_ppr, caption_rpr = grab(paragraphs, 65)
    item_ppr, item_rpr = grab(paragraphs, 91)
    ref_head_ppr, ref_head_rpr = grab(paragraphs, 124)
    ref_ppr, ref_rpr = grab(paragraphs, 129)
    ref_ppr, ref_rpr = strip_color(ref_ppr), strip_color(ref_rpr)
    keywords_ppr = strip_color(keywords_ppr)

    blank = lambda ppr: paragraph(ppr, "")  # noqa: E731
    out_xml = []

    out_xml.append(paragraph(title_ppr, runs(doc["title_ko"], title_rpr)))
    out_xml.append(blank(grab(paragraphs, 4)[0]))
    marks = []
    for index, name in enumerate(doc["authors_ko"]):
        marks.append(run(("·" if index else "") + name[0], author_rpr))
        marks.append(run(name[1], rpr_of(author_rpr, bold=True, sup=True)))
    out_xml.append(paragraph(author_ppr, "".join(marks)))
    out_xml.append(paragraph(aff_ppr, "".join(
        run(("·" if i else "") + aff, aff_rpr) + run(f"{i + 1})", rpr_of(aff_rpr, sup=True)) for i, aff in enumerate(doc["affiliations_ko"]))))
    out_xml.append(blank(grab(paragraphs, 7)[0]))
    out_xml.append(paragraph(en_title_ppr, runs(doc["title_en"], en_title_rpr)))
    marks = []
    for index, name in enumerate(doc["authors_en"]):
        marks.append(run(("·" if index else "") + name[0], en_author_rpr))
        marks.append(run(name[1], rpr_of(en_author_rpr, sup=True)))
    out_xml.append(paragraph(en_author_ppr, "".join(marks)))
    for i, aff in enumerate(doc["affiliations_en"]):
        out_xml.append(paragraph(en_aff_ppr, run(f"{i + 1})", rpr_of(en_aff_rpr, sup=True)) + run(aff, en_aff_rpr)))
    out_xml.append(blank(grab(paragraphs, 13)[0]))
    out_xml.append(paragraph(abstract_ppr, run("Abstract", rpr_of(abstract_rpr, bold=True)) + run(" : ", abstract_rpr)
                             + runs(doc["abstract"], abstract_rpr)))
    out_xml.append(blank(grab(paragraphs, 15)[0]))
    out_xml.append(paragraph(keywords_ppr, run("Key words", rpr_of(abstract_rpr, bold=True)) + run(" : ", abstract_rpr)
                             + runs(doc["keywords"], abstract_rpr)))
    out_xml.append(blank(grab(paragraphs, 17)[0]))
    out_xml.append(first_section)

    # The corresponding-author footnote hangs on a hidden white "." paragraph of the template
    footnote_ref = re.sub(r' w14:paraId="[0-9A-F]+" w14:textId="[0-9A-F]+"', "", paragraphs[24])
    out_xml.append(footnote_ref)
    footnotes = package.text("word/footnotes.xml")
    fn_rpr = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hint="eastAsia"/><w:sz w:val="16"/></w:rPr>'
    new_fn = ('<w:footnote w:id="1"><w:p><w:pPr><w:pStyle w:val="a4"/></w:pPr>'
              f'<w:r>{fn_rpr}<w:t xml:space="preserve">* 교신저자, E-mail: {escape(doc["email"])}</w:t></w:r></w:p></w:footnote>')
    footnotes = re.sub(r'<w:footnote w:id="1">.*?</w:footnote>', lambda _: new_fn, footnotes, count=1, flags=re.S)
    package.set_text("word/footnotes.xml", footnotes)

    figure_number = 0
    for block in doc["blocks"]:
        kind = block[0]
        if kind == "h1":
            out_xml.append(blank(grab(paragraphs, 32)[0]))
            out_xml.append(paragraph(h1_ppr, runs(block[1], h1_rpr)))
        elif kind == "h2":
            out_xml.append(paragraph(h2_ppr, runs(block[1], h2_rpr)))
        elif kind == "h3":
            out_xml.append(paragraph(h3_ppr, runs(block[1], h3_rpr)))
        elif kind == "p":
            out_xml.append(paragraph(body_ppr, runs(block[1], body_rpr)))
        elif kind == "item":
            out_xml.append(paragraph(item_ppr, runs(block[1], item_rpr)))
        elif kind == "fig":
            figure_number += 1
            out_xml.append(image_paragraph(package, Path(fig_dir) / block[1], figure_number))
            keep = re.sub(r"<w:spacing [^>]*/>(?=<w:rPr>)", '<w:spacing w:before="20" w:after="120" w:line="240" w:lineRule="auto"/>', caption_ppr, count=1)
            out_xml.append(paragraph(keep, runs(f"Fig. {figure_number} {block[2]}", strip_color(caption_rpr))))
        elif kind == "table":
            caption = re.sub(r"<w:spacing [^>]*/>(?=<w:rPr>)", '<w:keepNext/><w:spacing w:before="80" w:after="40" w:line="240" w:lineRule="auto"/>', caption_ppr, count=1)
            out_xml.append(paragraph(caption, runs(f"Table {block[1]} {block[2]}", strip_color(caption_rpr))))
            out_xml.append(table_xml(block[3], block[4], block[5], bold_rows=block[6] if len(block) > 6 else ()))
            out_xml.append(paragraph('<w:pPr><w:spacing w:before="0" w:after="60" w:line="120" w:lineRule="exact"/></w:pPr>', ""))
        elif kind == "references":
            out_xml.append(blank(grab(paragraphs, 125)[0]))
            out_xml.append(paragraph(ref_head_ppr, run("References", ref_head_rpr)))
            for entry in block[1]:
                out_xml.append(paragraph(ref_ppr, runs(entry, ref_rpr)))
        elif kind == "note":
            out_xml.append(paragraph(body_ppr, runs(block[1], body_rpr)))
        else:
            raise ValueError(kind)

    new_body = "".join(out_xml) + tail_sect + "</w:body></w:document>"
    package.set_text("word/document.xml", head + new_body)

    # Relationships: drop comments, images and OLE of the template, add the figures
    rels = package.text("word/_rels/document.xml.rels")
    removed_targets = []

    def drop(match):
        target = re.search(r'Target="([^"]+)"', match.group(0)).group(1)
        if re.search(r'Type="[^"]*/(comments|commentsExtended|people|image|oleObject)"', match.group(0)) or "comments" in target or "people" in target:
            removed_targets.append(target)
            return ""
        return match.group(0)

    rels = re.sub(r"<Relationship [^>]*/>", drop, rels)
    added = "".join(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{name}"/>'
                    for rid, name in package.images)
    rels = rels.replace("</Relationships>", added + "</Relationships>")
    package.set_text("word/_rels/document.xml.rels", rels)

    other_refs = " ".join(package.text(n) for n in package.files if n.endswith(".rels") and n != "word/_rels/document.xml.rels")
    for target in removed_targets:
        if target.startswith("file:") or target.startswith("http"):
            continue
        part = "word/" + target if not target.startswith("/") else target[1:]
        if Path(target).name not in other_refs:
            package.files.pop(part, None)
    for name in ("word/comments.xml", "word/commentsExtended.xml", "word/people.xml"):
        package.files.pop(name, None)
    types = package.text("[Content_Types].xml")
    types = re.sub(r'<Override PartName="/word/(comments|commentsExtended|people)\.xml"[^>]*/>', "", types)
    package.set_text("[Content_Types].xml", types)

    core = package.text("docProps/core.xml")
    core = re.sub(r"<dc:title>.*?</dc:title>", f"<dc:title>{escape(doc['title_ko'])}</dc:title>", core)
    core = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator>Eungyun Im</dc:creator>", core)
    core = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", "<cp:lastModifiedBy>Eungyun Im</cp:lastModifiedBy>", core)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = re.sub(r"(<dcterms:modified[^>]*>).*?(</dcterms:modified>)", rf"\g<1>{now}\g<2>", core)
    package.set_text("docProps/core.xml", core)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        order = ["[Content_Types].xml"] + [n for n in package.files if n != "[Content_Types].xml"]
        for name in order:
            target.writestr(name, package.files[name])
    print("wrote", out)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], HERE / "numbers.json", HERE)

// 書籍原稿（Word）を content.js から組み立てる
//   node build_book.js  → FX包み足_原稿.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat, PageBreak, Footer,
  PageNumber, TableOfContents,
} = require("docx");
const book = require("./content");

const MINCHO = { ascii: "Yu Mincho", eastAsia: "游明朝", hAnsi: "Yu Mincho" };
const GOTHIC = { ascii: "Yu Gothic", eastAsia: "游ゴシック", hAnsi: "Yu Gothic" };
const PAGE_W = 8391, PAGE_H = 11906, MARGIN_X = 1021, MARGIN_Y = 1134;   // A5
const TEXT_W = PAGE_W - MARGIN_X * 2;                                     // 6349 DXA
const IMG_W = Math.round(TEXT_W / 1440 * 96);
const EX_IMG_W = Math.round(IMG_W * 0.92);                                 // 実例ページは少し小さく                              // px
const GREEN = "1E8449", RED = "C0392B";

let listInstance = 0;

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 100, line: opts.line || 360 },
    indent: opts.noIndent ? undefined : { firstLine: 210 },
    alignment: opts.align,
    children: [new TextRun({ text, ...opts.run })],
  });
}

function image(src, caption, width = IMG_W) {
  const file = path.join(__dirname, src);
  const { w, h } = pngSize(file);
  const out = [new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(file),
      transformation: { width, height: Math.round(width * h / w) } })],
  })];
  if (caption) {
    out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: caption, size: 17, font: GOTHIC, color: "555555" })] }));
  }
  return out;
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" };
const cellBorders = { top: border, bottom: border, left: border, right: border };

function table(rows, widths, header = true) {
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({
      children: r.map((c, j) => new TableCell({
        width: { size: widths[j], type: WidthType.DXA },
        borders: cellBorders,
        shading: header && i === 0 ? { fill: "EDEDED", type: ShadingType.CLEAR, color: "auto" } : undefined,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: c, size: 18,
          bold: header && i === 0, font: header && i === 0 ? GOTHIC : MINCHO })] })],
      })),
    })),
  });
}

function box(title, text, fill = "F3F6FA", edge = "8AA4C8") {
  const b = { style: BorderStyle.SINGLE, size: 8, color: edge, space: 6 };
  const common = { border: { top: b, bottom: b, left: b, right: b },
    shading: { fill, type: ShadingType.CLEAR, color: "auto" }, indent: { left: 120, right: 120 } };
  return [
    new Paragraph({ ...common, keepNext: true, keepLines: true, spacing: { before: 160, after: 0 },
      children: [new TextRun({ text: title, bold: true, font: GOTHIC, size: 19 })] }),
    new Paragraph({ ...common, keepLines: true, spacing: { after: 200, line: 320 },
      children: [new TextRun({ text, size: 19 })] }),
  ];
}

function list(items, numbered) {
  const inst = ++listInstance;
  return items.map((t) => new Paragraph({
    numbering: { reference: numbered ? "num" : "bullet", level: 0, instance: numbered ? inst : 0 },
    spacing: { after: 60, line: 340 },
    children: [new TextRun(t)],
  }));
}

function heading(text, level) {
  return new Paragraph({ heading: level, children: [new TextRun(text)] });
}

// 実例データを2列×3段にまとめて縦幅を節約する
function dataTable(data) {
  const cells = data.concat(data.length % 2 ? [["", ""]] : []);
  const rows = [];
  for (let i = 0; i < cells.length; i += 2) rows.push([...cells[i], ...cells[i + 1]]);
  const w = [1350, TEXT_W / 2 - 1350, 950, TEXT_W / 2 - 950];
  return table(rows, w, false);
}

function example(ex) {
  const color = ex.loss ? RED : GREEN;
  const out = [
    new Paragraph({ heading: HeadingLevel.HEADING_2, pageBreakBefore: true, spacing: { before: 0, after: 80 },
      children: [new TextRun({ text: ex.id + "　", size: 21 }), new TextRun({ text: ex.title, color, size: 21 })] }),
    ...image(ex.img, null, EX_IMG_W),
    dataTable(ex.data),
    new Paragraph({ spacing: { after: 80 }, children: [] }),
    ...ex.body.map((t) => p(t, { line: 320 })),
    ...box(ex.loss ? "この負けから学ぶこと" : "ポイント", ex.point,
      ex.loss ? "FBF1F0" : "F1F8F3", ex.loss ? "D9A19B" : "8FC3A0"),
  ];
  return out;
}

function render(blocks) {
  const out = [];
  for (const b of blocks) {
    switch (b.t) {
      case "h1": out.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true,
        children: [new TextRun(b.text)] })); break;
      case "h2": out.push(heading(b.text, HeadingLevel.HEADING_2)); break;
      case "h3": out.push(heading(b.text, HeadingLevel.HEADING_3)); break;
      case "p": out.push(p(b.text)); break;
      case "bullets": out.push(...list(b.items, false)); break;
      case "numbered": out.push(...list(b.items, true)); break;
      case "img": out.push(...image(b.src, b.caption)); break;
      case "table": out.push(table(b.rows, b.widths), new Paragraph({ spacing: { after: 120 }, children: [] })); break;
      case "box": out.push(...box(b.title, b.text)); break;
      case "example": out.push(...example(b)); break;
      case "pagebreak": break;   // 章は h1 で改ページ済み
      default: throw new Error("unknown block " + b.t);
    }
  }
  return out;
}

const titlePage = [
  new Paragraph({ spacing: { before: 3000 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({ text: book.title, bold: true, size: 48, font: GOTHIC })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1600 },
    children: [new TextRun({ text: book.subtitle, size: 21, font: GOTHIC, color: "444444" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: book.author, size: 24 })] }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: "目次", bold: true, size: 30, font: GOTHIC })] }),
  new TableOfContents("目次", { hyperlink: true, headingStyleRange: "1-2" }),
];

const doc = new Document({
  title: book.title,
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: MINCHO, size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: GOTHIC },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: "333333", space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: GOTHIC },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 21, bold: true, font: GOTHIC },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bullet", levels: [{ level: 0, format: LevelFormat.BULLET, text: "・", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 420, hanging: 280 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 420, hanging: 320 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: PAGE_H },
      margin: { top: MARGIN_Y, bottom: MARGIN_Y, left: MARGIN_X, right: MARGIN_X } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 16 })] })] }) },
    children: [...titlePage, ...render(book.blocks)],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "FX包み足_原稿.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});

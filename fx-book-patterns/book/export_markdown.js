// content.js を Markdown（画像は figures/ を相対参照）に書き出す
//   node export_markdown.js  → FX包み足_原稿.md
const fs = require("fs");
const path = require("path");
const book = require("./content");

const md = [`# ${book.title}`, "", `## ${book.subtitle}`, "", book.author, ""];
const tableMd = (rows) => [
  "| " + rows[0].join(" | ") + " |",
  "|" + rows[0].map(() => "---").join("|") + "|",
  ...rows.slice(1).map((r) => "| " + r.join(" | ") + " |"), ""];

for (const b of book.blocks) {
  switch (b.t) {
    case "h1": md.push(`# ${b.text}`, ""); break;
    case "h2": md.push(`## ${b.text}`, ""); break;
    case "h3": md.push(`### ${b.text}`, ""); break;
    case "p": md.push(b.text, ""); break;
    case "bullets": md.push(...b.items.map((i) => `- ${i}`), ""); break;
    case "numbered": md.push(...b.items.map((i, n) => `${n + 1}. ${i}`), ""); break;
    case "img": md.push(`![${b.caption || ""}](${b.src})`, "", b.caption ? `*${b.caption}*` : "", ""); break;
    case "table": md.push(...tableMd(b.rows)); break;
    case "box": md.push(`> **${b.title}**`, ">", `> ${b.text}`, ""); break;
    case "example":
      md.push(`## ${b.id}　${b.title}`, "", `![${b.id}](${b.img})`, "");
      md.push(...tableMd([["項目", "値"], ...b.data]));
      md.push(...b.body.flatMap((t) => [t, ""]));
      md.push(`> **${b.loss ? "この負けから学ぶこと" : "ポイント"}**`, ">", `> ${b.point}`, "");
      break;
    case "pagebreak": break;
    default: throw new Error("unknown block " + b.t);
  }
}
fs.writeFileSync(path.join(__dirname, "FX包み足_原稿.md"), md.join("\n"));
console.log("ok");

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, TabStopType, TabStopPosition
} = require("docx");

// --- CONFIG ---
const PAGE_WIDTH = 11906; // A4 DXA
const PAGE_HEIGHT = 16838;
const MARGIN = 1440; // 1 inch
const CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN;

const FILES = [
  "frontmatter.md", "cap00.md", "cap01.md", "cap02.md", "cap03.md",
  "cap04.md", "cap05.md", "cap06_07.md", "cap08.md", "cap09.md",
  "cap10.md", "cap11.md", "cap12.md", "cap13.md", "cap14.md",
  "cap15_16_17.md", "appendices.md"
];

// --- MARKDOWN PARSER ---
function parseMarkdown(text) {
  const lines = text.split("\n");
  const elements = [];
  let inCodeBlock = false;
  let codeLines = [];
  let inTable = false;
  let tableRows = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code blocks
    if (line.startsWith("```")) {
      if (inCodeBlock) {
        elements.push({ type: "code", content: codeLines.join("\n") });
        codeLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }
    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    // Tables
    if (line.includes("|") && line.trim().startsWith("|")) {
      if (!inTable) {
        inTable = true;
        tableRows = [];
      }
      // Skip separator rows
      if (/^\|[\s\-:|]+\|$/.test(line.trim())) continue;
      const cells = line.split("|").slice(1, -1).map(c => c.trim());
      if (cells.length > 0) tableRows.push(cells);
      continue;
    } else if (inTable) {
      inTable = false;
      if (tableRows.length > 0) {
        elements.push({ type: "table", rows: tableRows });
        tableRows = [];
      }
    }

    // Headings
    if (line.startsWith("# ")) {
      elements.push({ type: "h1", content: line.slice(2).trim() });
    } else if (line.startsWith("## ")) {
      elements.push({ type: "h2", content: line.slice(3).trim() });
    } else if (line.startsWith("### ")) {
      elements.push({ type: "h3", content: line.slice(4).trim() });
    } else if (line.startsWith("#### ")) {
      elements.push({ type: "h4", content: line.slice(5).trim() });
    } else if (line.startsWith("> ")) {
      elements.push({ type: "quote", content: line.slice(2).trim() });
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push({ type: "bullet", content: line.slice(2).trim() });
    } else if (/^\d+\.\s/.test(line)) {
      elements.push({ type: "number", content: line.replace(/^\d+\.\s/, "").trim() });
    } else if (line.startsWith("$$")) {
      // Display math - collect until closing $$
      if (line.endsWith("$$") && line.length > 4) {
        elements.push({ type: "math", content: line.slice(2, -2).trim() });
      } else {
        let mathContent = line.slice(2);
        while (i + 1 < lines.length && !lines[i + 1].startsWith("$$")) {
          i++;
          mathContent += " " + lines[i];
        }
        if (i + 1 < lines.length) i++; // skip closing $$
        elements.push({ type: "math", content: mathContent.trim() });
      }
    } else if (line === "---" || line === "***") {
      elements.push({ type: "hr" });
    } else if (line === "\\newpage") {
      elements.push({ type: "pagebreak" });
    } else if (line.trim() === "") {
      // skip blank lines
    } else {
      elements.push({ type: "para", content: line });
    }
  }

  // Flush remaining table
  if (inTable && tableRows.length > 0) {
    elements.push({ type: "table", rows: tableRows });
  }

  return elements;
}

// --- TEXT FORMATTING ---
function formatInlineText(text) {
  const runs = [];
  // Split by bold, italic, code, and LaTeX inline
  const regex = /(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`([^`]+)`|\$([^$]+)\$)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      runs.push(new TextRun({ text: text.slice(lastIndex, match.index), font: "Times New Roman", size: 24 }));
    }
    if (match[2]) { // bold italic
      runs.push(new TextRun({ text: match[2], bold: true, italics: true, font: "Times New Roman", size: 24 }));
    } else if (match[3]) { // bold
      runs.push(new TextRun({ text: match[3], bold: true, font: "Times New Roman", size: 24 }));
    } else if (match[4]) { // italic
      runs.push(new TextRun({ text: match[4], italics: true, font: "Times New Roman", size: 24 }));
    } else if (match[5]) { // inline code
      runs.push(new TextRun({ text: match[5], font: "Courier New", size: 20, shading: { fill: "E8E8E8", type: ShadingType.CLEAR } }));
    } else if (match[6]) { // inline math
      runs.push(new TextRun({ text: match[6], italics: true, font: "Cambria Math", size: 24 }));
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    runs.push(new TextRun({ text: text.slice(lastIndex), font: "Times New Roman", size: 24 }));
  }
  if (runs.length === 0) {
    runs.push(new TextRun({ text: text, font: "Times New Roman", size: 24 }));
  }
  return runs;
}

// --- ELEMENT TO DOCX ---
function elementToDocx(el, numbering) {
  switch (el.type) {
    case "h1":
      return [
        new Paragraph({ children: [new PageBreak()] }),
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 480, after: 240 },
          children: [new TextRun({ text: el.content.replace(/\*/g, ""), bold: true, font: "Times New Roman", size: 32 })]
        })
      ];
    case "h2":
      return [new Paragraph({
        heading: HeadingLevel.HEADING_2,
        spacing: { before: 360, after: 180 },
        children: [new TextRun({ text: el.content.replace(/\*/g, ""), bold: true, font: "Times New Roman", size: 28 })]
      })];
    case "h3":
      return [new Paragraph({
        heading: HeadingLevel.HEADING_3,
        spacing: { before: 240, after: 120 },
        children: [new TextRun({ text: el.content.replace(/\*/g, ""), bold: true, italics: true, font: "Times New Roman", size: 24 })]
      })];
    case "h4":
      return [new Paragraph({
        spacing: { before: 180, after: 100 },
        children: [new TextRun({ text: el.content.replace(/\*/g, ""), bold: true, font: "Times New Roman", size: 24 })]
      })];
    case "para":
      return [new Paragraph({
        spacing: { after: 120, line: 360 },
        children: formatInlineText(el.content)
      })];
    case "quote":
      return [new Paragraph({
        spacing: { after: 120, line: 360 },
        indent: { left: 720, right: 720 },
        children: [new TextRun({ text: el.content.replace(/\*/g, ""), italics: true, font: "Times New Roman", size: 24, color: "444444" })]
      })];
    case "bullet":
      return [new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        spacing: { after: 60, line: 360 },
        children: formatInlineText(el.content)
      })];
    case "number":
      return [new Paragraph({
        numbering: { reference: "numbers", level: 0 },
        spacing: { after: 60, line: 360 },
        children: formatInlineText(el.content)
      })];
    case "math":
      return [new Paragraph({
        spacing: { before: 120, after: 120, line: 360 },
        alignment: AlignmentType.CENTER,
        indent: { left: 360, right: 360 },
        children: [new TextRun({ text: el.content, italics: true, font: "Cambria Math", size: 24 })]
      })];
    case "code":
      return el.content.split("\n").map(codeLine =>
        new Paragraph({
          spacing: { after: 0, line: 240 },
          shading: { fill: "F0F0F0", type: ShadingType.CLEAR },
          indent: { left: 360, right: 360 },
          children: [new TextRun({ text: codeLine || " ", font: "Courier New", size: 18 })]
        })
      );
    case "table":
      return [buildTable(el.rows)];
    case "hr":
      return [new Paragraph({
        spacing: { before: 120, after: 120 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "888888", space: 1 } },
        children: [new TextRun({ text: "" })]
      })];
    case "pagebreak":
      return [new Paragraph({ children: [new PageBreak()] })];
    default:
      return [];
  }
}

// --- TABLE BUILDER ---
function buildTable(rows) {
  if (rows.length === 0) return new Paragraph({ children: [] });
  const numCols = Math.max(...rows.map(r => r.length));
  const colWidth = Math.floor(CONTENT_WIDTH / numCols);
  const border = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
  const borders = { top: border, bottom: border, left: border, right: border };

  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: Array(numCols).fill(colWidth),
    rows: rows.map((row, rowIdx) =>
      new TableRow({
        children: Array(numCols).fill(null).map((_, colIdx) => {
          const cellText = (row[colIdx] || "").trim();
          const isHeader = rowIdx === 0;
          return new TableCell({
            borders,
            width: { size: colWidth, type: WidthType.DXA },
            shading: isHeader ? { fill: "2C3E50", type: ShadingType.CLEAR } : undefined,
            margins: { top: 40, bottom: 40, left: 80, right: 80 },
            children: [new Paragraph({
              spacing: { after: 0 },
              children: [new TextRun({
                text: cellText.replace(/\*\*/g, ""),
                bold: isHeader,
                font: "Times New Roman",
                size: 20,
                color: isHeader ? "FFFFFF" : "000000"
              })]
            })]
          });
        })
      })
    )
  });
}

// --- MAIN BUILD ---
async function build() {
  console.log("Reading markdown files...");
  let allElements = [];

  for (const file of FILES) {
    const path = `${__dirname}/${file}`;
    console.log(`  Processing ${file}...`);
    const text = fs.readFileSync(path, "utf8");
    const elements = parseMarkdown(text);
    allElements = allElements.concat(elements);
  }

  console.log(`Parsed ${allElements.length} elements total.`);

  // Convert to docx paragraphs
  let children = [];
  for (const el of allElements) {
    const docxEls = elementToDocx(el);
    children = children.concat(docxEls);
  }

  console.log(`Generated ${children.length} docx paragraphs.`);

  // Build document
  const doc = new Document({
    styles: {
      default: {
        document: {
          run: { font: "Times New Roman", size: 24 }
        }
      },
      paragraphStyles: [
        {
          id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 32, bold: true, font: "Times New Roman", color: "1A1A2E" },
          paragraph: { spacing: { before: 480, after: 240 }, outlineLevel: 0 }
        },
        {
          id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 28, bold: true, font: "Times New Roman", color: "16213E" },
          paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 1 }
        },
        {
          id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 24, bold: true, italics: true, font: "Times New Roman", color: "0F3460" },
          paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 }
        },
      ]
    },
    numbering: {
      config: [
        {
          reference: "bullets",
          levels: [{
            level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } }
          }]
        },
        {
          reference: "numbers",
          levels: [{
            level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } }
          }]
        },
      ]
    },
    sections: [
      // Title page
      {
        properties: {
          page: {
            size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
            margin: { top: 4320, right: MARGIN, bottom: MARGIN, left: MARGIN }
          }
        },
        children: [
          new Paragraph({ spacing: { after: 600 }, alignment: AlignmentType.CENTER, children: [] }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 200 },
            children: [new TextRun({ text: "NietzscheDB", font: "Times New Roman", size: 72, bold: true, color: "1A1A2E" })]
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 400 },
            children: [new TextRun({ text: "O Abismo que Te Observa", font: "Times New Roman", size: 48, italics: true, color: "333333" })]
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 120 },
            border: { top: { style: BorderStyle.SINGLE, size: 3, color: "888888", space: 8 } },
            children: [new TextRun({ text: " ", size: 12 })]
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 200 },
            children: [new TextRun({ text: "Arquitetura Multi-Manifold e a Pragm\u00e1tica da Vontade de Pot\u00eancia", font: "Times New Roman", size: 28, color: "555555" })]
          }),
          new Paragraph({ spacing: { after: 1200 }, children: [] }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 200 },
            children: [new TextRun({ text: "Jose R F Junior", font: "Times New Roman", size: 32, bold: true })]
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 200 },
            children: [new TextRun({ text: "Primeira Edi\u00e7\u00e3o \u2014 Mar\u00e7o 2026", font: "Times New Roman", size: 24, color: "666666" })]
          }),
        ]
      },
      // TOC page
      {
        properties: {
          page: {
            size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
            margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }
          }
        },
        children: [
          new Paragraph({
            heading: HeadingLevel.HEADING_1,
            children: [new TextRun({ text: "\u00cdndice", font: "Times New Roman", size: 32, bold: true })]
          }),
          new TableOfContents("Table of Contents", {
            hyperlink: true,
            headingStyleRange: "1-3",
          }),
        ]
      },
      // Main content
      {
        properties: {
          page: {
            size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
            margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }
          }
        },
        headers: {
          default: new Header({
            children: [new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({ text: "NietzscheDB: O Abismo que Te Observa", font: "Times New Roman", size: 18, italics: true, color: "999999" })]
            })]
          })
        },
        footers: {
          default: new Footer({
            children: [new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "\u2014 ", font: "Times New Roman", size: 18, color: "999999" }),
                new TextRun({ children: [PageNumber.CURRENT], font: "Times New Roman", size: 18, color: "999999" }),
                new TextRun({ text: " \u2014", font: "Times New Roman", size: 18, color: "999999" }),
              ]
            })]
          })
        },
        children: children
      }
    ]
  });

  console.log("Generating .docx buffer...");
  const buffer = await Packer.toBuffer(doc);
  const outPath = `${__dirname}/NietzscheDB_O_Abismo_que_Te_Observa.docx`;
  fs.writeFileSync(outPath, buffer);
  console.log(`\nDone! Wrote ${(buffer.length / 1024 / 1024).toFixed(2)} MB to ${outPath}`);
  console.log(`Total paragraphs: ${children.length}`);
}

build().catch(err => {
  console.error("Error:", err);
  process.exit(1);
});

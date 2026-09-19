import { escapeHtml, raw } from "./html.js";

/** Escape first, then add the few inline elements the AI analysis uses. */
function renderInline(text) {
    return escapeHtml(text)
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

/**
 * Render the small Markdown subset produced by the AI analysis:
 * `##` headings, bullet and numbered lists, paragraphs, **bold** and `code`.
 * Input is always escaped, so the result is safe to insert into the page.
 */
export function renderMarkdown(source) {
    const blocks = [];
    let paragraph = [];
    let list = null;

    const flushParagraph = () => {
        if (paragraph.length) {
            blocks.push(`<p>${renderInline(paragraph.join(" "))}</p>`);
            paragraph = [];
        }
    };

    const flushList = () => {
        if (list) {
            blocks.push(`<${list.tag}>${list.items.join("")}</${list.tag}>`);
            list = null;
        }
    };

    const addListItem = (tag, text) => {
        flushParagraph();

        if (list && list.tag !== tag) {
            flushList();
        }

        list ??= { tag, items: [] };
        list.items.push(`<li>${renderInline(text)}</li>`);
    };

    for (const line of String(source ?? "").split(/\r?\n/)) {
        const heading = line.match(/^#{1,6}\s+(.*)$/);
        const bullet = line.match(/^\s*[-*]\s+(.*)$/);
        const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);

        if (heading) {
            flushParagraph();
            flushList();
            blocks.push(`<h4>${renderInline(heading[1])}</h4>`);
        } else if (bullet) {
            addListItem("ul", bullet[1]);
        } else if (numbered) {
            addListItem("ol", numbered[1]);
        } else if (line.trim() === "") {
            flushParagraph();
            flushList();
        } else {
            flushList();
            paragraph.push(line.trim());
        }
    }

    flushParagraph();
    flushList();

    return raw(blocks.join(""));
}

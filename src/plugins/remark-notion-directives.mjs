import { visit } from 'unist-util-visit';

// Turns the container directives emitted by the Notion exporter
//   :::callout{icon="💡"} ... :::
//   :::bookmark{url="..."} title :::
//   :::embed{url="..."} caption :::
// into HTML nodes carrying react-notion-x class names, so the vendored
// Notion stylesheet renders them. No per-post component imports needed.
export default function remarkNotionDirectives() {
  return (tree) => {
    visit(tree, (node) => {
      if (node.type !== 'containerDirective') return;
      const attrs = node.attributes || {};

      if (node.name === 'callout') {
        const icon = attrs.icon || '💡';
        node.data = {
          hName: 'div',
          hProperties: { className: ['notion-callout', 'notion-gray_co'] },
        };
        // prepend the icon span; keep the directive's children as the body
        node.children = [
          {
            type: 'html',
            value: `<div class="notion-page-icon-inline notion-page-icon-span"><span class="notion-page-icon" role="img" aria-label="${icon}">${icon}</span></div>`,
          },
          {
            type: 'paragraph',
            data: { hName: 'div', hProperties: { className: ['notion-callout-text'] } },
            children: node.children,
          },
        ];
        return;
      }

      if (node.name === 'figure') {
        const src = attrs.src || '';
        const alt = attrs.alt || textOf(node);
        const hasCaption = node.children && node.children.length > 0;
        node.data = { hName: 'figure', hProperties: { className: ['notion-figure'] } };
        const img = {
          type: 'html',
          value: `<img src="${esc(src)}" alt="${esc(alt)}" loading="lazy" />`,
        };
        if (hasCaption) {
          node.children = [
            img,
            {
              type: 'paragraph',
              data: { hName: 'figcaption', hProperties: { className: ['notion-asset-caption'] } },
              children: node.children,
            },
          ];
        } else {
          node.children = [img];
        }
        return;
      }

      if (node.name === 'bookmark') {
        const url = attrs.url || '#';
        const label = textOf(node) || url;
        node.data = { hName: 'div', hProperties: { className: ['notion-row'] } };
        node.children = [
          {
            type: 'html',
            value:
              `<a class="notion-bookmark" href="${esc(url)}" target="_blank" rel="noopener noreferrer">` +
              `<div><div class="notion-bookmark-title">${esc(label)}</div>` +
              `<div class="notion-bookmark-link"><div class="notion-bookmark-link-text">${esc(url)}</div></div>` +
              `</div></a>`,
          },
        ];
        return;
      }

      if (node.name === 'embed') {
        const url = attrs.url || '#';
        node.data = { hName: 'div', hProperties: { className: ['notion-row'] } };
        node.children = [
          {
            type: 'html',
            value:
              `<a class="notion-bookmark" href="${esc(url)}" target="_blank" rel="noopener noreferrer">` +
              `<div><div class="notion-bookmark-link"><div class="notion-bookmark-link-text">${esc(url)}</div></div></div></a>`,
          },
        ];
        return;
      }
    });
  };
}

function textOf(node) {
  let out = '';
  visit(node, 'text', (t) => {
    out += t.value;
  });
  return out.trim();
}

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

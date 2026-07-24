import { visit } from 'unist-util-visit';

// Maps plain Markdown-generated HTML elements onto the class names that
// react-notion-x's stylesheet targets, so the vendored Notion CSS applies
// to Astro's Markdown output without shipping the Notion renderer.
const TAG_CLASS = {
  h1: 'notion-h notion-h1',
  h2: 'notion-h notion-h2',
  h3: 'notion-h notion-h3',
  p: 'notion-text',
  blockquote: 'notion-quote',
  hr: 'notion-hr',
  ul: 'notion-list notion-list-disc',
  ol: 'notion-list notion-list-numbered',
  table: 'notion-simple-table',
};

function addClass(node, cls) {
  node.properties = node.properties || {};
  const existing = node.properties.className || [];
  const list = Array.isArray(existing) ? existing : [existing];
  node.properties.className = [...list, ...cls.split(' ')];
}

export default function rehypeNotionClasses() {
  return (tree) => {
    visit(tree, 'element', (node) => {
      const cls = TAG_CLASS[node.tagName];
      if (cls) addClass(node, cls);

      // Links inside prose (skip anchor links added elsewhere)
      if (node.tagName === 'a') addClass(node, 'notion-link');

      // Standalone code blocks: <pre><code> → wrap class for the Notion code look
      if (node.tagName === 'pre') addClass(node, 'notion-code');

      // Inline code (a <code> not inside a <pre>)
      if (node.tagName === 'code' && !node.properties?.className) {
        addClass(node, 'notion-inline-code');
      }
    });
  };
}

// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

import remarkDirective from 'remark-directive';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

import remarkNotionDirectives from './src/plugins/remark-notion-directives.mjs';
import rehypeNotionClasses from './src/plugins/rehype-notion-classes.mjs';

// https://astro.build/config
export default defineConfig({
	site: 'https://flagrantsystemerror.com',
	integrations: [mdx(), sitemap()],
	markdown: {
		remarkPlugins: [remarkDirective, remarkNotionDirectives, remarkMath],
		rehypePlugins: [rehypeKatex, rehypeNotionClasses],
		shikiConfig: { theme: 'github-light' },
	},
});

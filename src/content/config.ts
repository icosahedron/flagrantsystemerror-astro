import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
	type: 'content',
	schema: z.object({
		title: z.string(),
		description: z.string().optional(),
		pubDate: z.coerce.date(),
		updatedDate: z.coerce.date().optional(),
		heroImage: z.string().optional(),
		heroImagePosition: z.number().optional(),
		icon: z.string().optional(),
		// Mirrors Notion's "Public" checkbox. When false the post is hidden from
		// the production build (no page, not in archive/RSS) but still viewable
		// via `npm run dev`. Defaults true so a missing field publishes.
		public: z.boolean().default(true),
	}),
});

// Standalone pages (About, Colophon): authored like posts but kept out of
// the blog index and RSS feed.
const pages = defineCollection({
	type: 'content',
	schema: z.object({
		title: z.string(),
		description: z.string().optional(),
		pubDate: z.coerce.date().optional(),
		updatedDate: z.coerce.date().optional(),
		heroImage: z.string().optional(),
		heroImagePosition: z.number().optional(),
		icon: z.string().optional(),
	}),
});

export const collections = { blog, pages };

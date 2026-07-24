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
		// Hidden from the production build (no page, not in archive/RSS) but
		// still viewable via `npm run dev`.
		draft: z.boolean().default(false),
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

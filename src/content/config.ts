import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  schema: z.object({
    title: z.object({
      zh: z.string(),
      en: z.string()
    }),
    description: z.object({
      zh: z.string(),
      en: z.string()
    }),
    date: z.string().transform((str) => new Date(str)),
    category: z.string(),
    tags: z.array(z.string()).optional(),
    draft: z.boolean().default(false),
    author: z.string().default('James Xie'),
    ogImage: z.string().optional()
  }),
});

export const collections = {
  blog,
};
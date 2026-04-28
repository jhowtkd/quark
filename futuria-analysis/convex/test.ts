import { mutation } from "./_generated.js";
import { v } from "convex/values";

export const hello = mutation({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    return `Hello, ${args.name}!`;
  },
});

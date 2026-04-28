import { mutation } from "./_generated.js";
import { v } from "convex/values";

export const minimal = mutation({
  args: { test: v.string() },
  handler: async (ctx, args) => {
    return { result: "ok", input: args.test };
  },
});

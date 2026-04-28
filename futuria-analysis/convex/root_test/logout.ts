import { mutation } from "../_generated.js";

export const logout = mutation({
  args: {},
  handler: async (_ctx) => {
    // In stateless token-based auth, the client discards the token.
    // This mutation confirms the logout request was received.
    return { success: true, message: "Logged out successfully" };
  },
});

# Authentication System Design

**Date:** 2026-04-13  
**Author:** Brainstorming Session  
**Status:** Draft

---

## Overview

Add authentication to Quark using **Better Auth** (frontend) + **Convex** (backend/users database). This enables user accounts, protected routes, and user-specific simulation storage.

---

## Architecture

```
Frontend (Vue 3)
├── Better Auth (auth state, form handling)
├── Vue Router (route guards)
└── Convex Client (API calls)

Backend Services
├── Convex (users table, auth handlers)
└── Flask (simulations - unchanged)
```

---

## Convex Schema

```typescript
// convex/schema.ts

import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  users: defineTable({
    email: v.string(),
    hashedPassword: v.string(),
    name: v.string(),
    createdAt: v.number(),
  }).index("by_email", ["email"]),
});
```

---

## Convex Auth Functions

| Function | Description |
|----------|-------------|
| `auth.register` | Create user with hashed password |
| `auth.login` | Validate credentials, return session |
| `auth.logout` | Clear session |
| `auth.me` | Get current user info |

---

## Frontend Pages

| Route | Description | Auth Required |
|-------|-------------|--------------|
| `/` | Home/Dashboard | Yes |
| `/login` | Login form | No |
| `/register` | Registration form | No |
| `/profile` | User profile | Yes |
| `/simulation/:id` | Simulation view | Yes |

---

## Components to Create

### Backend (Convex)

1. `convex/schema.ts` - Users table definition
2. `convex/auth/register.ts` - Registration handler
3. `convex/auth/login.ts` - Login handler
4. `convex/auth/logout.ts` - Logout handler

### Frontend (Vue)

1. `frontend/src/pages/LoginPage.vue` - Login form
2. `frontend/src/pages/RegisterPage.vue` - Registration form
3. `frontend/src/pages/ProfilePage.vue` - User profile
4. `frontend/src/router/auth.ts` - Router middleware
5. `frontend/src/composables/useAuth.ts` - Auth composable

---

## Integration Points

### Vue Router Guard

```typescript
// Protecting routes that need auth
{
  path: '/simulation/:id',
  component: SimulationView,
  beforeEnter: requireAuth
}
```

### Simulation API Changes

- Add `userId` to simulation records (owner tracking)
- Filter simulations by `userId` in list queries

---

## Security Considerations

- Passwords hashed with bcrypt (via Convex `Password hf`)
- Session tokens in HTTP-only cookies
- CSRF protection via Convex built-in
- Rate limiting on auth endpoints (Convex built-in)

---

## Migration Plan

### Phase 1: Backend Setup
- [ ] Create Convex project
- [ ] Define schema
- [ ] Implement auth functions

### Phase 2: Frontend Integration
- [ ] Install better-auth
- [ ] Create login/register pages
- [ ] Add route guards

### Phase 3: Protect Existing Features
- [ ] Add auth to simulation routes
- [ ] Associate simulations with users

---

## What This Does NOT Include

- OAuth providers (Google, GitHub)
- Password reset flow
- Email verification
- Role-based access control (admin/user)
- Team/workspace features

---

## Files to Modify/Create

| File | Action |
|------|--------|
| `convex/schema.ts` | Create |
| `convex/auth/*.ts` | Create |
| `frontend/src/router/index.ts` | Modify |
| `frontend/src/pages/*.vue` | Create |
| `frontend/src/composables/useAuth.ts` | Create |

---

## Next Step

After user approval → Create implementation plan (writing-plans skill)
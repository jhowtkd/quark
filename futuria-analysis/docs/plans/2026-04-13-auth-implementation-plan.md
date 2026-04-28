# Authentication System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add authentication to Quark using Better Auth (frontend) + Convex (backend/users)

**Architecture:** Convex handles user registration/login with bcrypt password hashing. Better Auth manages auth state in Vue. Vue Router guards protect simulation routes. Flask simulation backend remains unchanged.

**Tech Stack:** Convex, Better Auth, Vue Router 4, bcrypt

---

## Prerequisites

Before starting, verify these are installed:
- Node.js 18+
- npm/pnpm
- Git

---

## Task 1: Initialize Convex Project

**Files:**
- Create: `convex/schema.ts`
- Create: `convex/tsconfig.json`
- Create: `convex/convex.json`

**Step 1: Install Convex CLI**

```bash
npm install convex
```

**Step 2: Initialize Convex project**

```bash
npx convex init
```

When prompted, choose:
- "Don't link to an existing project" (we'll create a new one)
- Project name: `quark-auth`
- Configure deployment: we'll do this later

**Step 3: Verify Convex structure**

```bash
ls -la convex/
```

Expected output:
```
convex.json
tsconfig.json
```

---

## Task 2: Define Users Schema

**Files:**
- Modify: `convex/schema.ts`

**Step 1: Write the schema**

Create `convex/schema.ts`:

```typescript
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

**Step 2: Verify schema is valid**

```bash
npx convex lint
```

Expected: No errors

---

## Task 3: Create Auth API Functions

**Files:**
- Create: `convex/auth/register.ts`
- Create: `convex/auth/login.ts`
- Create: `convex/auth/logout.ts`

**Step 1: Create auth/register.ts**

```typescript
import { mutation } from "./_generated/server";
import { Password } from "convex/password";

export const register = mutation({
  args: {
    email: v.string(),
    password: v.string(),
    name: v.string(),
  },
  handler: async (ctx, args) => {
    // Check if user exists
    const existing = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();

    if (existing) {
      throw new Error("User already exists");
    }

    // Hash password and create user
    const hashedPassword = await Password.hash(args.password);

    await ctx.db.insert("users", {
      email: args.email,
      hashedPassword,
      name: args.name,
      createdAt: Date.now(),
    });
  },
});
```

**Step 2: Create auth/login.ts**

```typescript
import { mutation } from "./_generated/server";
import { Password } from "convex/password";

export const login = mutation({
  args: {
    email: v.string(),
    password: v.string(),
  },
  handler: async (ctx, args) => {
    const user = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();

    if (!user) {
      throw new Error("Invalid credentials");
    }

    const valid = await Password.verify(user.hashedPassword, args.password);

    if (!valid) {
      throw new Error("Invalid credentials");
    }

    // Return user (without password)
    return {
      userId: user._id,
      email: user.email,
      name: user.name,
    };
  },
});
```

**Step 3: Create auth/logout.ts**

```typescript
import { mutation } from "./_generated/server";

export const logout = mutation({
  args: {},
  handler: async (ctx) => {
    // Convex handles session cleanup automatically
    return { success: true };
  },
});
```

---

## Task 4: Install Better Auth

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install better-auth**

```bash
cd frontend
npm install better-auth vue-router
```

**Step 2: Verify installation**

```bash
cat package.json | grep -E "better-auth|vue-router"
```

Expected output showing both packages

---

## Task 5: Create Login Page

**Files:**
- Create: `frontend/src/pages/LoginPage.vue`

**Step 1: Write the component**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation } from '@convex/vue'
import { api } from '../../convex/_generated/api'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const login = useMutation(api.auth.login)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  
  try {
    const result = await login({
      email: email.value,
      password: password.value,
    })
    
    // Redirect to home after successful login
    router.push('/')
  } catch (e) {
    error.value = e.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <h1>Login</h1>
    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label>Email</label>
        <input v-model="email" type="email" required />
      </div>
      <div class="field">
        <label>Password</label>
        <input v-model="password" type="password" required />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
    <p>
      Don't have an account? <router-link to="/register">Register</router-link>
    </p>
  </div>
</template>

<style scoped>
.auth-page {
  max-width: 400px;
  margin: 2rem auto;
  padding: 2rem;
}
.field {
  margin-bottom: 1rem;
}
.error {
  color: red;
}
</style>
```

---

## Task 6: Create Register Page

**Files:**
- Create: `frontend/src/pages/RegisterPage.vue`

**Step 1: Write the component**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation } from '@convex/vue'
import { api } from '../../convex/_generated/api'

const router = useRouter()
const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

const register = useMutation(api.auth.register)

async function handleSubmit() {
  error.value = ''
  
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  
  loading.value = true
  
  try {
    await register({
      email: email.value,
      password: password.value,
      name: name.value,
    })
    
    // Redirect to login after successful registration
    router.push('/login')
  } catch (e) {
    error.value = e.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <h1>Create Account</h1>
    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label>Name</label>
        <input v-model="name" type="text" required />
      </div>
      <div class="field">
        <label>Email</label>
        <input v-model="email" type="email" required />
      </div>
      <div class="field">
        <label>Password</label>
        <input v-model="password" type="password" required minlength="8" />
      </div>
      <div class="field">
        <label>Confirm Password</label>
        <input v-model="confirmPassword" type="password" required />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Creating account...' : 'Register' }}
      </button>
    </form>
    <p>
      Already have an account? <router-link to="/login">Login</router-link>
    </p>
  </div>
</template>

<style scoped>
.auth-page {
  max-width: 400px;
  margin: 2rem auto;
  padding: 2rem;
}
.field {
  margin-bottom: 1rem;
}
.error {
  color: red;
}
</style>
```

---

## Task 7: Create Auth Composable

**Files:**
- Create: `frontend/src/composables/useAuth.ts`

**Step 1: Write the composable**

```typescript
import { ref, computed } from 'vue'
import { useQuery } from '@convex/vue'
import { api } from '../../convex/_generated/api'

const currentUser = ref<{ userId: string; email: string; name: string } | null>(null)
const isAuthenticated = computed(() => !!currentUser.value)

export function useAuth() {
  return {
    currentUser,
    isAuthenticated,
    async logout() {
      // Clear user state
      currentUser.value = null
    },
    setUser(user: typeof currentUser.value) {
      currentUser.value = user
    },
  }
}
```

---

## Task 8: Update Vue Router

**Files:**
- Modify: `frontend/src/router/index.ts`

**Step 1: Add auth routes and guards**

Add to router:

```typescript
import LoginPage from '@/pages/LoginPage.vue'
import RegisterPage from '@/pages/RegisterPage.vue'

// Add to routes array:
{
  path: '/login',
  component: LoginPage,
  meta: { requiresAuth: false }
},
{
  path: '/register',
  component: RegisterPage,
  meta: { requiresAuth: false }
}

// Add navigation guard:
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !isAuthenticated.value) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && isAuthenticated.value) {
    next('/')
  } else {
    next()
  }
})
```

---

## Task 9: Configure Convex Client in Vue

**Files:**
- Modify: `frontend/src/main.js`

**Step 1: Add Convex provider**

```javascript
import { ConvexProvider } from '@convex/vue'

createApp(App)
  .use(router)
  .use(i18n)
  .provide('convex', convex)
  .mount('#app')
```

---

## Task 10: Update Home Page Login Link

**Files:**
- Modify: `frontend/src/views/Home.vue`

**Step 1: Add login button**

Add a login button in the navbar or hero section:

```vue
<router-link to="/login" class="btn-login">
  Login
</router-link>
```

---

## Testing Checklist

After implementation, verify:

- [ ] Can register a new user
- [ ] Can login with valid credentials
- [ ] Cannot login with invalid credentials
- [ ] Protected routes redirect to login
- [ ] Logged-in users cannot access login/register pages
- [ ] Logout clears session

---

## Commit Strategy

Commit after each task:

```bash
git add .
git commit -m "feat(auth): [task description]"
```

---

## Next Steps After Implementation

1. Deploy Convex (run `npx convex deploy`)
2. Set Convex deployment URL in frontend
3. Test auth flow end-to-end

---

**Plan complete and saved to `docs/plans/2026-04-13-auth-implementation-plan.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
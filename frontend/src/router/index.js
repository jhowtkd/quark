import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import { isAuthenticated } from '../api/auth.js'

// Lazy-loaded route components
const LoginPage = () => import('../views/LoginPage.vue')
const RegisterPage = () => import('../views/RegisterPage.vue')
const Process = () => import('../views/MainView.vue')
const SimulationView = () => import('../views/SimulationView.vue')
const SimulationRunView = () => import('../views/SimulationRunView.vue')
const ReportView = () => import('../views/ReportView.vue')
const InteractionView = () => import('../views/InteractionView.vue')
const TriageView = () => import('../views/TriageView.vue')

// Routes that require authentication
const PROTECTED_ROUTES = ['Home', 'Process', 'Simulation', 'SimulationRun', 'Report', 'Interaction']

// Routes only for guests (logged out users)
const GUEST_ONLY_ROUTES = ['Login', 'Register']

/**
 * Navigation guard to protect routes requiring authentication
 */
const requireAuth = (to, from, next) => {
  if (PROTECTED_ROUTES.includes(to.name)) {
    if (!isAuthenticated()) {
      // Store intended destination for redirect after login
      const redirectPath = to.fullPath !== '/' ? to.fullPath : null
      const query = redirectPath ? { redirect: redirectPath } : {}
      next({ name: 'Login', query })
      return
    }
  }
  next()
}

/**
 * Navigation guard to redirect authenticated users away from guest routes
 */
const guestOnly = (to, from, next) => {
  if (GUEST_ONLY_ROUTES.includes(to.name) && isAuthenticated()) {
    // Redirect authenticated users to home
    next({ name: 'Home' })
    return
  }
  next()
}

/**
 * Handle redirect after login if user was trying to access protected route
 */
const handleLoginRedirect = (to, from, next) => {
  if (to.name === 'Login' && to.query.redirect) {
    // User was redirected after attempted access to protected route
    // Proceed normally - the LoginPage component handles the redirect
  }
  next()
}

const routes = [
  {
    path: '/style-guide',
    name: 'StyleGuide',
    component: () => import('../views/StyleGuide.vue'),
  },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { guestOnly: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterPage,
    meta: { guestOnly: true }
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: Process,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/simulation/:simulationId',
    name: 'Simulation',
    component: SimulationView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: SimulationRunView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: ReportView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: InteractionView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/triage',
    name: 'Triage',
    component: TriageView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Register navigation guards
router.beforeEach(requireAuth)
router.beforeEach(guestOnly)

export default router

<template>
  <div class="login-page">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="nav-brand">FUTUR.IA</div>
      <div class="nav-links">
        <LanguageSwitcher />
      </div>
    </nav>

    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1 class="login-title">{{ $t('auth.login') }}</h1>
          <p class="login-subtitle">{{ $t('auth.loginSubtitle') }}</p>
        </div>

        <form @submit.prevent="handleLogin" class="login-form">
          <!-- Email Field -->
          <div class="form-group">
            <label for="email" class="form-label">{{ $t('auth.email') }}</label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              class="form-input"
              :class="{ 'input-error': errors.email }"
              :placeholder="$t('auth.emailPlaceholder')"
              @blur="validateEmail"
            />
            <span v-if="errors.email" class="error-message">{{ errors.email }}</span>
          </div>

          <!-- Password Field -->
          <div class="form-group">
            <label for="password" class="form-label">{{ $t('auth.password') }}</label>
            <div class="password-wrapper">
              <input
                id="password"
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                :class="{ 'input-error': errors.password }"
                :placeholder="$t('auth.passwordPlaceholder')"
                @blur="validatePassword"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? $t('auth.hidePassword') : $t('auth.showPassword')"
              >
                {{ showPassword ? '👁' : '👁‍🗨' }}
              </button>
            </div>
            <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
          </div>

          <!-- Error Alert -->
          <div v-if="loginError" class="alert alert-error">
            <span class="alert-icon">⚠</span>
            {{ $t(loginError) }}
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            class="login-button"
            :disabled="loading || !isFormValid"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>{{ $t('auth.loginButton') }}</span>
          </button>
        </form>

        <div class="login-footer">
          <p class="register-link">
            {{ $t('auth.noAccount') }}
            <router-link to="/register">{{ $t('auth.registerHere') }}</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { login as loginApi } from '../api/auth.js'

const router = useRouter()
const route = useRoute()

// Form state
const formData = ref({
  email: '',
  password: ''
})

const errors = ref({
  email: '',
  password: ''
})

const loading = ref(false)
const loginError = ref('')
const showPassword = ref(false)

// Validation
const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!formData.value.email) {
    errors.value.email = 'auth.errors.emailRequired'
  } else if (!emailRegex.test(formData.value.email)) {
    errors.value.email = 'auth.errors.invalidEmail'
  } else {
    errors.value.email = ''
  }
}

const validatePassword = () => {
  if (!formData.value.password) {
    errors.value.password = 'auth.errors.passwordRequired'
  } else if (formData.value.password.length < 6) {
    errors.value.password = 'auth.errors.passwordTooShort'
  } else {
    errors.value.password = ''
  }
}

const isFormValid = computed(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return (
    formData.value.email &&
    emailRegex.test(formData.value.email) &&
    formData.value.password &&
    formData.value.password.length >= 6
  )
})

// Login handler
const handleLogin = async () => {
  // Validate all fields
  validateEmail()
  validatePassword()

  if (!isFormValid.value) {
    return
  }

  loading.value = true
  loginError.value = ''

  try {
    const response = await loginApi({
      email: formData.value.email,
      password: formData.value.password
    })

    // Store user info
    localStorage.setItem('user', JSON.stringify(response))
    localStorage.setItem('isAuthenticated', 'true')

    // Redirect to intended destination or home
    const redirect = route.query.redirect
    if (redirect && typeof redirect === 'string') {
      router.push(redirect)
    } else {
      router.push('/')
    }
  } catch (error) {
    console.error('Login failed:', error)
    loginError.value = 'auth.errors.loginFailed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:root {
  --color-on-background: var(--color-on-background);
  --color-surface: var(--color-surface);
  --gray-light: var(--color-surface-container-low);
  --gray-text: var(--color-muted);
  --border: var(--color-outline);
  --error: var(--color-error);
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.login-page {
  min-height: 100vh;
  background: var(--color-surface);
  font-family: var(--font-sans);
  color: var(--color-on-background);
}

/* Navbar */
.navbar {
  height: 60px;
  background: var(--color-on-background);
  color: var(--color-surface);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: var(--font-mono);
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.2rem;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Login Container */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 60px);
  padding: 40px 20px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 48px;
  border: 1px solid var(--border);
  background: var(--color-surface);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-title {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--color-on-background);
}

.login-subtitle {
  color: var(--gray-text);
  margin: 0;
  font-size: 0.95rem;
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-on-background);
}

.form-input {
  width: 100%;
  padding: 14px 0px;
  border: none;
  border-bottom: 2px solid var(--color-muted);
  background: transparent;
  font-size: 1rem;
  font-family: var(--font-human);
  font-weight: 400;
  transition: border-color 0.2s;
  box-sizing: border-box;
  border-radius: 0px;
}

.form-input:focus {
  outline: none;
  border-bottom-color: var(--color-on-background);
}

.form-input.input-error {
  border-bottom-color: var(--color-error);
}

.password-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-wrapper .form-input {
  padding-right: 48px;
}

.password-toggle {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  font-size: 1.2rem;
}

.password-toggle:hover {
  opacity: 0.7;
}

.error-message {
  color: var(--error);
  font-size: 0.85rem;
}

/* Alert */
.alert {
  padding: 14px 16px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
}

.alert-error {
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-bg);
  color: var(--error);
}

.alert-icon {
  font-size: 1.1rem;
}

/* Button */
.login-button {
  width: 100%;
  padding: 16px;
  background: var(--color-on-background);
  color: var(--color-surface-container-highest);
  border: none;
  font-size: 1rem;
  font-weight: 600;
  font-family: var(--font-machine);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  border-radius: 0px;
}

.login-button:hover:not(:disabled) {
  background: var(--color-background);
  color: var(--color-on-background);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

.login-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top-color: var(--white);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Footer */
.login-footer {
  margin-top: 32px;
  text-align: center;
}

.register-link {
  color: var(--gray-text);
  font-size: 0.9rem;
}

.register-link a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
  }

  .login-title {
    font-size: 1.75rem;
  }
}
</style>

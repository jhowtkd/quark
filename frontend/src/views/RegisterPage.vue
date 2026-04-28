<template>
  <div class="register-page">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="nav-brand">FUTUR.IA</div>
      <div class="nav-links">
        <LanguageSwitcher />
      </div>
    </nav>

    <div class="register-container">
      <div class="register-card">
        <div class="register-header">
          <h1 class="register-title">{{ $t('auth.register') }}</h1>
          <p class="register-subtitle">{{ $t('auth.loginSubtitle') }}</p>
        </div>

        <form @submit.prevent="handleRegister" class="register-form">
          <!-- Name Field -->
          <div class="form-group">
            <label for="name" class="form-label">{{ $t('auth.name') }}</label>
            <input
              id="name"
              v-model="formData.name"
              type="text"
              class="form-input"
              :class="{ 'input-error': errors.name }"
              :placeholder="$t('auth.namePlaceholder')"
              @blur="validateName"
            />
            <span v-if="errors.name" class="error-message">{{ errors.name }}</span>
          </div>

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

          <!-- Confirm Password Field -->
          <div class="form-group">
            <label for="confirmPassword" class="form-label">{{ $t('auth.confirmPassword') }}</label>
            <div class="password-wrapper">
              <input
                id="confirmPassword"
                v-model="formData.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                class="form-input"
                :class="{ 'input-error': errors.confirmPassword }"
                :placeholder="$t('auth.confirmPasswordPlaceholder')"
                @blur="validateConfirmPassword"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showConfirmPassword = !showConfirmPassword"
                :aria-label="showConfirmPassword ? $t('auth.hidePassword') : $t('auth.showPassword')"
              >
                {{ showConfirmPassword ? '👁' : '👁‍🗨' }}
              </button>
            </div>
            <span v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</span>
          </div>

          <!-- Error Alert -->
          <div v-if="registerError" class="alert alert-error">
            <span class="alert-icon">⚠</span>
            {{ $t(registerError) }}
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            class="register-button"
            :disabled="loading || !isFormValid"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>{{ $t('auth.registerButton') }}</span>
          </button>
        </form>

        <div class="register-footer">
          <p class="login-link">
            {{ $t('auth.alreadyHaveAccount') }}
            <router-link to="/login">{{ $t('auth.loginHere') }}</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { register as registerApi } from '../api/auth.js'

const router = useRouter()

// Form state
const formData = ref({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const errors = ref({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const registerError = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

// Validation
const validateName = () => {
  if (!formData.value.name) {
    errors.value.name = 'auth.errors.nameRequired'
  } else {
    errors.value.name = ''
  }
}

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

const validateConfirmPassword = () => {
  if (!formData.value.confirmPassword) {
    errors.value.confirmPassword = 'auth.errors.passwordRequired'
  } else if (formData.value.password !== formData.value.confirmPassword) {
    errors.value.confirmPassword = 'auth.errors.passwordsDoNotMatch'
  } else {
    errors.value.confirmPassword = ''
  }
}

const isFormValid = computed(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return (
    formData.value.name &&
    formData.value.email &&
    emailRegex.test(formData.value.email) &&
    formData.value.password &&
    formData.value.password.length >= 6 &&
    formData.value.confirmPassword &&
    formData.value.password === formData.value.confirmPassword
  )
})

// Register handler
const handleRegister = async () => {
  // Validate all fields
  validateName()
  validateEmail()
  validatePassword()
  validateConfirmPassword()

  if (!isFormValid.value) {
    return
  }

  loading.value = true
  registerError.value = ''

  try {
    const response = await registerApi({
      name: formData.value.name,
      email: formData.value.email,
      password: formData.value.password
    })

    // Store user info
    localStorage.setItem('user', JSON.stringify(response))
    localStorage.setItem('isAuthenticated', 'true')

    // Redirect to home
    router.push('/')
  } catch (error) {
    console.error('Registration failed:', error)
    const msg = error?.message || ''
    if (msg.includes('User already exists')) {
      registerError.value = 'auth.errors.emailTaken'
    } else if (msg.includes('Server Error')) {
      registerError.value = 'auth.errors.registerFailed'
    } else {
      registerError.value = 'auth.errors.registerFailed'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:root {
  --black: #000000;
  --white: #FFFFFF;
  --gray-light: #F5F5F5;
  --gray-text: #666666;
  --border: #E5E5E5;
  --error: #DC3545;
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.register-page {
  min-height: 100vh;
  background: var(--white);
  font-family: var(--font-sans);
  color: var(--black);
}

/* Navbar */
.navbar {
  height: 60px;
  background: var(--black);
  color: var(--white);
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

/* Register Container */
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 60px);
  padding: 40px 20px;
}

.register-card {
  width: 100%;
  max-width: 420px;
  padding: 48px;
  border: 1px solid var(--border);
  background: var(--white);
}

.register-header {
  text-align: center;
  margin-bottom: 40px;
}

.register-title {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--black);
}

.register-subtitle {
  color: var(--gray-text);
  margin: 0;
  font-size: 0.95rem;
}

/* Form */
.register-form {
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
  color: var(--black);
}

.form-input {
  width: 100%;
  padding: 14px 0px;
  border: none;
  border-bottom: 2px solid #777777;
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
  border-bottom-color: #000000;
}

.form-input.input-error {
  border-bottom-color: #ba1a1a;
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
  background: #FFF5F5;
  border: 1px solid #FED7D7;
  color: var(--error);
}

.alert-icon {
  font-size: 1.1rem;
}

/* Button */
.register-button {
  width: 100%;
  padding: 16px;
  background: #000000;
  color: #e2e2e2;
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

.register-button:hover:not(:disabled) {
  background: #f9f9f9;
  color: #000000;
  box-shadow: 4px 4px 0 #000000;
}

.register-button:disabled {
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
.register-footer {
  margin-top: 32px;
  text-align: center;
}

.login-link {
  color: var(--gray-text);
  font-size: 0.9rem;
}

.login-link a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 480px) {
  .register-card {
    padding: 32px 24px;
  }

  .register-title {
    font-size: 1.75rem;
  }
}
</style>

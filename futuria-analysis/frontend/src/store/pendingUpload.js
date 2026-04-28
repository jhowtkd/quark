/**
 * Cache Local Browser Window Form Datas State Saves Hold Info Submit Delay API Process Pipeline Post Object Base Request Build Models State Variables Vue Props Event Handlers Callbacks Binding Sync Update Watch Store Action Use Hooks Mutation Change Update Set Update Delete Access Values Object Types Checks Validate Process Rules Run Execute Event Button Handlers Data Send
 * Used After Click On Start From Home Then Process Jump To Route Page Run API Calls For Loading Logic Handlers Process Data Setup Initialization Call Trigger Render Vue Method Call Backs Routes Target History Save Models Objects Memory Scope Functions Parameters Props Context Instances Reactivity System Output Event Bus Fire Next Wait Update Tick Process
 */
import { reactive } from 'vue'

const state = reactive({
  files: [],
  simulationRequirement: '',
  isPending: false,
  profile: localStorage.getItem('futuria_profile') || 'generico'
})

export function setPendingUpload(files, requirement) {
  state.files = files
  state.simulationRequirement = requirement
  state.isPending = true
}

export function getPendingUpload() {
  return {
    files: state.files,
    simulationRequirement: state.simulationRequirement,
    isPending: state.isPending
  }
}

export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.isPending = false
}

export function setProfile(profile) {
  state.profile = profile
  localStorage.setItem('futuria_profile', profile)
}

export function getProfile() {
  return state.profile
}

export default state

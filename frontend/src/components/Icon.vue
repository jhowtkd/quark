<template>
  <component :is="iconComponent" :size="size" :stroke-width="strokeWidth" />
</template>

<script setup>
import { computed } from 'vue'
import {
  Sun,
  Moon,
  Monitor,
  LogOut,
  ExternalLink,
  RefreshCw,
  Maximize2,
  Minimize2,
  ChevronDown,
  Diamond,
  Play,
  Check,
  X,
  Loader2,
  FileText,
  BarChart3,
  MessageSquare,
  Globe,
  AlertCircle,
  Info,
  Circle,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 20 },
  strokeWidth: { type: Number, default: 2 },
})

const ICON_MAP = {
  sun: Sun,
  moon: Moon,
  monitor: Monitor,
  'log-out': LogOut,
  'external-link': ExternalLink,
  'refresh-cw': RefreshCw,
  'maximize-2': Maximize2,
  'minimize-2': Minimize2,
  'chevron-down': ChevronDown,
  'chevron-up': ChevronUp,
  'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight,
  diamond: Diamond,
  play: Play,
  check: Check,
  x: X,
  'loader-2': Loader2,
  'file-text': FileText,
  'bar-chart-3': BarChart3,
  'message-square': MessageSquare,
  globe: Globe,
  'alert-circle': AlertCircle,
  info: Info,
  circle: Circle,
}

const iconComponent = computed(() => ICON_MAP[props.name] || null)
</script>

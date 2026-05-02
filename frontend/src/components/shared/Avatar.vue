<script setup lang="ts">
import type { PresenceStatus } from '@/types'
import PresenceDot from './PresenceDot.vue'

const props = withDefaults(
  defineProps<{
    src?: string | null
    name: string
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
    showPresence?: boolean
    presenceStatus?: PresenceStatus
  }>(),
  {
    src: null,
    size: 'md',
    showPresence: false,
    presenceStatus: 'offline',
  }
)

const sizeClasses: Record<string, string> = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
  xl: 'w-16 h-16 text-2xl',
}

function initials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}
</script>

<template>
  <div class="relative inline-flex flex-shrink-0">
    <img
      v-if="props.src"
      :src="props.src"
      :alt="props.name"
      class="rounded-full object-cover"
      :class="sizeClasses[props.size]"
    />
    <div
      v-else
      class="rounded-full bg-brand-100 text-brand-600 font-semibold flex items-center justify-center select-none"
      :class="sizeClasses[props.size]"
    >
      {{ initials(props.name) }}
    </div>

    <PresenceDot
      v-if="props.showPresence"
      :status="props.presenceStatus"
      class="absolute bottom-0 right-0 ring-2 ring-white dark:ring-surface-dark"
    />
  </div>
</template>

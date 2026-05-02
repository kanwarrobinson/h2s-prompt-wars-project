<script setup lang="ts">
import type { PresenceStatus } from '@/types'

withDefaults(
  defineProps<{ status?: PresenceStatus }>(),
  { status: 'offline' }
)
</script>

<template>
  <span
    class="block w-2.5 h-2.5 rounded-full"
    :class="{
      'bg-green-500': status === 'online',
      'bg-yellow-400': status === 'away',
      'bg-gray-400': status === 'offline',
    }"
  />
</template>

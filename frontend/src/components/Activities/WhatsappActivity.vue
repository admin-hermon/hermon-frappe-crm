<template>
  <div class="pb-5 mt-px">
    <div class="mb-4">
      <div class="flex items-center justify-stretch gap-2 text-base">
        <div class="inline-flex items-center flex-wrap gap-1.5 text-ink-gray-8 font-medium">
          <span class="font-medium">{{ activity.owner_name }}</span>
        </div>
        <div class="ml-auto whitespace-nowrap">
          <Tooltip :text="formatDate(activity.creation)">
            <div class="text-sm text-ink-gray-5">
              {{ __(timeAgo(activity.creation)) }}
            </div>
          </Tooltip>
        </div>
      </div>
      <div class="text-base">{{ activity.content }}</div>
    </div>
  </div>
</template>
<script setup>
import { Tooltip } from 'frappe-ui'
import { timeAgo, formatDate } from '@/utils'
defineProps({
  activity: {
    type: Object,
    required: true,
  },
})
</script> 
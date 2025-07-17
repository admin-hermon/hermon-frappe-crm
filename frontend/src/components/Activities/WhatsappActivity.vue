<template>
  <div class="pb-5 mt-px">
    <div class="mb-4">
      <div class="flex items-center justify-stretch gap-2 text-base">
        <div class="inline-flex items-center flex-wrap gap-1.5 text-gray-900 dark:text-gray-100 font-medium">
          <span class="font-medium">{{ activity.owner_name }}</span>
        </div>
        <div class="ml-auto whitespace-nowrap">
          <Tooltip :text="formatDate(activity.creation)">
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ __(timeAgo(activity.creation)) }}
            </div>
          </Tooltip>
        </div>
      </div>
      <div class="text-base text-gray-800 dark:text-gray-300">{{ activity.content }}</div>
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
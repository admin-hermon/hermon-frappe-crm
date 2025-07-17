<template>
  <div 
    v-if="powerDialer.isActive" 
    class="fixed bottom-4 left-4 z-10 rounded-lg border border-gray-200 bg-white p-4 shadow-lg dark:border-gray-700 dark:bg-gray-800 min-w-[300px]"
  >
    <div class="mb-3 flex items-center justify-between">
      <h3 class="font-semibold text-gray-800 dark:text-gray-200">Power Dialer</h3>
      <button 
        @click="powerDialer.endSession()"
        class="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
      >
        ✕
      </button>
    </div>
    
    <!-- Progress -->
    <div class="mb-3">
      <div class="mb-1 flex justify-between text-sm text-gray-600 dark:text-gray-400">
        <span>{{ powerDialer.completedLeads.length + 1 }} of {{ powerDialer.leads.length }}</span>
        <span>{{ powerDialer.remainingLeads.length }} remaining</span>
      </div>
      <div class="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
        <div 
          class="h-2 rounded-full bg-blue-600 transition-all" 
          :style="{ width: `${powerDialer.progressPercentage}%` }"
        ></div>
      </div>
    </div>
    
    <!-- Current Lead -->
    <div v-if="powerDialer.currentLead" class="mb-4 rounded bg-blue-50 p-3 dark:bg-gray-700">
      <div class="font-medium text-gray-800 dark:text-gray-200">{{ powerDialer.currentLead.lead_name }}</div>
      <div class="text-sm text-blue-600 dark:text-blue-400">{{ powerDialer.currentLead.primary_phone }}</div>
      <div v-if="powerDialer.currentLead.organization" class="text-xs text-gray-600 dark:text-gray-400">
        {{ powerDialer.currentLead.organization }}
      </div>
    </div>

    <!-- Status -->
    <div class="mb-4 text-center">
      <div v-if="powerDialer.isDialing" class="font-medium text-blue-600 dark:text-blue-400">
        📞 Calling...
      </div>
      <div v-else-if="powerDialer.isManualPause" class="font-medium text-orange-600 dark:text-orange-400">
        ⏸️ Session Paused
      </div>
      <div v-else-if="powerDialer.isPaused" class="font-medium text-yellow-600 dark:text-yellow-400">
        ⏳ Next call in {{ powerDialer.pauseCountdown }}s
      </div>
      <div v-else class="font-medium text-green-600 dark:text-green-400">
        ✅ Ready for next call
      </div>
    </div>

    <!-- Controls -->
    <div class="flex gap-2">
      <button 
        v-if="powerDialer.canPause && !powerDialer.isManualPause"
        @click="powerDialer.pauseSession()" 
        :disabled="powerDialer.isDialing"
        class="flex-1 rounded bg-orange-100 px-3 py-2 text-orange-700 hover:bg-orange-200 disabled:opacity-50 dark:bg-orange-900 dark:text-orange-300 dark:hover:bg-orange-800"
      >
        ⏸️ Pause
      </button>
      
      <button 
        v-if="powerDialer.canResume && powerDialer.isManualPause"
        @click="powerDialer.resumeSession()"
        class="flex-1 rounded bg-green-100 px-3 py-2 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800"
      >
        ▶️ Resume
      </button>

      <button 
        @click="powerDialer.skipLead()" 
        :disabled="powerDialer.isDialing"
        class="flex-1 rounded bg-gray-100 px-3 py-2 text-gray-700 hover:bg-gray-200 disabled:opacity-50 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
      >
        ⏭️ Skip
      </button>
    </div>
  </div>
</template>

<script setup>
import { powerDialerStore } from '@/stores/powerDialer'

const powerDialer = powerDialerStore()
</script> 
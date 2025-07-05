<template>
  <div 
    v-if="powerDialer.isActive" 
    class="fixed bottom-4 left-4 z-10 bg-white border-2 border-blue-200 rounded-lg shadow-lg p-4 min-w-[300px]"
  >
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-gray-800">Power Dialer</h3>
      <button 
        @click="powerDialer.endSession()"
        class="text-gray-400 hover:text-gray-600"
      >
        ✕
      </button>
    </div>
    
    <!-- Progress -->
    <div class="mb-3">
      <div class="flex justify-between text-sm text-gray-600 mb-1">
        <span>{{ powerDialer.completedLeads.length + 1 }} of {{ powerDialer.leads.length }}</span>
        <span>{{ powerDialer.remainingLeads.length }} remaining</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div 
          class="bg-blue-600 h-2 rounded-full transition-all" 
          :style="{ width: `${powerDialer.progressPercentage}%` }"
        ></div>
      </div>
    </div>
    
    <!-- Current Lead -->
    <div v-if="powerDialer.currentLead" class="mb-4 p-3 bg-blue-50 rounded">
      <div class="font-medium">{{ powerDialer.currentLead.lead_name }}</div>
      <div class="text-sm text-blue-600">{{ powerDialer.currentLead.primary_phone }}</div>
      <div v-if="powerDialer.currentLead.organization" class="text-xs text-gray-600">
        {{ powerDialer.currentLead.organization }}
      </div>
    </div>

    <!-- Status -->
    <div class="mb-4 text-center">
      <div v-if="powerDialer.isDialing" class="text-blue-600 font-medium">
        📞 Calling...
      </div>
      <div v-else-if="powerDialer.isManualPause" class="text-orange-600 font-medium">
        ⏸️ Session Paused
      </div>
      <div v-else-if="powerDialer.isPaused" class="text-yellow-600 font-medium">
        ⏳ Next call in {{ powerDialer.pauseCountdown }}s
      </div>
      <div v-else class="text-green-600 font-medium">
        ✅ Ready for next call
      </div>
    </div>

    <!-- Controls -->
    <div class="flex gap-2">
      <button 
        v-if="powerDialer.canPause && !powerDialer.isManualPause"
        @click="powerDialer.pauseSession()" 
        :disabled="powerDialer.isDialing"
        class="flex-1 px-3 py-2 bg-orange-100 text-orange-700 rounded hover:bg-orange-200 disabled:opacity-50"
      >
        ⏸️ Pause
      </button>
      
      <button 
        v-if="powerDialer.canResume && powerDialer.isManualPause"
        @click="powerDialer.resumeSession()"
        class="flex-1 px-3 py-2 bg-green-100 text-green-700 rounded hover:bg-green-200"
      >
        ▶️ Resume
      </button>

      <button 
        @click="powerDialer.skipLead()" 
        :disabled="powerDialer.isDialing"
        class="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
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
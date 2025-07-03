import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { globalStore } from './global'
import { createToast } from '@/utils'

export const powerDialerStore = defineStore('power-dialer', () => {
  const { makeCall } = globalStore()
  
  const isActive = ref(false)
  const currentLeadIndex = ref(0)
  const leads = ref([])
  const pauseBetweenCalls = ref(60) // seconds
  const isDialing = ref(false)
  const isPaused = ref(false)
  const isManualPause = ref(false)
  const pauseCountdown = ref(0)
  const pauseTimer = ref(null)
  
  const currentLead = computed(() => 
    leads.value[currentLeadIndex.value] || null
  )
  
  const remainingLeads = computed(() => 
    leads.value.slice(currentLeadIndex.value + 1)
  )
  
  const completedLeads = computed(() => 
    leads.value.slice(0, currentLeadIndex.value)
  )

  const progressPercentage = computed(() => {
    if (!leads.value.length) return 0
    
    // If there's a current lead, include it in progress (matches display text)
    // If no current lead, we've completed everything (100%)
    const currentProgress = currentLead.value 
      ? completedLeads.value.length + 1 
      : leads.value.length
      
    return (currentProgress / leads.value.length) * 100
  })

  const canPause = computed(() => 
    isActive.value && !isDialing.value
  )

  const canResume = computed(() => 
    isActive.value && (isPaused.value || isManualPause.value)
  )

  function startSession(leadsList) {
    // Process leads to ensure we have phone numbers
    leads.value = leadsList.map(lead => ({
      ...lead,
      primary_phone: lead.mobile_no || lead.phone
    })).filter(lead => lead.primary_phone)
    
    currentLeadIndex.value = 0
    isActive.value = true
    
    callNext()
  }

  async function callNext() {
    if (isManualPause.value) {
      return // Don't proceed if manually paused
    }

    if (currentLeadIndex.value >= leads.value.length) {
      endSession()
      return
    }

    const lead = currentLead.value
    if (lead?.primary_phone) {
      try {
        isDialing.value = true
        // Use existing makeCall function - it handles all Twilio integration
        await Promise.resolve(makeCall(lead.primary_phone))
      } catch (error) {
        // Handle call initiation error
        console.error('Power Dialer call error:', error)
        isDialing.value = false
        isManualPause.value = true
        isPaused.value = false
        pauseCountdown.value = 0

        createToast({
          title: 'Call Error',
          text: error?.message || 'Failed to initiate call',
          icon: 'x',
          iconClasses: 'text-ink-red-4',
        })
        // Do not proceed automatically; user can skip or resume
        return
      }
    } else {
      // Skip lead without phone number
      nextLead()
    }
  }

  function onCallEnded() {
    isDialing.value = false
    
    // Check if this was the last lead before starting pause countdown
    if (currentLeadIndex.value >= leads.value.length - 1) {
      // This was the last lead, end the session
      endSession()
      return
    }
    
    // Start pause countdown if configured
    if (pauseBetweenCalls.value > 0 && !isManualPause.value) {
      startPauseCountdown()
    } else {
      nextLead()
    }
  }

  function startPauseCountdown(startValue = pauseBetweenCalls.value) {
    isPaused.value = true
    pauseCountdown.value = startValue

    // clear any existing timer first
    if (pauseTimer.value) {
      clearInterval(pauseTimer.value)
    }

    pauseTimer.value = setInterval(() => {
      pauseCountdown.value--

      if (pauseCountdown.value <= 0) {
        clearInterval(pauseTimer.value)
        pauseTimer.value = null
        isPaused.value = false

        if (!isManualPause.value) {
          nextLead()
        }
      }
    }, 1000)
  }

  function pauseSession() {
    if (!canPause.value) return

    isManualPause.value = true

    // If we're in auto-pause countdown, stop it but keep remaining time
    if (pauseTimer.value) {
      clearInterval(pauseTimer.value)
      pauseTimer.value = null
    }

    // Keep the remaining pauseCountdown value as-is so we can resume later
    // If pauseCountdown is zero (pause before countdown started), set to default
    if (pauseCountdown.value <= 0) {
      pauseCountdown.value = pauseBetweenCalls.value
    }

    isPaused.value = false
  }

  function resumeSession() {
    if (!canResume.value) return

    isManualPause.value = false

    // If we have remaining countdown time, resume it; otherwise start full countdown
    if (pauseCountdown.value > 0) {
      startPauseCountdown(pauseCountdown.value)
    } else if (!isPaused.value) {
      // No existing countdown, probably paused before countdown began
      startPauseCountdown()
    }
  }

  function nextLead() {
    currentLeadIndex.value++
    if (currentLeadIndex.value >= leads.value.length) {
      endSession()
    } else {
      callNext()
    }
  }

  function skipLead() {
    if (pauseTimer.value) {
      clearInterval(pauseTimer.value)
      pauseTimer.value = null
    }
    // Clear any pause states
    isPaused.value = false
    isManualPause.value = false
    pauseCountdown.value = 0
    nextLead()
  }

  function endSession() {
    // Clean up timers
    if (pauseTimer.value) {
      clearInterval(pauseTimer.value)
      pauseTimer.value = null
    }
    
    // Reset state
    isActive.value = false
    isDialing.value = false
    isPaused.value = false
    isManualPause.value = false
    pauseCountdown.value = 0
    leads.value = []
    currentLeadIndex.value = 0
  }

  return {
    isActive,
    leads,
    currentLead,
    remainingLeads,
    completedLeads,
    progressPercentage,
    pauseCountdown,
    isDialing,
    isPaused,
    isManualPause,
    canPause,
    canResume,
    pauseBetweenCalls,
    startSession,
    onCallEnded,
    pauseSession,
    resumeSession,
    nextLead,
    skipLead,
    endSession
  }
}) 
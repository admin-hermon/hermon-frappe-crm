import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useFeatureFlagsStore = defineStore('crm-feature-flags', () => {
  const featureFlags = ref({
    leadEditingEnabled: false,
  })

  return {
    featureFlags,
  }
})

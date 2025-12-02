<template>
  <div class="flex h-full flex-col gap-8 p-8">
    <h2 class="flex gap-2 text-xl font-semibold leading-none h-5 text-ink-gray-9">
      {{ __('Calling and SMS Settings') }}
      <Badge v-if="isDirty" :label="__('Not Saved')" variant="subtle" theme="orange" />
    </h2>

    <div v-if="isContentReady" class="flex-1 flex flex-col gap-8 overflow-y-auto">
      <div v-if="hasAvailableNumbers" class="w-1/2 flex flex-col gap-4">
        <FormControl type="select" v-model="selectedNumber" :label="__('Preferred Calling and SMS Number')"
          :options="availableNumbersOptions"
          :description="__('Select your preferred number from the pool of available Twilio numbers')" />
        <div class="flex items-start gap-2">
          <FormControl type="checkbox" v-model="overrideGeoRouting" :label="__('Override geo-based routing')"
            class="mt-1" />
          <Tooltip
            :text="__('When enabled, your preferred number will always be used, regardless of the destination number location. Geo-based routing will be skipped.')"
            class="ml-1">
            <Icon name="info" class="h-4 w-4 text-ink-gray-5" />
          </Tooltip>
        </div>
      </div>
      <div v-else class="w-1/2 rounded border border-outline-gray-2 bg-surface-gray p-4">
        <p class="text-sm text-ink-gray-6">
          {{ __('No Twilio numbers are available. Please configure at least one enabled Twilio number to use calling and SMS features.') }}
        </p>
      </div>
    </div>

    <div v-else class="flex flex-1 items-center justify-center">
      <Spinner class="size-8" />
    </div>

    <div class="flex justify-end gap-2">
      <Button :loading="isSaving" :label="__('Save')" variant="solid" :disabled="!canSave" @click="savePreferences" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import Icon from '@/components/Icon.vue'
import { createListResource, createDocumentResource, FormControl, Spinner, Button, Tooltip, Badge, call } from 'frappe-ui'
import { createToast } from '@/utils'
import { sessionStore } from '@/stores/session'

// Form state - separate from model
const selectedNumber = ref('')
const overrideGeoRouting = ref(false)
const isNewDocument = ref(false)

const availableNumbers = createListResource({
  doctype: 'CRM Twilio Number',
  filters: { enabled: 1 },
  fields: ['phone_number', 'geographic_description', 'country_code'],
  orderBy: 'phone_number',
  pageLength: 1000,
  auto: true,
  transform(data) {
    if (!data || !Array.isArray(data)) {
      return []
    }
    return data.map(num => ({
      label: `${num.phone_number} (${num.geographic_description || num.country_code})`,
      value: num.phone_number
    }))
  }
})

const availableNumbersOptions = computed(() => {
  return availableNumbers.data || []
})

const hasAvailableNumbers = computed(() => {
  return availableNumbersOptions.value.length > 0
})

const { user } = sessionStore()

const telephonyAgent = createDocumentResource({
  doctype: 'CRM Telephony Agent',
  name: user,
  fields: ['twilio_number', 'override_geo_routing', 'user', 'twilio', 'default_medium', 'call_receiving_device'],
  auto: true,
  onSuccess: () => {
    syncFormValuesFromDoc()
  },
  onError: (err) => {
    // Check if document doesn't exist (404 error)
    if (err?.httpStatus === 404 || err?.exc_type === 'DoesNotExistError') {
      isNewDocument.value = true
    }
  }
})

function syncFormValuesFromDoc() {
  const doc = telephonyAgent?.doc
  if (doc) {
    isNewDocument.value = false
    selectedNumber.value = doc.twilio_number || ''
    overrideGeoRouting.value = doc.override_geo_routing || false
  }
}

// Watch for document changes to sync form values
// This watcher will trigger both on telephonyAgent.doc changes and immediately on component mount (due to { immediate: true }).
// The initial run upon mount ensures the form is synced with document values when the component loads.
watch(
  () => telephonyAgent?.doc,
  () => {
    syncFormValuesFromDoc()
  },
  { immediate: true }
)

const isContentReady = computed(() => {
  const numbersLoading = availableNumbers.loading
  const agentLoading = telephonyAgent?.get?.loading || false
  return !numbersLoading && !agentLoading
})

const isDirty = computed(() => {
  // If document doesn't exist (new document), consider it dirty if user has selected a number
  if (isNewDocument.value) {
    return !!selectedNumber.value
  }

  // If document hasn't loaded yet, not dirty
  if (!telephonyAgent?.doc) {
    return false
  }

  // Compare with original values
  const originalNumber = telephonyAgent.doc.twilio_number || ''
  const originalOverride = telephonyAgent.doc.override_geo_routing || false

  return selectedNumber.value !== originalNumber || overrideGeoRouting.value !== originalOverride
})

const isSaving = ref(false)

const canSave = computed(() => {
  if (!isDirty.value) return false
  if (!selectedNumber.value) return false
  return true
})

function showSuccessToast() {
  createToast({
    title: __('Success'),
    text: __('Calling and sms preferences saved successfully'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}

function showErrorToast(err) {
  const errorMessage = err?.error?.messages?.[0] || err?.messages?.[0] || err?.error?.message || err?.message || __('Failed to save calling and sms preferences')
  createToast({
    title: __('Error'),
    text: errorMessage,
    icon: 'x',
    iconClasses: 'text-ink-red-4',
  })
}

async function createTelephonyAgent() {
  const doc = await call('frappe.client.insert', {
    doc: {
      doctype: 'CRM Telephony Agent',
      user: user,
      twilio: 1,
      default_medium: 'Twilio',
      call_receiving_device: 'Computer',
      twilio_number: selectedNumber.value,
      override_geo_routing: overrideGeoRouting.value
    }
  })

  if (!doc.name) {
    throw new Error(__('Failed to create telephony agent'))
  }

  isNewDocument.value = false
  await telephonyAgent.reload()
  showSuccessToast()
}

async function updateTelephonyAgent() {
  await telephonyAgent.setValue.submit({
    twilio_number: selectedNumber.value,
    override_geo_routing: overrideGeoRouting.value
  })

  showSuccessToast()
}

async function savePreferences() {
  if (!selectedNumber.value) {
    showErrorToast({ message: __('Please select a preferred calling and SMS number before saving.') })
    return
  }

  isSaving.value = true

  try {
    if (isNewDocument.value) {
      await createTelephonyAgent()
    } else {
      await updateTelephonyAgent()
    }
  } catch (err) {
    showErrorToast(err)
  } finally {
    isSaving.value = false
  }
}
</script>
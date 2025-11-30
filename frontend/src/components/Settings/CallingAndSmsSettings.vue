<template>
  <div class="flex h-full flex-col gap-8 p-8">
    <h2 class="flex gap-2 text-xl font-semibold leading-none h-5 text-ink-gray-9">
      {{ __('Calling and SMS Settings') }}
      <Badge v-if="telephonyAgent.isDirty" :label="__('Not Saved')" variant="subtle" theme="orange" />
    </h2>

    <div v-if="telephonyAgent.doc && !telephonyAgent.get.loading && !availableNumbers.loading"
      class="flex-1 flex flex-col gap-8 overflow-y-auto">
      <FormControl type="select" v-model="telephonyAgent.doc.twilio_number" :label="__('Preferred Calling and SMS Number')"
        :options="availableNumbers"
        :description="__('Select your preferred number from the pool of available Twilio numbers')" class="w-1/2" />

      <div class="flex items-start gap-2">
        <FormControl type="checkbox" v-model="telephonyAgent.doc.override_geo_routing"
          :label="__('Override geo-based routing')" class="mt-1" />
        <Tooltip
          :text="__('When enabled, your preferred number will always be used, regardless of the destination number location. Geo-based routing will be skipped.')"
          class="ml-1">
          <Icon name="info" class="h-4 w-4 text-ink-gray-5" />
        </Tooltip>
      </div>
    </div>

    <div v-else class="flex flex-1 items-center justify-center">
      <Spinner class="size-8" />
    </div>

    <div class="flex justify-between gap-2">
      <div>
        <ErrorMessage class="mt-2" :message="telephonyAgent.save.error" />
      </div>
      <Button :loading="telephonyAgent.save.loading" :label="__('Save')" variant="solid"
        :disabled="!telephonyAgent.isDirty" @click="savePreferences" />
    </div>
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { createResource, createDocumentResource, call, FormControl, Spinner, Button, ErrorMessage, Tooltip, Badge } from 'frappe-ui'
import { createToast } from '@/utils'

const availableNumbers = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'CRM Twilio Number',
    filters: { enabled: 1 },
    fields: ['phone_number', 'geographic_description', 'country_code'],
    order_by: 'phone_number'
  },
  auto: true,
  transform(data) {
    return [
      { label: __('None'), value: '' },
      ...((data || []).map(num => ({
        label: `${num.phone_number} (${num.geographic_description || num.country_code})`,
        value: num.phone_number
      })))
    ]
  }
})

// Shared toast handlers to avoid duplication
const showSuccessToast = () => {
  createToast({
    title: __('Success'),
    text: __('Calling and sms preferences saved successfully'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}

const showErrorToast = (err) => {
  createToast({
    title: __('Error'),
    text: err.message || err.messages?.[0] || __('Failed to save calling and sms preferences'),
    icon: 'x',
    iconClasses: 'text-ink-red-4',
  })
}

const telephonyAgent = createDocumentResource({
  doctype: 'CRM Telephony Agent',
  name: frappe.session.user,
  fields: ['twilio_number', 'override_geo_routing'],
  auto: true,
  onError: (err) => {
    // Document doesn't exist yet - initialize with default values
    if (!telephonyAgent.doc) {
      telephonyAgent.setDoc({
        user: frappe.session.user,
        twilio: 1,
        default_medium: 'Twilio',
        call_receiving_device: 'Computer',
        twilio_number: '',
        override_geo_routing: false
      })
    }
  },
  setValue: {
    onSuccess: showSuccessToast,
    onError: showErrorToast,
  },
})

async function savePreferences() {
  // If document doesn't exist, create it first
  if (!telephonyAgent.doc?.name) {
    try {
      await call('frappe.client.insert', {
        doc: {
          doctype: 'CRM Telephony Agent',
          user: frappe.session.user,
          twilio: 1,
          default_medium: 'Twilio',
          call_receiving_device: 'Computer',
          twilio_number: telephonyAgent.doc?.twilio_number || '',
          override_geo_routing: telephonyAgent.doc?.override_geo_routing || false
        }
      })
      // Reload to get the newly created document
      await telephonyAgent.reload()

      showSuccessToast()
      return
    } catch (err) {
      showErrorToast(err)
      return
    }
  }

  // Document exists - use save method (simpler than setValue, saves entire doc)
  await telephonyAgent.save.submit()
}
</script>

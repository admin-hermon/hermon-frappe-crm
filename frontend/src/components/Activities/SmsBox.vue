<template>
  <div
    v-if="smsBox.show"
    class="p-4 border-t border-gray-300 bg-gray-50 dark:border-gray-700 dark:bg-gray-900"
  >
    <div class="flex flex-col">
      <textarea
        v-model="newMessage"
        placeholder="Type your message here..."
        :disabled="sendSms.loading"
        ref="smsTextarea"
        class="w-full min-h-[80px] p-2 bg-white border border-gray-300 rounded resize-y dark:bg-gray-800 dark:border-gray-600 dark:text-white"
      ></textarea>
      <div v-if="sendError" class="p-2 text-sm text-red-600 bg-red-50 rounded-md">
        {{ sendError }}
      </div>
      <div class="flex items-center justify-between mt-2">
        <Button @click="sendMessage" :disabled="!newMessage || sendSms.loading">
          {{ sendSms.loading ? 'Sending...' : 'Send' }}
        </Button>
        <Button variant="ghost" @click="smsBox.show = false">
          {{ __('Cancel') }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { Button } from 'frappe-ui';
import { createResource } from 'frappe-ui';

const props = defineProps({
  doc: {
    type: Object,
    required: true,
  },
  smsBox: {
    type: Object,
    required: true,
  }
});

const emit = defineEmits(['reload']);

const newMessage = ref('');
const smsTextarea = ref(null);
const sendError = ref('');

const sendSms = createResource({
  url: 'crm.integrations.twilio.api.send_sms',
  makeAPICall: false,
});

watch(() => props.smsBox.show, (newValue) => {
  if (newValue) {
    sendError.value = '';
    nextTick(() => {
      smsTextarea.value?.focus();
    });
  }
});

watch(newMessage, () => {
	if (sendError.value) {
		sendError.value = '';
	}
});

function sendMessage() {
  if (!newMessage.value.trim()) return;
  sendError.value = '';

  sendSms.submit({
    lead_identifier: props.doc.name,
    message: newMessage.value,
  }).then(() => {
    newMessage.value = '';
    props.smsBox.show = false;
    emit('reload');
  }).catch((err) => {
    sendError.value = err.messages?.[0] || 'An unknown error occurred while sending the SMS.';
  });
}
</script> 
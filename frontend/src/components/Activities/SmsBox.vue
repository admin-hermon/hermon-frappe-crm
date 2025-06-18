<template>
  <div v-if="smsBox.show" class="sms-composer-box">
    <div class="sms-composer">
      <textarea
        v-model="newMessage"
        placeholder="Type your message here..."
        :disabled="sendSms.loading"
        ref="smsTextarea"
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

<style scoped>
.sms-composer-box {
  padding: 1rem;
  border-top: 1px solid #d1d8dd;
  background: #f9fafb;
}
.sms-composer {
  display: flex;
  flex-direction: column;
}
.sms-composer textarea {
  width: 100%;
  border-radius: 4px;
  border: 1px solid #d1d8dd;
  padding: 0.5rem;
  resize: vertical;
  min-height: 80px;
}
</style> 
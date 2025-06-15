<template>
	<div class="sms-area">
		<div class="sms-history-container">
			<div v-if="loading" class="loading-state">Loading messages...</div>
			<div v-else-if="error" class="error-state">{{ error }}</div>
			<div class="sms-history" v-else-if="history.length">
				<div 
					v-for="msg in history" 
					:key="msg.name" 
					class="sms-message"
					:class="['direction-' + msg.direction.toLowerCase()]"
				>
					<div class="message-bubble">
						<p class="message-content">{{ msg.message }}</p>
						<span class="message-timestamp">{{ formatDate(msg.creation) }}</span>
					</div>
				</div>
			</div>
			<div v-else class="empty-state">
				<div class="flex flex-col items-center justify-center h-full">
					<Icon name="message-off" class="w-10 h-10 text-gray-400" />
					<p class="mt-2 text-gray-500">No SMS messages yet.</p>
					<p class="mt-1 text-sm text-gray-400">Sent and received SMS messages will appear here.</p>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { formatDate } from '@/utils'

const props = defineProps({
	history: {
		type: Array,
		required: true,
	},
	loading: {
		type: Boolean,
		default: false,
	},
	error: {
		type: [String, Object],
		default: null,
	}
});
</script>

<style scoped>
.sms-area {
	display: flex;
	flex-direction: column;
	height: 100%;
}

.sms-history-container {
	flex-grow: 1;
	overflow-y: auto;
	padding: 1rem;
	display: flex;
	flex-direction: column;
}

.sms-history {
	display: flex;
	flex-direction: column-reverse; /* Show latest messages at the bottom */
	flex-grow: 1;
}

.loading-state, .error-state, .empty-state {
	text-align: center;
	padding: 2rem;
	color: #8d99a6;
	margin: auto;
}

.error-state {
	color: #ff5858;
}

.sms-message {
	display: flex;
	margin-bottom: 0.5rem;
	max-width: 100%;
}

.message-bubble {
	max-width: 70%;
	padding: 0.5rem 0.75rem;
	border-radius: 15px;
	position: relative;
	word-wrap: break-word;
}

.message-content {
	margin: 0;
	white-space: pre-wrap;
}

.message-timestamp {
	font-size: 0.7rem;
	color: #6c757d;
	display: block;
	margin-top: 0.25rem;
}

/* Outgoing messages */
.direction-outgoing {
	justify-content: flex-end;
	align-self: flex-end;
}
.direction-outgoing .message-bubble {
	background-color: #dcf8c6;
	border-bottom-right-radius: 3px;
}
.direction-outgoing .message-timestamp {
	text-align: right;
}

/* Incoming messages */
.direction-incoming {
	justify-content: flex-start;
	align-self: flex-start;
}
.direction-incoming .message-bubble {
	background-color: #f1f0f0;
	border-bottom-left-radius: 3px;
}
</style>
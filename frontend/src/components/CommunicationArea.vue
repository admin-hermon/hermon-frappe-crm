<template>
  <div class="flex justify-between gap-3 border-t px-4 py-2.5 sm:px-10">
    <div class="flex gap-1.5">
      <Button
        ref="sendEmailRef"
        variant="ghost"
        :class="[
          showEmailBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
        ]"
        :label="__('Reply')"
        @click="toggleEmailBox()"
      >
        <template #prefix>
          <Email2Icon class="h-4" />
        </template>
      </Button>
      <Button
        variant="ghost"
        :label="__('Comment')"
        :class="[
          showCommentBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
        ]"
        @click="toggleCommentBox()"
      >
        <template #prefix>
          <CommentIcon class="h-4" />
        </template>
      </Button>
    </div>
  </div>
  <div
    v-show="showEmailBox"
    @keydown.ctrl.enter.capture.stop="submitEmail"
    @keydown.meta.enter.capture.stop="submitEmail"
  >
    <EmailEditor
      ref="newEmailEditor"
      v-model:content="newEmail"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitEmail,
        disabled: emailEmpty,
      }"
      :discardButtonProps="{
        onClick: () => {
          showEmailBox = false
          newEmailEditor.subject = subject
          newEmailEditor.toEmails = doc.data.email ? [doc.data.email] : []
          newEmailEditor.ccEmails = []
          newEmailEditor.bccEmails = []
          newEmailEditor.cc = false
          newEmailEditor.bcc = false
          newEmail = ''
        },
      }"
      :editable="showEmailBox"
      v-model="doc.data"
      v-model:attachments="attachments"
      :doctype="doctype"
      :subject="subject"
      :placeholder="
        __('Hi John, \n\nCan you please provide more details on this...')
      "
    />
  </div>
  <div v-show="showCommentBox">
    <CommentBox
      ref="newCommentEditor"
      v-model:content="newComment"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitComment,
        disabled: commentEmpty,
      }"
      :discardButtonProps="{
        onClick: () => {
          showCommentBox = false
          newComment = ''
        },
      }"
      :editable="showCommentBox"
      v-model="doc.data"
      v-model:attachments="attachments"
      :doctype="doctype"
      :placeholder="__('@John, can you please check this?')"
    />
  </div>
</template>

<script setup>
import EmailEditor from '@/components/EmailEditor.vue'
import CommentBox from '@/components/CommentBox.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import { capture } from '@/telemetry'
import { usersStore } from '@/stores/users'
import { useStorage } from '@vueuse/core'
import { call, createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, watch, computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
})

const doc = defineModel()
const reload = defineModel('reload')

const emit = defineEmits(['scroll'])

const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const showEmailBox = ref(false)
const showCommentBox = ref(false)
const newEmail = useStorage('emailBoxContent', '')
const newComment = useStorage('commentBoxContent', '')
const newEmailEditor = ref(null)
const newCommentEditor = ref(null)
const sendEmailRef = ref(null)
const attachments = ref([])

const subject = computed(() => {
  let prefix = ''
  if (doc.value.data?.lead_name) {
    prefix = doc.value.data.lead_name
  } else if (doc.value.data?.organization) {
    prefix = doc.value.data.organization
  }
  return `${prefix} (#${doc.value.data.name})`
})

const signature = createResource({
  url: 'crm.api.get_user_signature',
  cache: 'user-email-signature',
  auto: true,
})

function setSignature(editor) {
  if (!signature.data) return
  let emailContent = editor.getHTML()
  emailContent = emailContent.startsWith('<p></p>')
    ? emailContent.slice(7)
    : emailContent
  // Signature data is set first, most likely to handle replies (setContent overrides the content entirely)
  editor.commands.setContent(parseSignature(signature.data))
  // Previous email content is inserted after the signature
  // setContent + insertContent ensures idempotency
  editor.commands.insertContent(emailContent)
  editor.commands.focus('start')
}

/**
 * Parses the signature data and returns either the original html based signature or a JSON representation of the signature
 * 
 * If the signature contains images, it will return a JSON representation of the signature.
 * 
 * We cannot mix HTML and JSON conteint in the payload pushed to setContent or insertContent - we need to return one or the other.
 * 
 * @param signatureData - The signature data to parse
 * @returns The parsed signature data
 */
function parseSignature(signatureData) {
  // Check if signature contains images
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = signatureData
  const images = tempDiv.querySelectorAll('img')
  const containsImages = images.length > 0

  // Original text logic, returns html based signature
  if (!containsImages) {
    return createTextSignature(signatureData)
  }

  // Signature contains images, return the a JSON representation of the signature as the HTML based payload has issues with images
  return createImageBasedSignature(images[0])
}

// Original text logic, previously implemented in setSignature
function createTextSignature(signatureData) {
  signatureData = signatureData.replace(/\n/g, '<br>')
  return signatureData
}

/**
 * TipTap's handling of <img> tags in HTML signatures is unreliable.
 * To ensure signatures with images are supported, we convert the signature
 * content into a JSON format representing structured TipTap nodes,
 * supporting a single image as a proper node. This provides stability for
 * emails with image signatures in the editor.
 *
 * 
 * The caveat of this is that if the signature contains multiple images, or other text,
 * it will only render the first image.
 */

function createImageBasedSignature(imageElementObject) {
  const imageUrl = imageElementObject.src
  const imageAlt = imageElementObject.alt || ''

  return [
    {
      type: 'paragraph',
      content: [
        {
          type: 'hardBreak'
        }
      ]
    },
    {
      type: 'paragraph',
      content: [
        {
          type: 'image',
          attrs: {
            src: imageUrl,
            alt: imageAlt,
            title: imageAlt
          }
        }
      ]
    }
  ]
}

watch(
  () => showEmailBox.value,
  (value) => {
    if (value) {
      let editor = newEmailEditor.value.editor
      editor.commands.focus()
      setSignature(editor)
    }
  },
)

watch(
  () => showCommentBox.value,
  (value) => {
    if (value) {
      newCommentEditor.value.editor.commands.focus()
    }
  },
)

const commentEmpty = computed(() => {
  return !newComment.value || newComment.value === '<p></p>'
})

const emailEmpty = computed(() => {
  return (
    !newEmail.value ||
    newEmail.value === '<p></p>' ||
    !newEmailEditor.value?.toEmails?.length
  )
})

async function sendMail() {
  let recipients = newEmailEditor.value.toEmails
  let subject = newEmailEditor.value.subject
  let cc = newEmailEditor.value.ccEmails || []
  let bcc = newEmailEditor.value.bccEmails || []

  if (attachments.value.length) {
    capture('email_attachments_added')
  }
  await call('frappe.core.doctype.communication.email.make', {
    recipients: recipients.join(', '),
    attachments: attachments.value.map((x) => x.name),
    cc: cc.join(', '),
    bcc: bcc.join(', '),
    subject: subject,
    content: newEmail.value,
    doctype: props.doctype,
    name: doc.value.data.name,
    send_email: 1,
    sender: getUser().email,
    sender_full_name: getUser()?.full_name || undefined,
  })
}

async function sendComment() {
  let comment = await call('frappe.desk.form.utils.add_comment', {
    reference_doctype: props.doctype,
    reference_name: doc.value.data.name,
    content: newComment.value,
    comment_email: getUser().email,
    comment_by: getUser()?.full_name || undefined,
  })
  if (comment && attachments.value.length) {
    capture('comment_attachments_added')
    await call('crm.api.comment.add_attachments', {
      name: comment.name,
      attachments: attachments.value.map((x) => x.name),
    })
  }
}

async function submitEmail() {
  if (emailEmpty.value) return
  showEmailBox.value = false
  await sendMail()
  newEmail.value = ''
  reload.value = true
  emit('scroll')
  capture('email_sent', { doctype: props.doctype })
  updateOnboardingStep('send_first_email')
}

async function submitComment() {
  if (commentEmpty.value) return
  showCommentBox.value = false
  await sendComment()
  newComment.value = ''
  reload.value = true
  emit('scroll')
  capture('comment_sent', { doctype: props.doctype })
  updateOnboardingStep('add_first_comment')
}

function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false
  }
  showEmailBox.value = !showEmailBox.value
}

function toggleCommentBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false
  }
  showCommentBox.value = !showCommentBox.value
}

defineExpose({
  show: showEmailBox,
  showComment: showCommentBox,
  editor: newEmailEditor,
})
</script>

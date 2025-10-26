<template>
  <Layout v-if="session().isLoggedIn">
    <!-- :key="$route.path" is used to force a reload of the page when the route changes -->
    <router-view :key="$route.path" /> 
  </Layout>
  <Dialogs />
  <Toasts />
  <PowerDialerUI />
</template>

<script setup>
import { Dialogs } from '@/utils/dialogs'
import { sessionStore as session } from '@/stores/session'
import { setTheme } from '@/stores/theme'
import { Toasts, setConfig } from 'frappe-ui'
import { computed, defineAsyncComponent, onMounted } from 'vue'
import PowerDialerUI from '@/components/PowerDialer/PowerDialerUI.vue'

const MobileLayout = defineAsyncComponent(
  () => import('./components/Layouts/MobileLayout.vue'),
)
const DesktopLayout = defineAsyncComponent(
  () => import('./components/Layouts/DesktopLayout.vue'),
)
const Layout = computed(() => {
  if (window.innerWidth < 640) {
    return MobileLayout
  } else {
    return DesktopLayout
  }
})

onMounted(() => setTheme())

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
</script>

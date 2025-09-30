<template>
  <div class="attachments view">
    <div class="attachments-list-container">
      <AttachmentsList show-authors />
    </div>
  </div>
</template>

<script>
import AttachmentsApi from '@/mixins/api/Attachments.vue'
import AttachmentsList from '@/views/attachments/AttachmentsList.vue'

export default {
  mixins: [AttachmentsApi],
  components: {
    AttachmentsList,
  },
}
</script>

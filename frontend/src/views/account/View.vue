<template>
  <Loader v-if="loading" />
  <div class="error" v-else-if="!account">
    <h2>Account not found</h2>
  </div>
  <div class="account view" v-else>
    <div class="header">
      <div class="title">
        <div class="banner">
          <a :href="account.header_url" target="_blank" rel="noopener" v-if="account.header_url">
            <img :src="account.header_path"
                 :alt="`Banner of ${account.display_name}`"
                 ref="banner"
                 @error="$refs.banner.src = account.header_url" />
          </a>
        </div>
        <div class="avatar">
          <a href="#" @click.prevent="showProfilePicModal = true">
            <img :src="account.avatar_path"
                 :alt="`Avatar of ${account.display_name}`"
                 ref="avatar"
                 @error="$refs.avatar.src = account.avatar_url" />
          </a>
        </div>
        <div class="details">
          <h2>{{ account.display_name }}</h2>
          <p class="fqn">
            <a :href="account.url" target="_blank" rel="noopener">
              {{ account.fqn }}
            </a>
          </p>
        </div>
      </div>

      <div class="note" v-if="account.profile_note">
        <p v-html="account.profile_note"></p>
      </div>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: view === 'posts' }" @click="view = 'posts'">
        <i class="fas fa-file-text" aria-hidden="true" /> Posts
      </button>
      <button class="tab" :class="{ active: view === 'attachments' }" @click="view = 'attachments'">
        <i class="fas fa-paperclip" aria-hidden="true" /> Attachments
      </button>
    </div>

    <PostsList :filter="{ account: account.fqn }" v-if="view === 'posts'" />
    <AttachmentsList :filter="{ account: account.fqn, excludeReplies: true }" v-else-if="view === 'attachments'" />
  </div>

  <Modal :show="showProfilePicModal"
         title="Profile picture"
         @close="showProfilePicModal = false">
    <div class="avatar-container">
      <img :src="account.avatar_path"
           :alt="`Avatar of ${account.display_name}`"
           ref="avatarModal"
           @error="$refs.avatarModal.src = account.avatar_url" />
    </div>
  </Modal>
</template>

<script>
import AccountsApi from '@/mixins/api/Accounts.vue'
import AttachmentsList from '@/views/attachments/AttachmentsList.vue'
import Loader from '@/elements/Loader.vue'
import Modal from '@/elements/Modal.vue'
import PostsList from '@/views/posts/PostsList.vue'
import PostsApi from '@/mixins/api/Posts.vue'

export default {
  mixins: [AccountsApi, PostsApi],
  components: {
    AttachmentsList,
    Loader,
    Modal,
    PostsList,
  },

  data() {
    return {
      account: null,
      showProfilePicModal: false,
      loading: true,
      view: null,
    }
  },

  methods: {
    async refresh() {
      this.account = await this.getAccount(this.$route.params.fqn)
    },
  },

  watch: {
    view(newView) {
      this.$router.replace({
        query: {
          ...this.$route.query,
          view: newView
        }
      })
    },
  },

  async mounted() {
    this.view = this.$route.query.view || 'posts'
    try {
      await this.refresh()
    } finally {
      this.loading = false
    }
  },
}
</script>

<style scoped lang="scss">
$banner-height: 200px;

.account.view {
  max-width: 800px;
  display: flex;
  flex-direction: column;
  margin: 0 auto;
  padding: 1em;
  position: relative;

  .header {
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-bottom: 1em;

    .title {
      display: flex;
      align-items: center;
      gap: 1.25em;
      margin-top: calc($banner-height / 2);
    }

    .banner {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: $banner-height;
      overflow: hidden;
      z-index: -1;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transform: scale(1.0);
      }
    }

    h2 {
      text-align: center;
      margin-bottom: 0.25em;
    }

    .avatar {
      width: 150px;
      height: 150px;
      border-radius: 50%;
      overflow: hidden;
      margin-bottom: 0.5em;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .details {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      margin-top: 75px;

      .fqn {
        margin: 0;
        font-size: 1em;
        font-weight: 200;
        color: var(--color-text-secondary);
        word-break: break-all;
      }
    }

    .note {
      margin-top: 0.5em;
      font-size: 0.9em;

      p {
        margin: 0;
      }
    }
  }
}
</style>

<style>
.avatar-container {
  background: black;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1em;
}

.avatar-container img {
    max-width: 100%;
    max-height: 80vh;
    object-fit: contain;
}
</style>

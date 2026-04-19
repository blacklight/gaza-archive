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
          <h2>
            {{ account.display_name }}
            <SuspensionIcon :state="account.state" />
          </h2>
          <p class="fqn">
            <a :href="account.url" target="_blank" rel="noopener">
              {{ account.fqn }}
            </a>
          </p>
          <button class="suspensions-button" @click="openSuspensionsModal">
            <i class="fas fa-exclamation-circle" aria-hidden="true"></i>
            See Suspensions
          </button>
        </div>
      </div>

      <div class="note" v-if="account.profile_note">
        <p v-html="account.profile_note"></p>
      </div>
    </div>

    <p class="fundraiser-campaign" v-if="account.campaign_url">
      <RouterLink :to="'/campaigns/accounts/' + account.fqn">
        <i class="fas fa-hand-holding-usd" aria-hidden="true"></i>
        View Fundraising Campaign
      </RouterLink>
    </p>

    <div class="profile-fields" v-if="profileFields?.length">
      <div class="field" v-for="field in profileFields" :key="field.key">
        <span class="field-key">{{ field.key }}</span>
        <span class="field-value" v-html="field.value"></span>
      </div>
    </div>

    <div class="tabs" v-if="!hideAllUserContent">
      <button class="tab" :class="{ active: view === 'posts' }" @click="view = 'posts'">
        <i class="fas fa-file-text" aria-hidden="true" /> Posts
      </button>
      <button class="tab" :class="{ active: view === 'attachments' }" @click="view = 'attachments'">
        <i class="fas fa-paperclip" aria-hidden="true" /> Attachments
      </button>
    </div>

    <PostsList :filter="{ account: account.fqn }" v-if="!hideAllUserContent && view === 'posts'" />
    <AttachmentsList :filter="{ account: account.fqn, excludeReplies: true }" v-else-if="!hideAllUserContent && view === 'attachments'" />
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

  <Modal :show="showSuspensionsModal"
         title="Account Suspension Status"
         @close="showSuspensionsModal = false">
    <div class="suspensions-container">
      <div v-if="suspensionsLoading" class="loading-message">
        <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
        Loading suspension information...
      </div>
      <div v-else-if="!suspensions.length" class="no-suspensions">
        No suspension information available.
      </div>
      <div v-else class="suspensions-list">
        <div class="suspension-item"
             v-for="suspension in suspensions"
             :key="suspension.server_url">
          <div class="suspension-header">
            <div class="server-info">
              <span class="suspension-state" :class="`state-${suspension.state.toLowerCase()}`">
                <i :class="getStateIcon(suspension.state)" aria-hidden="true"></i>
                {{ suspension.state }}
              </span>
              <span class="server-name">
                <strong>{{ suspension.server_url.replace('https://', '') }}</strong>
              </span>
            </div>
            <div class="suspension-date">
              Last checked: {{ formatDate(suspension.updated_at) }}
            </div>
          </div>
        </div>
      </div>
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
import SuspensionIcon from '@/components/SuspensionIcon.vue'

export default {
  mixins: [AccountsApi, PostsApi],
  components: {
    AttachmentsList,
    Loader,
    Modal,
    PostsList,
    SuspensionIcon,
  },

  data() {
    return {
      account: null,
      showProfilePicModal: false,
      showSuspensionsModal: false,
      suspensions: [],
      suspensionsLoading: false,
      loading: true,
      view: null,
    }
  },

  computed: {
    hideAllUserContent() {
      return this.$root.config.hide_all_user_content
    },

    profileFields() {
      return Object.entries(this.account?.profile_fields || {})?.map(
        ([key, value]) => {
          if (value?.match(/^https?:\/\/\S+$/)) {
            value = `<a href="${value}" target="_blank" rel="noopener">${value}</a>`
          }

          return { key, value }
        }
      ) || []
    },
  },

  methods: {
    async refresh() {
      this.account = await this.getAccount(this.$route.params.fqn)
    },

    async loadSuspensions() {
      if (this.suspensionsLoading) return

      this.suspensionsLoading = true
      try {
        this.suspensions = await this.getAccountSuspensions(this.$route.params.fqn, {
          state: ['LIMITED', 'SUSPENDED']
        })
      } catch (error) {
        console.error('Failed to load suspensions:', error)
        this.suspensions = []
      } finally {
        this.suspensionsLoading = false
      }
    },

    async openSuspensionsModal() {
      this.showSuspensionsModal = true
      await this.loadSuspensions()
    },

    getStateIcon(state) {
      const iconMap = {
        'LIMITED': 'fas fa-exclamation-triangle',
        'SUSPENDED': 'fas fa-ban',
        'DELETED': 'fas fa-trash'
      }
      return iconMap[state] || ''
    },

    formatDate(dateString) {
      if (!dateString) return 'Unknown'
      return new Date(dateString).toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      })
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
@use '@/styles/index' as *;

$banner-height: 200px;

.account.view {
  display: flex;
  flex-direction: column;
  margin: 0 auto;
  padding: 1em;
  position: relative;

  @include from($tablet) {
    max-width: $tablet;
  }

  @include until($tablet) {
    max-width: 90%;
  }

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

      .suspensions-button {
        margin-top: 0.5em;
        padding: 0.5em 1em;
        background-color: var(--color-primary);
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9em;
        display: flex;
        align-items: center;
        gap: 0.5em;

        &:hover {
          background-color: var(--color-primary-dark, #3498db);
        }
      }
    }

    .note {
      margin-top: 0.5em;
      font-size: 0.9em;
      overflow-x: hidden;

      p {
        margin: 0;
      }
    }
  }

  .fundraiser-campaign {
    margin-top: -0.75em;

    a {
      text-decoration: none;
      color: var(--color-primary);

      i {
        margin-right: 0.4em;
      }
    }
  }

  .profile-fields {
    margin-top: 1em;
    display: flex;
    flex-direction: column;
    flex-wrap: wrap;
    gap: 0.5em;
    border: 1px solid var(--color-border);
    padding: 0.5em;

    .field {
      display: flex;
      gap: 0.5em;

      .field-key {
        width: 10em;
        font-weight: bold;
        border-right: 1px solid var(--color-border);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .field-value {
        color: var(--color-text-secondary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }
}

.suspensions-container {
  .loading-message {
    text-align: center;
    padding: 2em;
    color: var(--color-text-secondary);

    i {
      margin-right: 0.5em;
    }
  }

  .no-suspensions {
    text-align: center;
    padding: 2em;
    color: var(--color-text-secondary);
  }

  .suspensions-list {
    .suspension-item {
      padding: 1em 0;
      border-bottom: 1px solid var(--color-border);

      &:last-child {
        border-bottom: none;
      }

      .suspension-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5em;

        .server-info {
          display: flex;
          align-items: center;
          gap: 1em;

          .suspension-state {
            width: 8em;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.3em;
            padding: 0.25em 0.5em;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;

            &.state-limited {
              background-color: #fff3cd;
              color: #856404;
            }

            &.state-suspended {
              background-color: #f8d7da;
              color: #721c24;
            }

            &.state-deleted {
              background-color: #f1f3f4;
              color: #5f6368;
            }
          }
        }

        .suspension-date {
          font-size: 0.75em;
          color: var(--color-text-secondary);
        }
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

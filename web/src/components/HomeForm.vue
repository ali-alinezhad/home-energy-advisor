<script setup lang="ts">
import { reactive, ref } from "vue"
import { createHome, getAdvice, getHome } from "../services/api"
import type { AdviceResponse, HomeResponse } from "../services/api"

interface AdvicePanelState {
  advice: AdviceResponse | null
  label: string
}

const emit = defineEmits<{
  (e: "advice-state-changed", value: AdvicePanelState): void
}>()

const latestCompletedBuildYear = new Date().getFullYear() - 1
const displayTimezone = import.meta.env.VITE_DISPLAY_TIMEZONE ?? "Europe/Berlin"

const form = reactive<HomeResponse>({
  id: 0,
  size: 120,
  year_built: 1985,
  heating_type: "gas",
  insulation_level: "medium",
  latest_advice: null,
  advice_generated_at: null,
})

const creating = ref(false)
const generating = ref(false)
const loadingHome = ref(false)
const error = ref("")
const successMessage = ref("")
const createdHomeId = ref<number | null>(null)
const lookupHomeId = ref<number | null>(null)
const lastSubmittedSnapshot = ref<string | null>(null)
const showRetryButton = ref(false)

function emitAdviceState(advice: AdviceResponse | null, label = "") {
  emit("advice-state-changed", { advice, label })
}

function buildSnapshot() {
  return JSON.stringify({
    size: form.size,
    year_built: form.year_built,
    heating_type: form.heating_type,
    insulation_level: form.insulation_level,
  })
}

function applyHome(home: HomeResponse) {
  form.id = home.id
  form.size = home.size
  form.year_built = home.year_built
  form.heating_type = home.heating_type
  form.insulation_level = home.insulation_level
  form.latest_advice = home.latest_advice
  form.advice_generated_at = home.advice_generated_at
  createdHomeId.value = home.id
  lastSubmittedSnapshot.value = buildSnapshot()
}

function hasUnsavedChanges() {
  return createdHomeId.value !== null && lastSubmittedSnapshot.value !== buildSnapshot()
}

function clearMessages() {
  error.value = ""
  successMessage.value = ""
}

function parseApiTimestamp(value: string): Date {
  const hasExplicitTimezone = /[zZ]|[+-]\d\d:\d\d$/.test(value)
  return new Date(hasExplicitTimezone ? value : `${value}Z`)
}

function latestAdviceLabel(home: HomeResponse) {
  if (!home.advice_generated_at) {
    return `Latest saved advice for home ID ${home.id}.`
  }

  const formatted = new Intl.DateTimeFormat("de-DE", {
    dateStyle: "short",
    timeStyle: "medium",
    hour12: false,
    timeZone: displayTimezone,
  }).format(parseApiTimestamp(home.advice_generated_at))

  return `Latest saved advice for home ID ${home.id} from ${formatted} (${displayTimezone}).`
}

async function loadHomeProfile() {
  if (!lookupHomeId.value) {
    error.value = "Enter a home ID to load a saved profile."
    return
  }

  loadingHome.value = true
  clearMessages()
  showRetryButton.value = false
  emitAdviceState(null)

  try {
    const home = await getHome(lookupHomeId.value)
    applyHome(home)
    successMessage.value = `Loaded saved home profile (ID: ${home.id}).`

    if (home.latest_advice) {
      emitAdviceState(home.latest_advice, latestAdviceLabel(home))
    } else {
      emitAdviceState(null)
    }
  } catch (err: any) {
    console.error(err)
    if (err?.response?.data?.detail) {
      error.value = err.response.data.detail
    } else if (err?.message) {
      error.value = err.message
    } else {
      error.value = "Failed to load the saved home profile."
    }
  } finally {
    loadingHome.value = false
  }
}

async function createHomeProfile() {
  creating.value = true
  clearMessages()
  showRetryButton.value = false
  emitAdviceState(null)

  try {
    const currentSnapshot = buildSnapshot()

    if (createdHomeId.value && lastSubmittedSnapshot.value === currentSnapshot) {
      successMessage.value = `Home profile already created (ID: ${createdHomeId.value}).`
      return
    }

    const home = await createHome({
      size: form.size,
      year_built: form.year_built,
      heating_type: form.heating_type,
      insulation_level: form.insulation_level,
    })

    applyHome(home)
    successMessage.value = `Home profile created successfully (ID: ${home.id}).`
  } catch (err: any) {
    console.error(err)
    if (err?.response?.data?.detail) {
      error.value = err.response.data.detail
    } else if (err?.message) {
      error.value = err.message
    } else {
      error.value = "Failed to create the home profile. Please try again."
    }
  } finally {
    creating.value = false
  }
}

async function generateAdvice() {
  clearMessages()
  showRetryButton.value = false

  if (!createdHomeId.value) {
    error.value = "Create or load a home profile before generating advice."
    emitAdviceState(null)
    return
  }

  if (hasUnsavedChanges()) {
    error.value = "Create the updated home profile before generating fresh advice."
    emitAdviceState(null)
    return
  }

  generating.value = true

  try {
    const advice = await getAdvice(createdHomeId.value)
    const label = `Fresh advice for home ID ${createdHomeId.value}.`
    successMessage.value = label
    form.latest_advice = advice
    form.advice_generated_at = new Date().toISOString()
    emitAdviceState(advice, label)
  } catch (err: any) {
    console.error(err)
    showRetryButton.value = true
    if (err?.response?.data?.detail) {
      error.value = err.response.data.detail
    } else if (err?.message) {
      error.value = err.message
    } else {
      error.value = "Failed to generate advice. Please try again."
    }
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div class="card">
    <h2>Home Details</h2>

    <div class="lookup-panel">
      <div class="form-row">
        <label for="home-id-lookup"><span>Load Saved Profile</span></label>
        <div class="lookup-row">
          <input
            id="home-id-lookup"
            v-model.number="lookupHomeId"
            type="number"
            min="1"
            placeholder="Enter home ID"
          />
          <button type="button" class="secondary-button" :disabled="loadingHome || creating || generating" @click="loadHomeProfile">
            {{ loadingHome ? "Loading..." : "Load" }}
          </button>
        </div>
      </div>
    </div>

    <form @submit.prevent="createHomeProfile" class="form">
      <label class="form-row">
        <span>Size (sqm)</span>
        <input v-model.number="form.size" type="number" min="20" max="2000" required />
      </label>

      <label class="form-row">
        <span>Year Built</span>
        <input
          v-model.number="form.year_built"
          type="number"
          min="1800"
          :max="latestCompletedBuildYear"
          required
        />
      </label>

      <label class="form-row">
        <span>Heating Type</span>
        <select v-model="form.heating_type">
          <option value="gas">Gas</option>
          <option value="oil">Oil</option>
          <option value="electric">Electric</option>
          <option value="heat_pump">Heat Pump</option>
        </select>
      </label>

      <label class="form-row">
        <span>Insulation Level</span>
        <select v-model="form.insulation_level">
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>

      <div class="button-row two-buttons">
        <button class="primary-button" type="submit" :disabled="creating || loadingHome || generating">
          {{ creating ? "Creating..." : "Create Home" }}
        </button>
        <button
          class="secondary-button"
          type="button"
          :disabled="creating || loadingHome || generating"
          @click="generateAdvice"
        >
          {{ generating ? "Generating..." : "Generate Advice" }}
        </button>
      </div>
    </form>

    <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
    <p v-if="error" class="error-message">{{ error }}</p>
    <button
      v-if="showRetryButton"
      type="button"
      class="retry-button"
      :disabled="generating || creating || loadingHome"
      @click="generateAdvice"
    >
      Retry Generate Advice
    </button>
  </div>
</template>

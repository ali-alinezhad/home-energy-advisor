<script setup lang="ts">
import { ref } from "vue"
import HomeForm from "./components/HomeForm.vue"
import AdviceView from "./components/AdviceView.vue"
import type { AdviceResponse } from "./services/api"

const advice = ref<AdviceResponse | null>(null)
const adviceLabel = ref("")

function handleAdviceStateChanged(data: {
  advice: AdviceResponse | null
  label: string
}) {
  advice.value = data.advice
  adviceLabel.value = data.label
}
</script>

<template>
  <main class="page">
    <div class="container">
      <header class="hero">
        <h1>Home Energy Advisor</h1>
        <p>
          Describe a home and receive AI-generated energy efficiency
          recommendations.
        </p>
      </header>

      <section class="grid">
        <HomeForm @advice-state-changed="handleAdviceStateChanged" />
        <AdviceView :advice="advice" :label="adviceLabel" />
      </section>
    </div>
  </main>
</template>

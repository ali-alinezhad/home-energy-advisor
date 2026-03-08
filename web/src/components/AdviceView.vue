<script setup lang="ts">
import type { AdviceResponse } from "../services/api"

defineProps<{
  advice: AdviceResponse | null
  label: string
}>()

function priorityLabel(priority: string) {
  if (priority === "high") return "High Priority"
  if (priority === "medium") return "Medium Priority"
  return "Low Priority"
}
</script>

<template>
  <div class="card">
    <h2>Energy Recommendations</h2>

    <p v-if="!advice" class="placeholder">
      Create or load a home profile, then generate fresh advice to see
      personalized recommendations here.
    </p>

    <template v-else>
      <p v-if="label" class="advice-label">{{ label }}</p>

      <ul class="advice-list">
        <li v-for="(item, i) in advice.recommendations" :key="i" class="advice-item">
          <div class="advice-header">
            <h3>{{ item.title }}</h3>
            <span class="badge" :class="item.priority">
              {{ priorityLabel(item.priority) }}
            </span>
          </div>

          <p>{{ item.description }}</p>
        </li>
      </ul>
    </template>
  </div>
</template>

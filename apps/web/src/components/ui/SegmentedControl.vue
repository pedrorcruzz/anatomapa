<script setup lang="ts" generic="T extends string">
defineProps<{
  modelValue: T
  options: { value: T; label: string }[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: T]
}>()
</script>

<template>
  <div
    class="flex w-full gap-0.5 rounded-xl bg-surface-soft p-1 ring-1 ring-border/70"
    role="radiogroup"
  >
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      role="radio"
      :aria-checked="option.value === modelValue"
      class="flex-1 rounded-lg px-2 py-1.5 text-sm font-medium whitespace-nowrap transition-all"
      :class="
        option.value === modelValue
          ? 'bg-gradient-to-b from-primary to-primary-hover text-white shadow-sm'
          : 'text-ink-muted hover:text-ink'
      "
      @click="emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

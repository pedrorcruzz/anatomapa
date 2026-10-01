<script setup lang="ts" generic="T extends string">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: T
    options: { value: T; label: string }[]
    id?: string
    disabled?: boolean
  }>(),
  {
    id: undefined,
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: T]
}>()

const open = ref(false)
const activeIndex = ref(0)
const triggerRef = ref<HTMLButtonElement | null>(null)
const listRef = ref<HTMLUListElement | null>(null)

const selectedLabel = computed(
  () => props.options.find((option) => option.value === props.modelValue)?.label ?? '',
)

function openList(): void {
  if (props.disabled) {
    return
  }
  open.value = true
  activeIndex.value = Math.max(
    0,
    props.options.findIndex((option) => option.value === props.modelValue),
  )
  nextTick(() => {
    const active = listRef.value?.children[activeIndex.value] as HTMLElement | undefined
    active?.scrollIntoView({ block: 'nearest' })
  })
}

function close(): void {
  open.value = false
}

function toggle(): void {
  if (open.value) {
    close()
  } else {
    openList()
  }
}

function select(value: T): void {
  emit('update:modelValue', value)
  close()
  triggerRef.value?.focus()
}

function onTriggerKeydown(event: KeyboardEvent): void {
  if (open.value) {
    return
  }
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp' || event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    openList()
  }
}

function onListKeydown(event: KeyboardEvent): void {
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    activeIndex.value = Math.min(props.options.length - 1, activeIndex.value + 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    activeIndex.value = Math.max(0, activeIndex.value - 1)
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    const option = props.options[activeIndex.value]
    if (option) {
      select(option.value)
    }
  } else if (event.key === 'Escape') {
    event.preventDefault()
    close()
    triggerRef.value?.focus()
  } else if (event.key === 'Tab') {
    close()
  }
}

function onClickOutside(event: MouseEvent): void {
  if (!open.value) {
    return
  }
  const target = event.target as Node
  if (triggerRef.value?.contains(target) || listRef.value?.contains(target)) {
    return
  }
  close()
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<template>
  <div class="relative">
    <button
      :id="id"
      ref="triggerRef"
      type="button"
      class="flex w-full items-center justify-between gap-2 rounded-xl bg-surface-soft px-3 py-2.5 text-left text-sm text-ink ring-1 ring-border/70 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
      :disabled="disabled"
      aria-haspopup="listbox"
      :aria-expanded="open"
      @click="toggle"
      @keydown="onTriggerKeydown"
    >
      <span class="truncate">{{ selectedLabel }}</span>
      <svg
        viewBox="0 0 24 24"
        width="14"
        height="14"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="shrink-0 text-ink-muted transition-transform"
        :class="open ? 'rotate-180' : ''"
      >
        <path d="M6 9l6 6 6-6" />
      </svg>
    </button>

    <ul
      v-if="open"
      ref="listRef"
      role="listbox"
      tabindex="-1"
      class="absolute z-20 mt-1.5 max-h-56 w-full overflow-auto rounded-xl bg-surface p-1 shadow-lg ring-1 ring-border/70"
      @keydown="onListKeydown"
    >
      <li
        v-for="(option, index) in options"
        :key="option.value"
        role="option"
        :aria-selected="option.value === modelValue"
        class="flex cursor-pointer items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm transition-colors"
        :class="[
          option.value === modelValue ? 'bg-primary/10 font-medium text-primary' : 'text-ink hover:bg-surface-soft',
          index === activeIndex && option.value !== modelValue ? 'bg-surface-soft' : '',
        ]"
        @click="select(option.value)"
        @mouseenter="activeIndex = index"
      >
        <span class="truncate">{{ option.label }}</span>
        <svg
          v-if="option.value === modelValue"
          viewBox="0 0 24 24"
          width="14"
          height="14"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="shrink-0"
        >
          <path d="M5 12l4 4L19 6" />
        </svg>
      </li>
    </ul>
  </div>
</template>

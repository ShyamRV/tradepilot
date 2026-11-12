"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PlaygroundStepId } from "@/lib/playground";

type PlaygroundState = {
  completed: PlaygroundStepId[];
  sampleOrderId: string | null;
  controlsAcknowledged: boolean;
  liveInterest: boolean;
  completeStep: (id: PlaygroundStepId) => void;
  setSampleOrderId: (id: string) => void;
  acknowledgeControls: () => void;
  expressLiveInterest: () => void;
  reset: () => void;
};

export const usePlaygroundStore = create<PlaygroundState>()(
  persist(
    (set) => ({
      completed: [],
      sampleOrderId: null,
      controlsAcknowledged: false,
      liveInterest: false,
      completeStep: (id) =>
        set((state) => ({
          completed: state.completed.includes(id) ? state.completed : [...state.completed, id]
        })),
      setSampleOrderId: (id) => set({ sampleOrderId: id }),
      acknowledgeControls: () =>
        set((state) => ({
          controlsAcknowledged: true,
          completed: state.completed.includes("controls")
            ? state.completed
            : [...state.completed, "controls"]
        })),
      expressLiveInterest: () => set({ liveInterest: true }),
      reset: () =>
        set({
          completed: [],
          sampleOrderId: null,
          controlsAcknowledged: false,
          liveInterest: false
        })
    }),
    {
      name: "tradepilot.playground"
    }
  )
);

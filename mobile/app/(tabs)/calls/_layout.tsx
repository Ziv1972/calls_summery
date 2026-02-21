/** Calls stack layout - list and detail screens. */

import { Stack } from "expo-router";

export default function CallsLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Calls" }} />
      <Stack.Screen
        name="[id]"
        options={{ title: "Call Detail" }}
      />
    </Stack>
  );
}

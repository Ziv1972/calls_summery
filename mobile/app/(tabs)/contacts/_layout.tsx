/** Contacts stack layout - list and detail. */

import { Stack } from "expo-router";

export default function ContactsLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Contacts" }} />
      <Stack.Screen name="[id]" options={{ title: "Contact" }} />
    </Stack>
  );
}

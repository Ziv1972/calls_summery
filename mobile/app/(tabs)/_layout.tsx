/** Tab layout - bottom tabs for main app sections. */

import FontAwesome from "@expo/vector-icons/FontAwesome";
import { Tabs } from "expo-router";
import React from "react";

import Colors from "@/constants/Colors";
import { useColorScheme } from "@/components/useColorScheme";

function TabIcon(props: {
  name: React.ComponentProps<typeof FontAwesome>["name"];
  color: string;
}) {
  return <FontAwesome size={24} style={{ marginBottom: -3 }} {...props} />;
}

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme ?? "light"].tint,
        tabBarStyle: {
          backgroundColor: Colors[colorScheme ?? "light"].surface,
          borderTopColor: Colors[colorScheme ?? "light"].border,
        },
        headerStyle: {
          backgroundColor: Colors[colorScheme ?? "light"].surface,
        },
        headerTintColor: Colors[colorScheme ?? "light"].text,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Dashboard",
          tabBarIcon: ({ color }) => <TabIcon name="home" color={color} />,
        }}
      />
      <Tabs.Screen
        name="calls"
        options={{
          title: "Calls",
          headerShown: false,
          tabBarIcon: ({ color }) => <TabIcon name="phone" color={color} />,
        }}
      />
      <Tabs.Screen
        name="upload"
        options={{
          title: "Upload",
          tabBarIcon: ({ color }) => (
            <TabIcon name="cloud-upload" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="contacts"
        options={{
          title: "Contacts",
          headerShown: false,
          tabBarIcon: ({ color }) => (
            <TabIcon name="address-book" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: "Settings",
          tabBarIcon: ({ color }) => <TabIcon name="cog" color={color} />,
        }}
      />
    </Tabs>
  );
}

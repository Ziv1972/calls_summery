/** Auth store - JWT tokens, user profile, login/logout with SecureStore. */

import * as SecureStore from "expo-secure-store";
import { create } from "zustand";
import type { User } from "../types/api";

const KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  USER: "user",
} as const;

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setTokens: (access, refresh) => {
    SecureStore.setItemAsync(KEYS.ACCESS_TOKEN, access);
    SecureStore.setItemAsync(KEYS.REFRESH_TOKEN, refresh);
    set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
  },

  setUser: (user) => {
    SecureStore.setItemAsync(KEYS.USER, JSON.stringify(user));
    set({ user });
  },

  logout: () => {
    SecureStore.deleteItemAsync(KEYS.ACCESS_TOKEN);
    SecureStore.deleteItemAsync(KEYS.REFRESH_TOKEN);
    SecureStore.deleteItemAsync(KEYS.USER);
    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
    });
  },

  hydrate: async () => {
    try {
      const [access, refresh, userStr] = await Promise.all([
        SecureStore.getItemAsync(KEYS.ACCESS_TOKEN),
        SecureStore.getItemAsync(KEYS.REFRESH_TOKEN),
        SecureStore.getItemAsync(KEYS.USER),
      ]);
      const user = userStr ? (JSON.parse(userStr) as User) : null;

      if (access && refresh) {
        set({
          accessToken: access,
          refreshToken: refresh,
          user,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({ isLoading: false });
      }
    } catch {
      set({ isLoading: false });
    }
  },
}));

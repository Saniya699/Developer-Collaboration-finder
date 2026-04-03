import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { api, setAuthToken } from "../api/client.js";

export const AuthContext = createContext(null);

const ACCESS_KEY = "dcf_access_token";
const REFRESH_KEY = "dcf_refresh_token";

export function AuthProvider({ children }) {
  const [accessToken, setAccessTokenState] = useState(() => localStorage.getItem(ACCESS_KEY));
  const [refreshToken, setRefreshTokenState] = useState(() => localStorage.getItem(REFRESH_KEY));
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setAuthToken(null);
    setAccessTokenState(null);
    setRefreshTokenState(null);
    setUser(null);
  }, []);

  const loadMe = useCallback(async () => {
    if (!accessToken) return;
    try {
      const res = await api.get("/api/profile/me");
      setUser(res.data);
    } catch (e) {
      // If token is invalid/expired, clear auth and let UI handle re-login.
      logout();
    }
  }, [accessToken, logout]);

  const setTokens = useCallback((access, refresh) => {
    if (access) {
      localStorage.setItem(ACCESS_KEY, access);
      setAccessTokenState(access);
      setAuthToken(access);
    }
    if (refresh) {
      localStorage.setItem(REFRESH_KEY, refresh);
      setRefreshTokenState(refresh);
    }
  }, []);

  useEffect(() => {
    setAuthToken(accessToken);
    setAuthLoading(true);
    loadMe().finally(() => setAuthLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Refresh access token on 401.
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (resp) => resp,
      async (error) => {
        const originalRequest = error?.config;
        const status = error?.response?.status;

        if (
          status === 401 &&
          refreshToken &&
          originalRequest &&
          !originalRequest.__dcf_retry
        ) {
          originalRequest.__dcf_retry = true;
          try {
            setAuthToken(refreshToken);
            const refreshResp = await api.post("/api/auth/refresh");
            const newAccess = refreshResp.data.access_token;
            setTokens(newAccess, refreshToken);
            setAuthToken(newAccess);
            originalRequest.headers.Authorization = `Bearer ${newAccess}`;
            return api(originalRequest);
          } catch (e) {
            logout();
            return Promise.reject(error);
          } finally {
            // Ensure subsequent requests use access token.
            setAuthToken(accessToken);
          }
        }

        return Promise.reject(error);
      },
    );

    return () => api.interceptors.response.eject(interceptor);
  }, [accessToken, logout, refreshToken, setTokens]);

  const login = useCallback(async (email, password) => {
    const res = await api.post("/api/auth/login", { email, password });
    setTokens(res.data.access_token, res.data.refresh_token);
    await loadMe();
    return res.data;
  }, [loadMe, setTokens]);

  const signup = useCallback(async ({ name, email, password, bio, skills, experience_level, availability, github_url }) => {
    const res = await api.post("/api/auth/register", {
      name,
      email,
      password,
      bio,
      skills: skills || [],
      experience_level: experience_level || "Beginner",
      availability: availability || "Part-time",
      github_url: github_url || null,
    });
    setTokens(res.data.access_token, res.data.refresh_token);
    await loadMe();
    return res.data;
  }, [loadMe, setTokens]);

  const value = useMemo(
    () => ({
      accessToken,
      refreshToken,
      user,
      authLoading,
      login,
      signup,
      logout,
      reloadMe: loadMe,
      setUser,
      setTokens,
    }),
    [accessToken, authLoading, login, loadMe, logout, refreshToken, setTokens, signup, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem("access_token");
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  headers.set("Content-Type", "application/json");

  let response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && token) {
    const refresh = localStorage.getItem("refresh_token");
    if (refresh) {
      try {
        const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });

        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);

          // Retry original request with new access token
          const retryHeaders = new Headers(options.headers || {});
          retryHeaders.set("Authorization", `Bearer ${data.access_token}`);
          retryHeaders.set("Content-Type", "application/json");

          response = await fetch(`${API_BASE}${url}`, {
            ...options,
            headers: retryHeaders,
          });
        } else {
          // If refresh token has expired or is invalid, redirect to login
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          if (typeof window !== "undefined") {
            window.location.href = "/login";
          }
        }
      } catch (err) {
        console.error("Token refresh error:", err);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }
  }

  return response;
}

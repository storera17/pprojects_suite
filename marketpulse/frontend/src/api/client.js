const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export async function request(path, options = {}, fallback = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      return {
        ...fallback,
        ...payload,
        status: payload.status || "error",
        error:
          payload.error ||
          `${response.status} ${response.statusText}`,
      };
    }

    return payload;
  } catch (error) {
    return {
      ...fallback,
      status: "error",
      error: error.message,
      offline: true,
    };
  }
}
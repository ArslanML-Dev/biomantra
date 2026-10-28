// The chosen demo user, kept in localStorage (prototype: no passwords).
import type { User } from "./api";

/** Read the saved user, or null on first launch. */
export function loadUser(): User | null {
  try {
    return JSON.parse(localStorage.getItem("user") ?? "null") as User | null;
  } catch {
    return null;
  }
}

/** Save (or clear) the current user. */
export function saveUser(user: User | null): void {
  if (user) localStorage.setItem("user", JSON.stringify(user));
  else localStorage.removeItem("user");
}

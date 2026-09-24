const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
  }
}

export function getToken() {
  return localStorage.getItem("lms_token");
}

export function setToken(token) {
  if (token) localStorage.setItem("lms_token", token);
  else localStorage.removeItem("lms_token");
}

export function getRole() {
  return localStorage.getItem("lms_role");
}

export function setRole(role) {
  if (role) localStorage.setItem("lms_role", role);
  else localStorage.removeItem("lms_role");
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const detail = data && data.detail !== undefined ? data.detail : res.statusText;
    throw new ApiError(res.status, detail);
  }

  return data;
}

export const api = {
  // --- auth (no token required) ---
  signup: (body) => request("/auth/signup", { method: "POST", body, auth: false }),
  login: (body) => request("/auth/login", { method: "POST", body, auth: false }),
  staffLogin: (body) =>
    request("/auth/staff-login", { method: "POST", body, auth: false }),

  // --- catalog ---
  listBooks: (limit = 20, offset = 0) =>
    request(`/books?limit=${limit}&offset=${offset}`, { auth: false }),
  getBook: (bookId) => request(`/books/${bookId}`, { auth: false }),
  createBook: (body) => request("/books", { method: "POST", body }),
  addCopy: (bookId, body) =>
    request(`/books/${bookId}/copies`, { method: "POST", body }),
  setCopyStatus: (copyId, copyStatus) =>
    request(`/books/copies/${copyId}/status`, {
      method: "PATCH",
      body: { copy_status: copyStatus },
    }),

  // --- member self-service ---
  me: () => request("/members/me"),
  updateMe: (body) => request("/members/me", { method: "PATCH", body }),
  changePassword: (body) =>
    request("/members/me/password", { method: "PATCH", body }),
  myLoans: (limit = 20, offset = 0) =>
    request(`/loans/mine?limit=${limit}&offset=${offset}`),
  myReservations: (limit = 20, offset = 0) =>
    request(`/reservations/mine?limit=${limit}&offset=${offset}`),
  myFines: (limit = 20, offset = 0) =>
    request(`/fines/mine?limit=${limit}&offset=${offset}`),
  reserveBook: (bookId) =>
    request("/reservations", { method: "POST", body: { book_id: bookId } }),
  cancelReservation: (reservationId) =>
    request(`/reservations/${reservationId}`, { method: "DELETE" }),

  // --- staff ---
  staffMe: () => request("/staff/me"),
  checkoutLoan: (memberId, copyId) =>
    request("/loans", {
      method: "POST",
      body: { member_id: memberId, copy_id: copyId },
    }),
  returnLoan: (loanId) => request(`/loans/${loanId}/return`, { method: "PATCH" }),
  generateOverdueFines: () =>
    request("/fines/generate-overdue", { method: "POST" }),
  payFine: (fineId) => request(`/fines/${fineId}/pay`, { method: "PATCH" }),
  getMemberProfile: (memberId) => request(`/members/${memberId}`),
  getMemberLoans: (memberId, limit = 20, offset = 0) =>
    request(`/members/${memberId}/loans?limit=${limit}&offset=${offset}`),
  getMemberReservations: (memberId, limit = 20, offset = 0) =>
    request(`/members/${memberId}/reservations?limit=${limit}&offset=${offset}`),
  getMemberFines: (memberId, limit = 20, offset = 0) =>
    request(`/members/${memberId}/fines?limit=${limit}&offset=${offset}`),
};

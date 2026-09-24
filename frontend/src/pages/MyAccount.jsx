import { useEffect, useState, useCallback } from "react";
import { api, ApiError } from "../api/api";

const TABS = ["Profile", "Loans", "Reservations", "Fines"];

export default function MyAccount() {
  const [tab, setTab] = useState(TABS[0]);
  const [profile, setProfile] = useState(null);
  const [loans, setLoans] = useState(null);
  const [reservations, setReservations] = useState(null);
  const [fines, setFines] = useState(null);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  const loadProfile = useCallback(async () => {
    try {
      setProfile(await api.me());
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load profile");
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    setError(null);
    (async () => {
      try {
        if (tab === "Loans") setLoans(await api.myLoans());
        if (tab === "Reservations") setReservations(await api.myReservations());
        if (tab === "Fines") setFines(await api.myFines());
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load data");
      }
    })();
  }, [tab]);

  async function saveProfile(e) {
    e.preventDefault();
    setNotice(null);
    setError(null);
    try {
      const updated = await api.updateMe({
        first_name: profile.first_name,
        last_name: profile.last_name,
        phone: profile.phone || null,
      });
      setProfile(updated);
      setNotice("Profile updated.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Update failed");
    }
  }

  async function cancelReservation(id) {
    setNotice(null);
    try {
      await api.cancelReservation(id);
      setReservations(await api.myReservations());
      setNotice("Reservation cancelled.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Cancel failed");
    }
  }

  return (
    <div className="page">
      <h1>My Account</h1>
      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? "active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>

      {error && <p className="error">{error}</p>}
      {notice && <p className="success">{notice}</p>}

      {tab === "Profile" && profile && (
        <form onSubmit={saveProfile} className="card narrow">
          <label>
            First name
            <input
              value={profile.first_name}
              onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
              required
            />
          </label>
          <label>
            Last name
            <input
              value={profile.last_name}
              onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
              required
            />
          </label>
          <label>
            Phone
            <input
              value={profile.phone || ""}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
            />
          </label>
          <p className="muted">Email: {profile.email}</p>
          <p className="muted">Status: {profile.member_status}</p>
          <button type="submit">Save</button>
        </form>
      )}

      {tab === "Loans" && loans && (
        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Checked out</th>
              <th>Due</th>
              <th>Returned</th>
              <th>Overdue</th>
            </tr>
          </thead>
          <tbody>
            {loans.items.map((l) => (
              <tr key={l.loan_id} className={l.is_overdue ? "row-warning" : ""}>
                <td>{l.title}</td>
                <td>{l.checkout_date}</td>
                <td>{l.due_date}</td>
                <td>{l.return_date || "—"}</td>
                <td>{l.is_overdue ? "Yes" : "No"}</td>
              </tr>
            ))}
            {loans.items.length === 0 && (
              <tr>
                <td colSpan={5}>No loans yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {tab === "Reservations" && reservations && (
        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Reserved</th>
              <th>Status</th>
              <th>Fulfilled</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {reservations.items.map((r) => (
              <tr key={r.reservation_id}>
                <td>{r.title}</td>
                <td>{r.reservation_date}</td>
                <td>{r.reservation_status}</td>
                <td>{r.fulfilled_date || "—"}</td>
                <td>
                  {r.reservation_status === "ACTIVE" && (
                    <button onClick={() => cancelReservation(r.reservation_id)}>
                      Cancel
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {reservations.items.length === 0 && (
              <tr>
                <td colSpan={5}>No reservations yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {tab === "Fines" && fines && (
        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Reason</th>
              <th>Amount</th>
              <th>Issued</th>
              <th>Paid</th>
            </tr>
          </thead>
          <tbody>
            {fines.items.map((f) => (
              <tr key={f.fine_id} className={!f.is_paid ? "row-warning" : ""}>
                <td>{f.title}</td>
                <td>{f.fine_reason}</td>
                <td>${f.fine_amount.toFixed(2)}</td>
                <td>{f.issued_date}</td>
                <td>{f.is_paid ? f.paid_date : "Unpaid"}</td>
              </tr>
            ))}
            {fines.items.length === 0 && (
              <tr>
                <td colSpan={5}>No fines. Keep it that way.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

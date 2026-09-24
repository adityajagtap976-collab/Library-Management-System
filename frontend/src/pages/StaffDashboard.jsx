import { useState } from "react";
import { api, ApiError } from "../api/api";

const TABS = ["Books", "Loans", "Fines", "Member Lookup"];

function useNotices() {
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const clear = () => {
    setError(null);
    setNotice(null);
  };
  return { error, setError, notice, setNotice, clear };
}

export default function StaffDashboard() {
  const [tab, setTab] = useState(TABS[0]);

  return (
    <div className="page">
      <h1>Staff Dashboard</h1>
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
      {tab === "Books" && <BooksPanel />}
      {tab === "Loans" && <LoansPanel />}
      {tab === "Fines" && <FinesPanel />}
      {tab === "Member Lookup" && <MemberLookupPanel />}
    </div>
  );
}

function BooksPanel() {
  const { error, setError, notice, setNotice, clear } = useNotices();
  const [book, setBook] = useState({
    title: "",
    isbn: "",
    publisher_id: "",
    genre: "",
    publication_date: "",
  });
  const [copy, setCopy] = useState({ book_id: "", shelf_location: "" });
  const [statusUpdate, setStatusUpdate] = useState({ copy_id: "", copy_status: "AVAILABLE" });

  async function createBook(e) {
    e.preventDefault();
    clear();
    try {
      const result = await api.createBook({
        title: book.title,
        isbn: book.isbn,
        publisher_id: Number(book.publisher_id),
        genre: book.genre || null,
        publication_date: book.publication_date || null,
      });
      setNotice(`Book created (id ${result.book_id}).`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to create book");
    }
  }

  async function addCopy(e) {
    e.preventDefault();
    clear();
    try {
      const result = await api.addCopy(Number(copy.book_id), {
        shelf_location: copy.shelf_location || null,
      });
      setNotice(`Copy added (id ${result.copy_id}).`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to add copy");
    }
  }

  async function updateStatus(e) {
    e.preventDefault();
    clear();
    try {
      await api.setCopyStatus(Number(statusUpdate.copy_id), statusUpdate.copy_status);
      setNotice("Copy status updated.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to update status");
    }
  }

  return (
    <div className="stack">
      {error && <p className="error">{error}</p>}
      {notice && <p className="success">{notice}</p>}

      <form onSubmit={createBook} className="card narrow">
        <h3>Add Book</h3>
        <label>
          Title
          <input
            value={book.title}
            onChange={(e) => setBook({ ...book, title: e.target.value })}
            required
          />
        </label>
        <label>
          ISBN
          <input
            value={book.isbn}
            onChange={(e) => setBook({ ...book, isbn: e.target.value })}
            minLength={10}
            required
          />
        </label>
        <label>
          Publisher ID
          <input
            type="number"
            value={book.publisher_id}
            onChange={(e) => setBook({ ...book, publisher_id: e.target.value })}
            required
          />
        </label>
        <label>
          Genre
          <input value={book.genre} onChange={(e) => setBook({ ...book, genre: e.target.value })} />
        </label>
        <label>
          Publication date
          <input
            type="date"
            value={book.publication_date}
            onChange={(e) => setBook({ ...book, publication_date: e.target.value })}
          />
        </label>
        <button type="submit">Create Book</button>
      </form>

      <form onSubmit={addCopy} className="card narrow">
        <h3>Add Copy</h3>
        <label>
          Book ID
          <input
            type="number"
            value={copy.book_id}
            onChange={(e) => setCopy({ ...copy, book_id: e.target.value })}
            required
          />
        </label>
        <label>
          Shelf location
          <input
            value={copy.shelf_location}
            onChange={(e) => setCopy({ ...copy, shelf_location: e.target.value })}
          />
        </label>
        <button type="submit">Add Copy</button>
      </form>

      <form onSubmit={updateStatus} className="card narrow">
        <h3>Update Copy Status</h3>
        <label>
          Copy ID
          <input
            type="number"
            value={statusUpdate.copy_id}
            onChange={(e) => setStatusUpdate({ ...statusUpdate, copy_id: e.target.value })}
            required
          />
        </label>
        <label>
          Status
          <select
            value={statusUpdate.copy_status}
            onChange={(e) =>
              setStatusUpdate({ ...statusUpdate, copy_status: e.target.value })
            }
          >
            {["AVAILABLE", "ON_LOAN", "LOST", "DAMAGED", "WITHDRAWN"].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Update Status</button>
      </form>
    </div>
  );
}

function LoansPanel() {
  const { error, setError, notice, setNotice, clear } = useNotices();
  const [checkout, setCheckout] = useState({ member_id: "", copy_id: "" });
  const [returnLoanId, setReturnLoanId] = useState("");

  async function doCheckout(e) {
    e.preventDefault();
    clear();
    try {
      const result = await api.checkoutLoan(
        Number(checkout.member_id),
        Number(checkout.copy_id)
      );
      setNotice(`Loan created (id ${result.loan_id}), due ${result.due_date}.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Checkout failed");
    }
  }

  async function doReturn(e) {
    e.preventDefault();
    clear();
    try {
      const result = await api.returnLoan(Number(returnLoanId));
      setNotice(`Loan ${result.loan_id} returned on ${result.return_date}.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Return failed");
    }
  }

  return (
    <div className="stack">
      {error && <p className="error">{error}</p>}
      {notice && <p className="success">{notice}</p>}

      <form onSubmit={doCheckout} className="card narrow">
        <h3>Checkout (create loan)</h3>
        <label>
          Member ID
          <input
            type="number"
            value={checkout.member_id}
            onChange={(e) => setCheckout({ ...checkout, member_id: e.target.value })}
            required
          />
        </label>
        <label>
          Copy ID
          <input
            type="number"
            value={checkout.copy_id}
            onChange={(e) => setCheckout({ ...checkout, copy_id: e.target.value })}
            required
          />
        </label>
        <button type="submit">Check Out</button>
      </form>

      <form onSubmit={doReturn} className="card narrow">
        <h3>Return Loan</h3>
        <label>
          Loan ID
          <input
            type="number"
            value={returnLoanId}
            onChange={(e) => setReturnLoanId(e.target.value)}
            required
          />
        </label>
        <button type="submit">Return</button>
      </form>
    </div>
  );
}

function FinesPanel() {
  const { error, setError, notice, setNotice, clear } = useNotices();
  const [fineId, setFineId] = useState("");

  async function generate() {
    clear();
    try {
      const result = await api.generateOverdueFines();
      setNotice(`Generated ${result.fines_created} fine(s).`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to generate fines");
    }
  }

  async function pay(e) {
    e.preventDefault();
    clear();
    try {
      const result = await api.payFine(Number(fineId));
      setNotice(`Fine ${result.fine_id} marked paid on ${result.paid_date}.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to mark paid");
    }
  }

  return (
    <div className="stack">
      {error && <p className="error">{error}</p>}
      {notice && <p className="success">{notice}</p>}

      <div className="card narrow">
        <h3>Generate Overdue Fines</h3>
        <p className="muted">
          Scans all overdue, unpaid loans and creates fine records for them.
        </p>
        <button onClick={generate}>Run</button>
      </div>

      <form onSubmit={pay} className="card narrow">
        <h3>Mark Fine Paid</h3>
        <label>
          Fine ID
          <input
            type="number"
            value={fineId}
            onChange={(e) => setFineId(e.target.value)}
            required
          />
        </label>
        <button type="submit">Mark Paid</button>
      </form>
    </div>
  );
}

function MemberLookupPanel() {
  const { error, setError, clear } = useNotices();
  const [memberId, setMemberId] = useState("");
  const [profile, setProfile] = useState(null);
  const [loans, setLoans] = useState(null);
  const [reservations, setReservations] = useState(null);
  const [fines, setFines] = useState(null);

  async function lookup(e) {
    e.preventDefault();
    clear();
    setProfile(null);
    try {
      const id = Number(memberId);
      const [p, l, r, f] = await Promise.all([
        api.getMemberProfile(id),
        api.getMemberLoans(id),
        api.getMemberReservations(id),
        api.getMemberFines(id),
      ]);
      setProfile(p);
      setLoans(l);
      setReservations(r);
      setFines(f);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Member not found");
    }
  }

  return (
    <div className="stack">
      <form onSubmit={lookup} className="card narrow">
        <h3>Look Up Member</h3>
        <label>
          Member ID
          <input
            type="number"
            value={memberId}
            onChange={(e) => setMemberId(e.target.value)}
            required
          />
        </label>
        <button type="submit">Look Up</button>
      </form>

      {error && <p className="error">{error}</p>}

      {profile && (
        <div className="card">
          <h3>
            {profile.first_name} {profile.last_name} — {profile.member_status}
          </h3>
          <p className="muted">{profile.email}</p>
          <p>
            {loans.items.length} loan(s), {reservations.items.length} reservation(s),{" "}
            {fines.items.filter((f) => !f.is_paid).length} unpaid fine(s)
          </p>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState, useCallback } from "react";
import { api, ApiError } from "../api/api";
import { useAuth } from "../context/AuthContext";

const PAGE_SIZE = 12;

export default function Catalog() {
  const [books, setBooks] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const { role } = useAuth();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listBooks(PAGE_SIZE, offset);
      setBooks(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load catalog");
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    load();
  }, [load]);

  async function reserve(bookId) {
    setNotice(null);
    try {
      await api.reserveBook(bookId);
      setNotice("Reservation placed.");
    } catch (err) {
      setNotice(
        err instanceof ApiError ? `Could not reserve: ${err.detail}` : "Could not reserve"
      );
    }
  }

  return (
    <div className="page">
      <h1>Catalog</h1>
      {notice && <p className="success">{notice}</p>}
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="grid">
          {books.map((book) => (
            <div key={book.book_id} className="card">
              <h3>{book.title}</h3>
              <p className="muted">{book.authors.join(", ") || "Unknown author"}</p>
              <p className="muted">{book.publisher_name}</p>
              <p className="muted">ISBN {book.isbn}</p>
              {book.genre && <p className="tag">{book.genre}</p>}
              {role === "member" && (
                <button onClick={() => reserve(book.book_id)}>Reserve</button>
              )}
            </div>
          ))}
          {books.length === 0 && <p>No books found.</p>}
        </div>
      )}

      <div className="pager">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
          Previous
        </button>
        <span>
          {offset + 1}-{Math.min(offset + PAGE_SIZE, total)} of {total}
        </span>
        <button
          disabled={offset + PAGE_SIZE >= total}
          onClick={() => setOffset(offset + PAGE_SIZE)}
        >
          Next
        </button>
      </div>
    </div>
  );
}

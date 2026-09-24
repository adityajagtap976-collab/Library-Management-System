import { createContext, useContext, useState, useCallback } from "react";
import { setToken, setRole, getRole, getToken } from "../api/api";

const AuthContext = createContext(null);

function decodeJwt(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [role, setRoleState] = useState(getRole());
  const [principal, setPrincipal] = useState(() => {
    const token = getToken();
    return token ? decodeJwt(token) : null;
  });

  const login = useCallback((token, roleValue) => {
    setToken(token);
    setRole(roleValue);
    setRoleState(roleValue);
    setPrincipal(decodeJwt(token));
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setRole(null);
    setRoleState(null);
    setPrincipal(null);
  }, []);

  return (
    <AuthContext.Provider value={{ role, principal, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

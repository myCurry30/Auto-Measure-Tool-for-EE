import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";
import {
  login as apiLogin,
  logout as apiLogout,
  getToken,
  setToken,
  getStoredUser,
  setStoredUser,
  type LoginResponse,
} from "../services/auth";

interface AuthState {
  username: string | null;
  role: string | null;
  displayName: string | null;
  isAuthenticated: boolean;
  login: (username: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState>({
  username: null,
  role: null,
  displayName: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = getToken();
    const user = getStoredUser();
    if (token && user) {
      setUsername(user.username);
      setRole(user.role);
      setDisplayName(user.display_name);
    }
  }, []);

  const login = async (username: string) => {
    const result: LoginResponse = await apiLogin(username);
    setToken(result.token);
    setStoredUser({
      username,
      role: result.role,
      display_name: result.display_name,
    });
    setUsername(username);
    setRole(result.role);
    setDisplayName(result.display_name);
    navigate("/connect");
  };

  const logout = () => {
    apiLogout();
    setUsername(null);
    setRole(null);
    setDisplayName(null);
    navigate("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        username,
        role,
        displayName,
        isAuthenticated: !!username,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

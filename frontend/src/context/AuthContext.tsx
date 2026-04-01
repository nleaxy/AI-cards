import React, { createContext, useContext, useState, useEffect } from 'react';

export interface User {
    id: number;
    username: string;
    email: string;
    role: 'user' | 'admin';
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string, user: User) => void;  // refresh token больше не передаем - он в cookie
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);

    useEffect(() => {
        // при загрузке страницы восстанавливаем access token и данные пользователя из localStorage
        // refresh token не нужно восстанавливать - он в httponly cookie, браузер сам его хранит
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }
    }, []);

    const login = (newToken: string, newUser: User) => {
        // сохраняем только access token и данные пользователя - refresh token в httponly cookie
        // удаляем старый refreshToken из localStorage если он там остался с прошлой версии
        setToken(newToken);
        setUser(newUser);
        localStorage.setItem('token', newToken);
        localStorage.setItem('user', JSON.stringify(newUser));
        localStorage.removeItem('refreshToken');  // чистим старое значение
    };

    const logout = () => {
        // очищаем access token и user из localStorage
        // refresh token удаляется сервером при вызове /logout (он устанавливает пустой cookie)
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('refreshToken');  // чистим старое значение если осталось
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!user }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

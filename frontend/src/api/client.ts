import { User } from '../context/AuthContext';

const API_URL = 'http://localhost:5000/api';

interface AuthResponse {
    access_token: string;
    user?: User;
}

// centralized fetch wrapper - подставляет access token в заголовок и обновляет его если истёк
// refresh token теперь хранится в httponly cookie - браузер сам его отправляет, мы его не трогаем
export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
    let token = localStorage.getItem('token');

    const defaultHeaders: Record<string, string> = {};

    // ставим content-type только если тело запроса не FormData (файл)
    if (!(options.body instanceof FormData)) {
        defaultHeaders['Content-Type'] = 'application/json';
    }

    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const headers = {
        ...defaultHeaders,
        ...options.headers,
    } as HeadersInit;

    // credentials: 'include' нужно чтобы браузер отправлял httponly cookie (refresh token)
    let response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
        credentials: 'include'
    });

    // если пришел 401 или 422 - access token истёк или невалиден, пробуем обновить через refresh token из cookie
    // 422 может прийти от Flask-JWT-Extended если изменился секретный ключ или структура токена
    if ((response.status === 401 || response.status === 422) && localStorage.getItem('token')) {
        try {
            // браузер автоматически отправит refresh_token cookie - нам не нужно его передавать вручную
            const refreshResponse = await fetch(`${API_URL}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'  // отправляем cookie с refresh token
            });

            if (refreshResponse.ok) {
                const data: AuthResponse = await refreshResponse.json();
                localStorage.setItem('token', data.access_token);

                // повторяем оригинальный запрос с новым access token
                const newHeaders = {
                    ...headers,
                    'Authorization': `Bearer ${data.access_token}`
                };

                response = await fetch(`${API_URL}${endpoint}`, {
                    ...options,
                    headers: newHeaders,
                    credentials: 'include'
                });
            } else {
                // refresh тоже не сработал - разлогиниваем пользователя
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/';
            }
        } catch (error) {
            // сетевая ошибка при обновлении токена
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
        }
    }

    return response;
};

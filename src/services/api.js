/**
 * Единый экземпляр API-клиента приложения.
 *
 * `AuthApi` наследует `ApiService`, поэтому инстанс умеет всё, что нужно
 * страницам: JSON-запросы (`get`/`post`/`put`/`patch`/`delete`), заголовок
 * `Authorization: Bearer …`, автоматическое обновление access-токена по
 * 401-ответу и методы авторизации (`login`/`register`/`logout`/`me`).
 */
import { AuthApi } from "./AuthApi";

/* Базовый адрес можно переопределить через VITE_API_URL (по умолчанию — текущий origin). */
const baseUrl = (import.meta.env && import.meta.env.VITE_API_URL) || "";

export const api = new AuthApi(baseUrl);

export { AuthApi };
export default api;

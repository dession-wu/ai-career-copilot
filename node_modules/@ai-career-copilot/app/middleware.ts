import createMiddleware from 'next-intl/middleware';
import { routing } from './src/i18n/routing';

export default createMiddleware(routing);

export const config = {
  // Matcher entries need to be relative paths and have the same structure.
  // 使用更宽泛的 matcher 确保 /login 和 /register 被捕获
  matcher: [
    '/',
    '/(zh|en)/:path*',
    '/login',
    '/register',
    '/((?!api|_next|.*\\..*).*)',
  ],
};

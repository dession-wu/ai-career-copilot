import { NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { Toaster } from 'sonner';
import { routing } from '@/i18n/routing';

// 静态导出模式：为每个 locale 预生成页面
export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  // 启用 next-intl 静态渲染：设置 requestLocale 缓存，避免回退 headers()
  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <NextIntlClientProvider messages={messages}>
      {children}
      <Toaster position="top-center" richColors />
    </NextIntlClientProvider>
  );
}

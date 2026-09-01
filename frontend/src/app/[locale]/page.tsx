'use client';

/**
 * Landing Page（落地页）
 *
 * 纯静态展示页，无业务逻辑：
 * - 结构：Header → Hero（渐变标题 + 双 CTA）→ 核心功能（4 卡片）→ 底部 CTA → Footer
 * - 风格：极简白底 + 轻量科技感（缓慢平移的细网格背景、CSS 渐隐浮现），纯 CSS 实现，零动画库依赖
 * - 配色：主色 #2563EB（蓝）/ 文字 #0F172A / 底色 #F8FAFC，均通过 Tailwind 任意值类内联指定
 * - 响应式：桌面多列 / 移动端单列
 * - i18n：文案全部走 next-intl messages（landing 命名空间），随 [locale] 预渲染
 */
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { FileText, Target, Compass, Mic, ArrowRight, Sparkles } from 'lucide-react';

/** 轻量动效样式：网格平移 + 渐隐浮现，均为纯 CSS 关键帧 */
const ANIMATION_CSS = `
  /* 缓慢平移的细网格背景（60s 循环，无感知级轻量动效） */
  @keyframes landing-grid-pan {
    from { background-position: 0 0; }
    to   { background-position: 64px 64px; }
  }
  .landing-grid {
    background-image:
      linear-gradient(to right, rgba(37, 99, 235, 0.07) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(37, 99, 235, 0.07) 1px, transparent 1px);
    background-size: 64px 64px;
    animation: landing-grid-pan 60s linear infinite;
  }
  /* 渐隐浮现：向下淡入，配合 animation-delay 实现错落出现 */
  @keyframes landing-fade-up {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .landing-fade-up {
    opacity: 0;
    animation: landing-fade-up 0.7s ease-out forwards;
  }
  /* 动效可关闭：尊重系统级"减少动态效果"偏好 */
  @media (prefers-reduced-motion: reduce) {
    .landing-grid { animation: none; }
    .landing-fade-up { animation: none; opacity: 1; }
  }
`;

export default function LandingPage() {
  const t = useTranslations('landing');

  // 四大核心功能卡片（图标 + 文案均来自 messages，便于双语维护）
  const features = [
    { icon: FileText, title: t('features.resume.title'), desc: t('features.resume.desc') },
    { icon: Target, title: t('features.diagnosis.title'), desc: t('features.diagnosis.desc') },
    { icon: Compass, title: t('features.planning.title'), desc: t('features.planning.desc') },
    { icon: Mic, title: t('features.interview.title'), desc: t('features.interview.desc') },
  ];

  return (
    <div className="min-h-screen bg-white text-[#0F172A]">
      {/* 集中注入本页专用动效样式，不污染全局 */}
      <style>{ANIMATION_CSS}</style>

      {/* ============ Header ============ */}
      <header className="sticky top-0 z-50 border-b border-slate-100 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#2563EB] text-white">
              <Sparkles className="h-4 w-4" />
            </span>
            <span className="text-lg font-semibold tracking-tight">AI Career Co-pilot</span>
          </Link>

          {/* 桌面导航：移动端隐藏（落地页保持极简，不做汉堡菜单） */}
          <nav className="hidden items-center gap-8 text-sm text-slate-600 sm:flex">
            <a href="#features" className="transition-colors hover:text-[#2563EB]">
              {t('nav.features')}
            </a>
            <Link href="/login" className="transition-colors hover:text-[#2563EB]">
              {t('nav.login')}
            </Link>
          </nav>

          <Link
            href="/register"
            className="rounded-full bg-[#2563EB] px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700"
          >
            {t('nav.start')}
          </Link>
        </div>
      </header>

      <main>
        {/* ============ Hero ============ */}
        <section className="relative overflow-hidden bg-[#F8FAFC]">
          {/* 缓慢平移的细网格背景（径向蒙版使其边缘自然消隐） */}
          <div
            className="landing-grid pointer-events-none absolute inset-0"
            style={{
              maskImage: 'radial-gradient(ellipse 70% 60% at 50% 40%, black 40%, transparent 100%)',
              WebkitMaskImage:
                'radial-gradient(ellipse 70% 60% at 50% 40%, black 40%, transparent 100%)',
            }}
          />

          <div className="relative mx-auto flex max-w-4xl flex-col items-center px-4 py-24 text-center sm:px-6 sm:py-32">
            {/* 顶部徽标条 */}
            <div className="landing-fade-up mb-6 rounded-full border border-blue-100 bg-blue-50 px-4 py-1.5 text-xs font-medium text-[#2563EB] sm:text-sm">
              {t('hero.badge')}
            </div>

            {/* 渐变标题 */}
            <h1 className="landing-fade-up text-4xl font-bold leading-tight tracking-tight sm:text-5xl md:text-6xl">
              {t('hero.title1')}
              <br />
              <span className="bg-gradient-to-r from-[#2563EB] to-sky-400 bg-clip-text text-transparent">
                {t('hero.title2')}
              </span>
            </h1>

            {/* 副标题 */}
            <p className="landing-fade-up mt-6 max-w-2xl text-base leading-relaxed text-slate-600 sm:text-lg">
              {t('hero.subtitle')}
            </p>

            {/* 双 CTA：免费开始（主）/ 了解更多（次） */}
            <div className="landing-fade-up mt-10 flex w-full flex-col items-center justify-center gap-3 sm:w-auto sm:flex-row">
              <Link
                href="/register"
                className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#2563EB] px-8 py-3 text-base font-semibold text-white shadow-lg shadow-blue-600/20 transition-all hover:bg-blue-700 hover:shadow-xl sm:w-auto"
              >
                {t('hero.ctaPrimary')}
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#features"
                className="inline-flex w-full items-center justify-center rounded-full border border-slate-200 bg-white px-8 py-3 text-base font-semibold text-slate-700 transition-colors hover:border-blue-300 hover:text-[#2563EB] sm:w-auto"
              >
                {t('hero.ctaSecondary')}
              </a>
            </div>
          </div>
        </section>

        {/* ============ 核心功能区：4 张卡片 ============ */}
        <section id="features" className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-24">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="landing-fade-up text-3xl font-bold tracking-tight sm:text-4xl">
              {t('features.title')}
            </h2>
            <p className="landing-fade-up mt-3 text-slate-600">{t('features.subtitle')}</p>
          </div>

          {/* 移动端单列，sm 起双列，lg 起四列 */}
          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <div
                key={f.title}
                className="landing-fade-up group rounded-2xl border border-slate-100 bg-white p-6 transition-all hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg hover:shadow-blue-600/5"
              >
                {/* 图标底座：hover 时主色加深，提供轻量反馈 */}
                <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-[#2563EB] transition-colors group-hover:bg-[#2563EB] group-hover:text-white">
                  <f.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ============ 底部 CTA ============ */}
        <section className="bg-[#F8FAFC]">
          <div className="landing-fade-up mx-auto max-w-4xl px-4 py-20 text-center sm:px-6 sm:py-24">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{t('cta.title')}</h2>
            <p className="mt-3 text-slate-600">{t('cta.subtitle')}</p>
            <Link
              href="/register"
              className="mt-8 inline-flex items-center justify-center gap-2 rounded-full bg-[#2563EB] px-8 py-3 text-base font-semibold text-white shadow-lg shadow-blue-600/20 transition-all hover:bg-blue-700"
            >
              {t('cta.button')}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>

      {/* ============ Footer ============ */}
      <footer className="border-t border-slate-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#2563EB] text-white">
              <Sparkles className="h-3 w-3" />
            </span>
            <span>{t('footer.tagline')}</span>
          </div>
          <span>
            © {new Date().getFullYear()} AI Career Co-pilot · {t('footer.rights')}
          </span>
        </div>
      </footer>
    </div>
  );
}